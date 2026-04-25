from pydantic import BaseModel
from decimal import Decimal

class GlobalStatsResponse(BaseModel):
    total_talleres: int
    total_incidentes: int
    total_comisiones: Decimal
    emergencias_activas: int
