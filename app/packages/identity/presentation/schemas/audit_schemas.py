from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Optional

class AuditLogResponse(BaseModel):
    id_bitacora: uuid.UUID
    id_usuario: uuid.UUID
    nombre_usuario: Optional[str] = None   # ← JOIN con la tabla usuarios
    ip: str
    accion: str
    descripcion: Optional[str] = None
    fecha_hora: datetime

    model_config = ConfigDict(from_attributes=True)
