from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.workshops.presentation.schemas import TallerCreate, TallerResponse
from app.packages.workshops.application.register_workshop import RegisterWorkshopUseCase

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
    taller = await repo.get_by_id(uuid.UUID(taller_id))
    if not taller:
        raise NotFoundError("Taller no encontrado.")
    return taller
