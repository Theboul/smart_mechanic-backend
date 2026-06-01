"""create_tracking_tecnico

Revision ID: 029711f1beca
Revises: 080a90c7b748
Create Date: 2026-05-31 20:38:49.437188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '029711f1beca'
down_revision: Union[str, Sequence[str], None] = '080a90c7b748'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Crear tabla tracking_tecnico
    op.create_table('tracking_tecnico',
    sa.Column('id_tracking', sa.UUID(), nullable=False),
    sa.Column('id_asignacion', sa.UUID(), nullable=False),
    sa.Column('id_taller', sa.UUID(), nullable=False),
    sa.Column('id_sucursal', sa.UUID(), nullable=True),
    sa.Column('latitud', sa.Numeric(precision=10, scale=7), nullable=False),
    sa.Column('longitud', sa.Numeric(precision=10, scale=7), nullable=False),
    sa.Column('velocidad', sa.Numeric(precision=6, scale=2), nullable=True),
    sa.Column('estado_tracking', sa.String(length=50), nullable=True),
    sa.Column('fecha_registro', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['id_asignacion'], ['asignacion_incidente.id_asignacion'], name='fk_tracking_asignacion'),
    sa.ForeignKeyConstraint(['id_sucursal', 'id_taller'], ['sucursal_taller.id_sucursal', 'sucursal_taller.id_taller'], name='fk_tracking_sucursal'),
    sa.ForeignKeyConstraint(['id_taller'], ['taller.id_taller'], name='fk_tracking_taller'),
    sa.PrimaryKeyConstraint('id_tracking')
    )

    # 2. Agregar clave foránea para id_usuario_cliente en incidente si no existe
    # Usamos execute con un DO block de PostgreSQL por seguridad
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
          AND kcu.column_name = 'id_usuario_cliente';

        IF fk_name IS NULL THEN
            ALTER TABLE incidente ADD CONSTRAINT fk_incidente_cliente FOREIGN KEY (id_usuario_cliente) REFERENCES usuarios(id_usuario);
        END IF;
    END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('fk_incidente_cliente', 'incidente', type_='foreignkey')
    op.drop_table('tracking_tecnico')
