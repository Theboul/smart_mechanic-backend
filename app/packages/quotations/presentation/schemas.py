from datetime import datetime
from decimal import Decimal
from typing import Optional, List
import uuid

from pydantic import BaseModel, Field


class QuotationCompatibilityQuery(BaseModel):
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    categoria_servicio: Optional[str] = None
    radius_km: float = Field(10.0, gt=0, le=100)


class QuotationRequestCreate(BaseModel):
    id_vehiculo: uuid.UUID
    latitud: float = Field(..., ge=-90, le=90)
    longitud: float = Field(..., ge=-180, le=180)
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None
    prioridad: str = Field("MEDIA", pattern="^(BAJA|MEDIA|ALTA|CRITICA)$")
    categoria_servicio: Optional[str] = None
    radius_km: float = Field(10.0, gt=0, le=100)


class QuotationRequestSelect(BaseModel):
    id_cotizacion: uuid.UUID


class QuotationWorkshopQuoteCreate(BaseModel):
    mano_obra_estimado: Decimal = Field(..., ge=0)
    repuestos_estimado: Decimal = Field(..., ge=0)
    total_estimado: Decimal = Field(..., ge=0)
    tiempo_estimado_minutos: int = Field(..., ge=30, le=2880)
    observaciones: Optional[str] = None
    vigencia_horas: int = Field(48, ge=1, le=720)


class QuotationWorkshopRejectCreate(BaseModel):
    motivo: Optional[str] = None


class QuotationWorkshopOptionResponse(BaseModel):
    id_taller: uuid.UUID
    id_sucursal_representante: uuid.UUID
    workshop_name: Optional[str] = None
    branch_name: Optional[str] = None
    distancia_km: Optional[Decimal] = None

    model_config = {"from_attributes": True}


class QuotationRequestResponse(BaseModel):
    id_solicitud_cotizacion: uuid.UUID
    id_cliente: uuid.UUID
    id_vehiculo: uuid.UUID
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    vehicle_label: Optional[str] = None
    vehicle_brand: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_plate: Optional[str] = None
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None
    prioridad: str
    categoria_servicio: Optional[str] = None
    estado: str
    fecha_vencimiento: datetime
    fecha_creacion: datetime
    fecha_modificacion: datetime
    compatible_workshops: List[QuotationWorkshopOptionResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class QuotationWorkshopInboxItemResponse(BaseModel):
    id_solicitud_taller: uuid.UUID
    id_solicitud_cotizacion: uuid.UUID
    id_taller: uuid.UUID
    id_sucursal_representante: uuid.UUID
    workshop_name: Optional[str] = None
    branch_name: Optional[str] = None
    estado_envio: str
    fecha_envio: datetime
    fecha_actualizacion: datetime
    request: QuotationRequestResponse

    model_config = {"from_attributes": True}


class QuotationResponse(BaseModel):
    id_cotizacion: uuid.UUID
    id_solicitud_cotizacion: uuid.UUID
    id_solicitud_taller: uuid.UUID
    id_taller: uuid.UUID
    id_sucursal_representante: uuid.UUID
    id_admin_responde: uuid.UUID
    mano_obra_estimado: Decimal
    repuestos_estimado: Decimal
    total_estimado: Decimal
    tiempo_estimado_minutos: int
    observaciones: Optional[str] = None
    vigencia_hasta: datetime
    estado: str
    id_incidente_generado: Optional[uuid.UUID] = None
    fecha_creacion: datetime
    fecha_modificacion: datetime

    workshop_name: Optional[str] = None
    branch_name: Optional[str] = None
    responder_name: Optional[str] = None

    model_config = {"from_attributes": True}


class QuotationIncidentResponse(BaseModel):
    id_incidente: uuid.UUID
    id_taller: Optional[uuid.UUID] = None
    id_sucursal: Optional[uuid.UUID] = None
    id_cotizacion_origen: Optional[uuid.UUID] = None
    origen: Optional[str] = None
    estado_incidente: str
    prioridad_incidente: str

    model_config = {"from_attributes": True}
