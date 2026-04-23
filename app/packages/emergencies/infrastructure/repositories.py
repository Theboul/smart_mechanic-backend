from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid

from app.packages.emergencies.domain.models import Incidente, EvidenciaIncidente, HistorialIncidente


class IncidentRepository:
    """Operaciones de BD para Incidentes y sus Evidencias."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Incidente ---

    async def create_incident(self, incidente: Incidente) -> Incidente:
        self.session.add(incidente)
        await self.session.commit()
        await self.session.refresh(incidente)
        return incidente

    async def get_by_id(self, incident_id: uuid.UUID) -> Optional[Incidente]:
        result = await self.session.execute(
            select(Incidente).where(Incidente.id_incidente == incident_id)
        )
        return result.scalars().first()

    async def update_incident(self, incidente: Incidente) -> Incidente:
        self.session.add(incidente)
        await self.session.commit()
        await self.session.refresh(incidente)
        return incidente

    async def get_by_workshop(self, taller_id: uuid.UUID) -> List[Incidente]:
        """Obtiene la lista de incidentes asignados a un taller."""
        result = await self.session.execute(
            select(Incidente).where(Incidente.id_taller == taller_id)
            .order_by(Incidente.fecha_reporte.desc())
        )
        return result.scalars().all()

    # --- Evidencias ---

    async def add_evidence(self, evidencia: EvidenciaIncidente) -> EvidenciaIncidente:
        self.session.add(evidencia)
        await self.session.commit()
        await self.session.refresh(evidencia)
        return evidencia

    async def get_evidences_by_incident(self, incident_id: uuid.UUID) -> List[EvidenciaIncidente]:
        result = await self.session.execute(
            select(EvidenciaIncidente).where(EvidenciaIncidente.id_incidente == incident_id)
        )
        return result.scalars().all()

    # --- Historial ---

    async def add_history(self, historial: HistorialIncidente) -> HistorialIncidente:
        self.session.add(historial)
        await self.session.commit()
        await self.session.refresh(historial)
        return historial
