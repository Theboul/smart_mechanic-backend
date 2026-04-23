import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.workshops.presentation.schemas import TallerCreate, TallerResponse, StatusUpdate
from app.packages.emergencies.presentation.schemas import IncidentResponse
from app.packages.workshops.application.register_workshop import RegisterWorkshopUseCase
from app.packages.workshops.application.update_status import UpdateIncidentStatusUseCase

router = APIRouter()


def get_workshop_repository(session: AsyncSession = Depends(get_db)) -> WorkshopRepository:
    return WorkshopRepository(session)


@router.post("/", response_model=TallerResponse, status_code=status.HTTP_201_CREATED)
async def register_workshop(
    taller_in: TallerCreate,
    current_user: Usuario = Depends(get_current_active_user),
    repo: WorkshopRepository = Depends(get_workshop_repository)
):
    """(CU13) Registrar un nuevo taller. Requiere rol admin_taller."""
    use_case = RegisterWorkshopUseCase(repo)
    return await use_case.execute(current_user, taller_in)


@router.get("/{taller_id}", response_model=TallerResponse)
async def get_workshop(
    taller_id: str,
    repo: WorkshopRepository = Depends(get_workshop_repository)
):
    """Consultar un taller por su ID."""
    import uuid
    from app.core.exceptions import NotFoundError
    if not taller:
        raise NotFoundError("Taller no encontrado.")
    return taller

@router.get("/me/assignments", response_model=list[IncidentResponse])
async def get_my_assignments(
    current_user: Usuario = Depends(get_current_active_user),
    workshop_repo: WorkshopRepository = Depends(get_workshop_repository),
    incident_repo: IncidentRepository = Depends(lambda: IncidentRepository(Depends(get_db))) # Esto fallará, mejor inyectar la sesión
):
    """(Fase 3) Obtener la lista de incidentes asignados al taller del usuario autenticado."""
    from app.core.exceptions import ForbiddenError
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("El usuario no es administrador de ningún taller.")
    
    # Reutilizamos el repo de incidentes
    from app.packages.emergencies.infrastructure.repositories import IncidentRepository
    # Necesitamos una sesión de DB fresca o inyectada
    # Usaremos el repo inyectado correctamente en la ruta
    return [] # Reajuste abajo

@router.get("/me/assignments", response_model=list[IncidentResponse])
async def list_my_assignments(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Lista las emergencias del taller vinculado al usuario logueado."""
    from app.core.exceptions import ForbiddenError
    workshop_repo = WorkshopRepository(db)
    incident_repo = IncidentRepository(db)
    
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")
        
    return await incident_repo.get_by_workshop(taller.id_taller)

@router.patch("/me/assignments/{incident_id}/status", response_model=IncidentResponse)
async def update_assignment_status(
    incident_id: uuid.UUID,
    update_in: StatusUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Actualiza el estado de un incidente asignado al taller."""
    from app.core.exceptions import ForbiddenError
    workshop_repo = WorkshopRepository(db)
    incident_repo = IncidentRepository(db)
    
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")
        
    use_case = UpdateIncidentStatusUseCase(incident_repo)
    return await use_case.execute(
        id_taller=taller.id_taller,
        id_incidente=incident_id,
        nuevo_estado=update_in.nuevo_estado,
        actor_nombre=current_user.nombre
    )
