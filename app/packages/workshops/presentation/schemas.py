from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid


# --- Requests ---

class TallerCreate(BaseModel):
    nombre: str = Field(..., max_length=150)
    nit: str = Field(..., max_length=50)
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    direccion: Optional[str] = Field(None, max_length=255)
    latitud: float = Field(..., ge=-90, le=90, description="Latitud GPS del taller")
    longitud: float = Field(..., ge=-180, le=180, description="Longitud GPS del taller")


# --- Responses ---

class TallerResponse(BaseModel):
    id_taller: uuid.UUID
    nombre: str
    nit: str
    telefono: Optional[str]
    email: Optional[str]
    direccion: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}

class StatusUpdate(BaseModel):
    nuevo_estado: str = Field(..., max_length=50, description="Ej: EN_CAMINO, EN_PROGRESO, COMPLETADO")
