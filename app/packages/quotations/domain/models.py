import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography

from app.core.database import Base


SOLICITUD_COTIZACION_ESTADOS = (
    "ABIERTA",
    "SIN_PROPUESTAS",
    "SELECCIONADA",
    "CERRADA",
    "CANCELADA",
)

SOLICITUD_TALLER_ESTADOS = (
    "ENVIADA",
    "RESPONDIDA",
    "RECHAZADA",
    "VENCIDA",
    "CANCELADA",
)

COTIZACION_ESTADOS = (
    "PENDIENTE",
    "ACEPTADA",
    "RECHAZADA",
    "VENCIDA",
    "CANCELADA",
)


class SolicitudCotizacion(Base):
    """Solicitud inicial creada por el cliente para comparar talleres."""

    __tablename__ = "solicitud_cotizacion"

    id_solicitud_cotizacion = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_cliente = Column(UUID(as_uuid=True), ForeignKey("usuarios.id_usuario"), nullable=False)
    id_vehiculo = Column(UUID(as_uuid=True), ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    ubicacion_cliente = Column(Geography("POINT", srid=4326), nullable=False)
    descripcion = Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    prioridad = Column(String(20), default="MEDIA", nullable=False)
    categoria_servicio = Column(String(150), nullable=True)
    estado = Column(String(50), default="ABIERTA", nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    cliente = relationship("app.packages.identity.domain.models.Usuario")
    vehiculo = relationship("app.packages.identity.domain.models.Vehiculo")
    talleres = relationship(
        "SolicitudCotizacionTaller",
        back_populates="solicitud",
        cascade="all, delete-orphan",
    )
    cotizaciones = relationship(
        "Cotizacion",
        back_populates="solicitud",
        cascade="all, delete-orphan",
    )


class SolicitudCotizacionTaller(Base):
    """Envio de una solicitud a un taller con su sucursal representante."""

    __tablename__ = "solicitud_cotizacion_taller"

    id_solicitud_taller = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_solicitud_cotizacion = Column(
        UUID(as_uuid=True),
        ForeignKey("solicitud_cotizacion.id_solicitud_cotizacion"),
        nullable=False,
    )
    id_taller = Column(UUID(as_uuid=True), ForeignKey("taller.id_taller"), nullable=False)
    id_sucursal_representante = Column(UUID(as_uuid=True), nullable=False)
    distancia_km = Column(Numeric(8, 2), nullable=True)
    estado_envio = Column(String(50), default="ENVIADA", nullable=False)
    fecha_envio = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    solicitud = relationship("SolicitudCotizacion", back_populates="talleres")
    taller = relationship("app.packages.workshops.domain.models.Taller")
    sucursal_representante = relationship(
        "app.packages.workshops.domain.models.SucursalTaller",
        primaryjoin="and_(SolicitudCotizacionTaller.id_sucursal_representante==SucursalTaller.id_sucursal, "
                    "SolicitudCotizacionTaller.id_taller==SucursalTaller.id_taller)",
        lazy="selectin",
        viewonly=True,
    )
    cotizacion = relationship(
        "Cotizacion",
        back_populates="solicitud_taller",
        uselist=False,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_sucursal_representante", "id_taller"],
            ["sucursal_taller.id_sucursal", "sucursal_taller.id_taller"],
            name="fk_solicitud_cotizacion_taller_sucursal",
        ),
        UniqueConstraint(
            "id_solicitud_cotizacion",
            "id_taller",
            name="uq_solicitud_cotizacion_taller",
        ),
    )


class Cotizacion(Base):
    """Propuesta economica emitida por un taller para una solicitud."""

    __tablename__ = "cotizacion"

    id_cotizacion = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_solicitud_cotizacion = Column(
        UUID(as_uuid=True),
        ForeignKey("solicitud_cotizacion.id_solicitud_cotizacion"),
        nullable=False,
    )
    id_solicitud_taller = Column(
        UUID(as_uuid=True),
        ForeignKey("solicitud_cotizacion_taller.id_solicitud_taller"),
        nullable=False,
    )
    id_taller = Column(UUID(as_uuid=True), ForeignKey("taller.id_taller"), nullable=False)
    id_sucursal_representante = Column(UUID(as_uuid=True), nullable=False)
    id_admin_responde = Column(UUID(as_uuid=True), ForeignKey("usuarios.id_usuario"), nullable=False)
    mano_obra_estimado = Column(Numeric(12, 2), nullable=False)
    repuestos_estimado = Column(Numeric(12, 2), nullable=False)
    total_estimado = Column(Numeric(12, 2), nullable=False)
    tiempo_estimado_minutos = Column(Integer, nullable=False)
    observaciones = Column(Text, nullable=True)
    vigencia_hasta = Column(DateTime, nullable=False)
    estado = Column(String(50), default="PENDIENTE", nullable=False)
    id_incidente_generado = Column(UUID(as_uuid=True), ForeignKey("incidente.id_incidente"), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    solicitud = relationship("SolicitudCotizacion", back_populates="cotizaciones")
    solicitud_taller = relationship("SolicitudCotizacionTaller", back_populates="cotizacion")
    taller = relationship("app.packages.workshops.domain.models.Taller")
    sucursal_representante = relationship(
        "app.packages.workshops.domain.models.SucursalTaller",
        primaryjoin="and_(Cotizacion.id_sucursal_representante==SucursalTaller.id_sucursal, "
                    "Cotizacion.id_taller==SucursalTaller.id_taller)",
        lazy="selectin",
        viewonly=True,
    )
    admin_responde = relationship("app.packages.identity.domain.models.Usuario")
    incidente_generado = relationship(
        "app.packages.emergencies.domain.models.Incidente",
        foreign_keys=[id_incidente_generado],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_sucursal_representante", "id_taller"],
            ["sucursal_taller.id_sucursal", "sucursal_taller.id_taller"],
            name="fk_cotizacion_sucursal",
        ),
        UniqueConstraint(
            "id_solicitud_cotizacion",
            "id_taller",
            name="uq_cotizacion_por_taller",
        ),
    )
