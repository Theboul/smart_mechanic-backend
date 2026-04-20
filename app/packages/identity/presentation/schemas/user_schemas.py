from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


# SCHEMA: CU3 – Actualizar Perfil
class UserProfileUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, max_length=20)


# SCHEMA: CU4 – Registro de Vehículos
class VehicleCreate(BaseModel):
    matricula: str = Field(..., max_length=20)
    marca: str = Field(..., max_length=100)
    modelo: str = Field(..., max_length=100)
    ano: int = Field(..., ge=1900, le=2100)
    color: Optional[str] = Field(None, max_length=50)


class VehicleResponse(BaseModel):
    id_vehiculo: uuid.UUID
    id_usuario: uuid.UUID
    matricula: str
    marca: str
    modelo: str
    ano: int
    color: Optional[str]
    foto: Optional[str]

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    id_usuario: uuid.UUID
    nombre: str
    telefono: Optional[str]
    correo: str
    rol_nombre: str
    estado: bool
    vehiculos: List[VehicleResponse] = []

    model_config = {"from_attributes": True}