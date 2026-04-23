from pydantic import BaseModel, ConfigDict
from decimal import Decimal
import uuid
from typing import Optional
from datetime import datetime

class PaymentCreate(BaseModel):
    monto_total: Decimal

class PaymentResponse(BaseModel):
    id_pago: uuid.UUID
    id_incidente: uuid.UUID
    id_taller: uuid.UUID
    monto: Decimal
    monto_comision: Decimal
    estado_pago: str
    fecha_pago: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
