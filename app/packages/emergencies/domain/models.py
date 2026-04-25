import uuid
from sqlalchemy import Column, String, Text, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geography
from datetime import datetime

from app.core.database import Base


class Incidente(Base):
    """Ticket de emergencia reportado por un cliente en campo."""
    __tablename__ = "incidente"

    id_incidente = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_vehiculo = Column(UUID(as_uuid=True), ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    id_taller = Column(UUID(as_uuid=True), ForeignKey("taller.id_taller"), nullable=True)
    id_tecnico = Column(UUID(as_uuid=True), ForeignKey("tecnico.id_tecnico"), nullable=True)

    # Coordenadas GPS de la emergencia — PostGIS POINT
    ubicacion_emergencia = Column(Geography('POINT', srid=4326), nullable=True)

    telefono = Column(String(20), nullable=True)
    descripcion = Column(Text, nullable=True)
    estado_incidente = Column(String(50), default="PENDIENTE", nullable=False)
    prioridad_incidente = Column(String(20), default="MEDIA", nullable=False)

    # Campos enriquecidos por la IA (Fase de procesamiento inteligente)
    transcripcion_audio = Column(Text, nullable=True)
    resumen_ia = Column(Text, nullable=True)
    analisis_consolidado = Column(Text, nullable=True)

    fecha_reporte = Column(DateTime, default=datetime.utcnow, nullable=False)

    vehiculo = relationship("Vehiculo")
    evidencias = relationship("EvidenciaIncidente", back_populates="incidente", cascade="all, delete-orphan")
    historial = relationship("HistorialIncidente", back_populates="incidente", cascade="all, delete-orphan")


class EvidenciaIncidente(Base):
    """Archivos multimedia (fotos, audios) y análisis por IA de un incidente."""
    __tablename__ = "evidencia_incidente"

    id_evidencia = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_incidente = Column(UUID(as_uuid=True), ForeignKey("incidente.id_incidente"), nullable=False)
    evidencia_tipo = Column(String(50), nullable=False)       # "foto", "audio", "video"
    archivo_url = Column(String(500), nullable=False)          # URL en S3
    transcripcion = Column(Text, nullable=True)                # Para audios (Whisper)
    confianza_deteccion = Column(Numeric(5, 4), nullable=True) # Score del modelo de visión
    tipo_de_combustible = Column(String(50), nullable=True)    # Inferido por IA
    analisis_imagen = Column(Text, nullable=True)              # Descripción devuelta por la IA
    fecha_subida = Column(DateTime, default=datetime.utcnow, nullable=False)

    incidente = relationship("Incidente", back_populates="evidencias")


class HistorialIncidente(Base):
    """Registro auditorio de todos los cambios de estado de un incidente."""
    __tablename__ = "historial_incidente"

    id_historial = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_incidente = Column(UUID(as_uuid=True), ForeignKey("incidente.id_incidente"), nullable=False)
    incidente_estado_anterior = Column(String(50), nullable=True)
    incidente_estado_nuevo = Column(String(50), nullable=False)
    historial_actor = Column(String(150), nullable=True)  # Nombre o ID del actor que realizó el cambio
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)

    incidente = relationship("Incidente", back_populates="historial")
