from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.emergencies.presentation.schemas import IncidentResponse

router = APIRouter()

@router.get("/{incident_id}/tracking", response_model=IncidentResponse)
async def track_incident(
    incident_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(Fase 4) Consultar el estado en tiempo real de una emergencia para el cliente."""
    from app.core.exceptions import NotFoundError, ForbiddenError
    incident_repo = IncidentRepository(db)
    
    incidente = await incident_repo.get_by_id(incident_id)
    if not incidente:
        raise NotFoundError("Incidente no encontrado.")
        
    # VALIDACIÓN SAAS: Verificar que el incidente pertenece al usuario logueado
    if incidente.id_usuario != current_user.id_usuario:
        raise ForbiddenError("No tienes permiso para ver el estado de esta emergencia.")
    
    return incidente
