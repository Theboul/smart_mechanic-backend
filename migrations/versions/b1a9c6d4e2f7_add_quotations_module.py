"""add quotations module

Revision ID: b1a9c6d4e2f7
Revises: 239492d1183e
Create Date: 2026-06-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geography
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = "b1a9c6d4e2f7"
down_revision: Union[str, Sequence[str], None] = "239492d1183e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "solicitud_cotizacion",
        sa.Column("id_solicitud_cotizacion", UUID(as_uuid=True), primary_key=True),
        sa.Column("id_cliente", UUID(as_uuid=True), sa.ForeignKey("usuarios.id_usuario"), nullable=False),
        sa.Column("id_vehiculo", UUID(as_uuid=True), sa.ForeignKey("vehiculo.id_vehiculo"), nullable=False),
        sa.Column("ubicacion_cliente", Geography(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("prioridad", sa.String(length=20), nullable=False, server_default=sa.text("'MEDIA'")),
        sa.Column("categoria_servicio", sa.String(length=150), nullable=True),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default=sa.text("'ABIERTA'")),
        sa.Column("fecha_vencimiento", sa.DateTime(), nullable=False),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_modificacion", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "solicitud_cotizacion_taller",
        sa.Column("id_solicitud_taller", UUID(as_uuid=True), primary_key=True),
        sa.Column("id_solicitud_cotizacion", UUID(as_uuid=True), sa.ForeignKey("solicitud_cotizacion.id_solicitud_cotizacion"), nullable=False),
        sa.Column("id_taller", UUID(as_uuid=True), sa.ForeignKey("taller.id_taller"), nullable=False),
        sa.Column("id_sucursal_representante", UUID(as_uuid=True), nullable=False),
        sa.Column("distancia_km", sa.Numeric(8, 2), nullable=True),
        sa.Column("estado_envio", sa.String(length=50), nullable=False, server_default=sa.text("'ENVIADA'")),
        sa.Column("fecha_envio", sa.DateTime(), nullable=False),
        sa.Column("fecha_actualizacion", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_sucursal_representante", "id_taller"],
            ["sucursal_taller.id_sucursal", "sucursal_taller.id_taller"],
            name="fk_solicitud_cotizacion_taller_sucursal",
        ),
        sa.UniqueConstraint("id_solicitud_cotizacion", "id_taller", name="uq_solicitud_cotizacion_taller"),
    )

    op.create_table(
        "cotizacion",
        sa.Column("id_cotizacion", UUID(as_uuid=True), primary_key=True),
        sa.Column("id_solicitud_cotizacion", UUID(as_uuid=True), sa.ForeignKey("solicitud_cotizacion.id_solicitud_cotizacion"), nullable=False),
        sa.Column("id_solicitud_taller", UUID(as_uuid=True), sa.ForeignKey("solicitud_cotizacion_taller.id_solicitud_taller"), nullable=False),
        sa.Column("id_taller", UUID(as_uuid=True), sa.ForeignKey("taller.id_taller"), nullable=False),
        sa.Column("id_sucursal_representante", UUID(as_uuid=True), nullable=False),
        sa.Column("id_admin_responde", UUID(as_uuid=True), sa.ForeignKey("usuarios.id_usuario"), nullable=False),
        sa.Column("mano_obra_estimado", sa.Numeric(12, 2), nullable=False),
        sa.Column("repuestos_estimado", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_estimado", sa.Numeric(12, 2), nullable=False),
        sa.Column("tiempo_estimado_minutos", sa.Integer(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("vigencia_hasta", sa.DateTime(), nullable=False),
        sa.Column("estado", sa.String(length=50), nullable=False, server_default=sa.text("'PENDIENTE'")),
        sa.Column("id_incidente_generado", UUID(as_uuid=True), sa.ForeignKey("incidente.id_incidente"), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_modificacion", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["id_sucursal_representante", "id_taller"],
            ["sucursal_taller.id_sucursal", "sucursal_taller.id_taller"],
            name="fk_cotizacion_sucursal",
        ),
        sa.UniqueConstraint("id_solicitud_cotizacion", "id_taller", name="uq_cotizacion_por_taller"),
    )

    op.add_column("incidente", sa.Column("origen", sa.String(length=50), nullable=True))
    op.add_column("incidente", sa.Column("id_cotizacion_origen", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_incidente_cotizacion_origen",
        "incidente",
        "cotizacion",
        ["id_cotizacion_origen"],
        ["id_cotizacion"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_incidente_cotizacion_origen", "incidente", type_="foreignkey")
    op.drop_column("incidente", "id_cotizacion_origen")
    op.drop_column("incidente", "origen")
    op.drop_table("cotizacion")
    op.drop_table("solicitud_cotizacion_taller")
    op.drop_table("solicitud_cotizacion")
