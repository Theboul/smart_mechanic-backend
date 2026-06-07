"""apply_structural_corrections

Revision ID: 080a90c7b748
Revises: a754325fd0a6
Create Date: 2026-05-31 18:16:59.820378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography


# revision identifiers, used by Alembic.
revision: str = '080a90c7b748'
down_revision: Union[str, Sequence[str], None] = 'a754325fd0a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Crear sucursal_taller
    op.create_table(
        'sucursal_taller',
        sa.Column('id_sucursal', sa.UUID(), nullable=False),
        sa.Column('id_taller', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(length=150), nullable=False),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('email', sa.String(length=150), nullable=True),
        sa.Column('direccion', sa.String(length=255), nullable=True),
        sa.Column('ubicacion', Geography(geometry_type='POINT', srid=4326), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id_sucursal'),
        sa.ForeignKeyConstraint(['id_taller'], ['taller.id_taller'], name='fk_sucursal_taller'),
        sa.UniqueConstraint('id_taller', 'nombre', name='uq_sucursal_taller_nombre'),
        sa.UniqueConstraint('id_sucursal', 'id_taller', name='uq_sucursal_taller_compuesta')
    )

    # 2. Crear usuario_taller
    op.create_table(
        'usuario_taller',
        sa.Column('id_usuario_taller', sa.UUID(), nullable=False),
        sa.Column('id_usuario', sa.UUID(), nullable=False),
        sa.Column('id_taller', sa.UUID(), nullable=False),
        sa.Column('id_sucursal', sa.UUID(), nullable=True),
        sa.Column('rol_contexto', sa.String(length=50), nullable=False),
        sa.Column('estado', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('fecha_asignacion', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id_usuario_taller'),
        sa.ForeignKeyConstraint(['id_usuario'], ['usuarios.id_usuario'], name='fk_usuario_taller_usuario'),
        sa.ForeignKeyConstraint(['id_taller'], ['taller.id_taller'], name='fk_usuario_taller_taller'),
        sa.ForeignKeyConstraint(['id_sucursal', 'id_taller'], ['sucursal_taller.id_sucursal', 'sucursal_taller.id_taller'], name='fk_usuario_taller_sucursal'),
        sa.UniqueConstraint('id_usuario', 'id_taller', 'rol_contexto', name='uq_usuario_taller_rol')
    )

    # 3. Modificar tecnico
    op.add_column('tecnico', sa.Column('id_sucursal', sa.UUID(), nullable=True))
    op.add_column('tecnico', sa.Column('estado_operativo', sa.String(length=50), nullable=False, server_default='DISPONIBLE'))
    op.create_foreign_key(
        'fk_tecnico_sucursal',
        'tecnico', 'sucursal_taller',
        ['id_sucursal', 'id_taller'],
        ['id_sucursal', 'id_taller']
    )

    # 4. Modificar incidente
    # 4.1. Agregar id_sucursal y FK compuesta
    op.add_column('incidente', sa.Column('id_sucursal', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_incidente_sucursal',
        'incidente', 'sucursal_taller',
        ['id_sucursal', 'id_taller'],
        ['id_sucursal', 'id_taller']
    )

    # 4.2. Agregar id_usuario_cliente
    op.add_column('incidente', sa.Column('id_usuario_cliente', sa.UUID(), nullable=True))
    # Poblar id_usuario_cliente de incidentes existentes usando el id_usuario del vehiculo asignado
    op.execute("""
        UPDATE incidente
        SET id_usuario_cliente = (
            SELECT id_usuario 
            FROM vehiculo 
            WHERE vehiculo.id_vehiculo = incidente.id_vehiculo
        )
        WHERE id_usuario_cliente IS NULL
    """)
    # Asegurar que sea NOT NULL ahora que están poblados
    op.alter_column('incidente', 'id_usuario_cliente', nullable=False)

    # 4.3. Corregir FK de id_tecnico de usuarios(id_usuario) a tecnico(id_tecnico)
    # Eliminar dinámicamente cualquier clave foránea existente sobre incidente.id_tecnico
    op.execute("""
    DO $$
    DECLARE
        fk_name text;
    BEGIN
        SELECT tc.constraint_name
        INTO fk_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = 'incidente'
          AND kcu.column_name = 'id_tecnico';

        IF fk_name IS NOT NULL THEN
            EXECUTE 'ALTER TABLE incidente DROP CONSTRAINT ' || quote_ident(fk_name);
        END IF;
    END $$;
    """)

    # Traducir id_tecnico de incidentes existentes (que almacenaban id_usuario del técnico) al id_tecnico correspondiente de la tabla tecnico
    op.execute("""
        UPDATE incidente
        SET id_tecnico = t.id_tecnico
        FROM tecnico t
        WHERE incidente.id_tecnico = t.id_usuario;
    """)

    # Limpiar cualquier id_tecnico que no exista en la tabla tecnico (huérfanos) para evitar fallos de FK
    op.execute("""
        UPDATE incidente
        SET id_tecnico = NULL
        WHERE id_tecnico NOT IN (SELECT id_tecnico FROM tecnico) AND id_tecnico IS NOT NULL;
    """)

    # Crear la nueva FK que apunta a tecnico(id_tecnico)
    op.create_foreign_key(
        'fk_incidente_tecnico',
        'incidente', 'tecnico',
        ['id_tecnico'], ['id_tecnico']
    )

    # 5. Modificar historial_incidente
    op.add_column('historial_incidente', sa.Column('id_taller', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_historial_incidente_taller',
        'historial_incidente', 'taller',
        ['id_taller'], ['id_taller']
    )
    op.add_column('historial_incidente', sa.Column('id_sucursal', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_historial_incidente_sucursal',
        'historial_incidente', 'sucursal_taller',
        ['id_sucursal', 'id_taller'],
        ['id_sucursal', 'id_taller']
    )
    op.add_column('historial_incidente', sa.Column('id_usuario_actor', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_historial_incidente_usuario_actor',
        'historial_incidente', 'usuarios',
        ['id_usuario_actor'], ['id_usuario']
    )


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Eliminar FKs y columnas de historial_incidente
    op.drop_constraint('fk_historial_incidente_usuario_actor', 'historial_incidente', type_='foreignkey')
    op.drop_column('historial_incidente', 'id_usuario_actor')
    op.drop_constraint('fk_historial_incidente_sucursal', 'historial_incidente', type_='foreignkey')
    op.drop_column('historial_incidente', 'id_sucursal')
    op.drop_constraint('fk_historial_incidente_taller', 'historial_incidente', type_='foreignkey')
    op.drop_column('historial_incidente', 'id_taller')

    # 2. Restaurar incidente
    # 2.1. Eliminar FK id_tecnico a tecnico y restaurar FK a usuarios
    op.drop_constraint('fk_incidente_tecnico', 'incidente', type_='foreignkey')
    op.create_foreign_key(
        'fk_incidente_tecnico_usuarios',
        'incidente', 'usuarios',
        ['id_tecnico'], ['id_usuario']
    )
    # 2.2. Eliminar columna id_usuario_cliente
    op.drop_column('incidente', 'id_usuario_cliente')
    # 2.3. Eliminar FK id_sucursal y su columna
    op.drop_constraint('fk_incidente_sucursal', 'incidente', type_='foreignkey')
    op.drop_column('incidente', 'id_sucursal')

    # 3. Restaurar tecnico
    op.drop_constraint('fk_tecnico_sucursal', 'tecnico', type_='foreignkey')
    op.drop_column('tecnico', 'estado_operativo')
    op.drop_column('tecnico', 'id_sucursal')

    # 4. Eliminar tablas usuario_taller y sucursal_taller
    op.drop_table('usuario_taller')
    op.drop_table('sucursal_taller')
