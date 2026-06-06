import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.packages.assignment.infrastructure.repositories import AssignmentRepository
from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.quotations.infrastructure.repositories import QuotationRepository
from app.packages.workshops.infrastructure.repositories import WorkshopRepository

logger = logging.getLogger(__name__)


class QuotationService:
    """Base compartida para los casos de uso de cotizaciones."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)
        self.workshop_repo = WorkshopRepository(db)
        self.user_repo = UserRepository(db)
        self.repo = QuotationRepository(db)

    def _point_wkt(self, latitud: float, longitud: float) -> str:
        return f"POINT({longitud} {latitud})"

    def _group_unique_workshops(self, nearby_rows):
        grouped = {}
        for branch, distance in nearby_rows:
            if branch.id_taller not in grouped:
                grouped[branch.id_taller] = (branch, distance)
        return grouped

    async def search_compatible_workshops(
        self,
        *,
        latitud: float,
        longitud: float,
        categoria_servicio: Optional[str] = None,
        radius_km: float = 10.0,
        limit: int = 10,
    ):
        point = self._point_wkt(latitud, longitud)
        nearby = await self.assignment_repo.get_nearby_workshops(
            point=point,
            radius_km=radius_km,
            limit=limit * 3,
            required_specialty=categoria_servicio,
        )
        grouped = self._group_unique_workshops(nearby)
        result = []
        for branch, distance in list(grouped.values())[:limit]:
            result.append((branch, Decimal(str(round(float(distance) / 1000.0, 2)))))
        return result
