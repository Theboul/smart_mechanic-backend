import uuid
from fastapi import APIRouter, Depends, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario
from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.emergencies.presentation.schemas import IncidentCreate, IncidentResponse, EvidenceResponse
from app.packages.emergencies.application.create_incident import CreateIncidentUseCase
from app.packages.emergencies.application.upload_evidence import UploadEvidenceUseCase
from app.packages.emergencies.application.analyze_incident_ai import AnalyzeIncidentAIUseCase
from app.packages.emergencies.application.tasks import run_full_incident_pipeline

router = APIRouter()


def get_incident_repository(session: AsyncSession = Depends(get_db)) -> IncidentRepository:
    return IncidentRepository(session)


def get_user_repository(session: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(session)


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def report_incident(
    incident_in: IncidentCreate,
    current_user: Usuario = Depends(get_current_active_user),
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """(CU5) Reportar una nueva emergencia. El vehículo debe pertenecer al cliente autenticado."""
    use_case = CreateIncidentUseCase(incident_repo, user_repo)
    return await use_case.execute(current_user, incident_in)


@router.post("/{incident_id}/evidence", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    incident_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    evidencia_tipo: str = Form(...),
    current_user: Usuario = Depends(get_current_active_user),
    incident_repo: IncidentRepository = Depends(get_incident_repository),
    user_repo: UserRepository = Depends(get_user_repository)
):
    """(CU6) Cargar evidencia y gatillar análisis de IA en segundo plano."""
    use_case = UploadEvidenceUseCase(incident_repo, user_repo)
    evidence = await use_case.execute(current_user, incident_id, file, evidencia_tipo)
    
    # Disparar el pipeline completo (IA + Búsqueda de Taller)
    background_tasks.add_task(run_full_incident_pipeline, incident_id)
    
    return evidence

@router.post("/{incident_id}/analyze", response_model=IncidentResponse)
async def manual_ai_analysis(
    incident_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    incident_repo: IncidentRepository = Depends(get_incident_repository)
):
    """Disparar manualmente el análisis de IA (útil para pruebas)."""
    ai_use_case = AnalyzeIncidentAIUseCase(incident_repo)
    result = await ai_use_case.execute(incident_id)
    if not result:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Incidente no encontrado.")
    return result


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    incident_repo: IncidentRepository = Depends(get_incident_repository)
):
    """Consultar el detalle completo de un incidente (con sus evidencias)."""
    from app.core.exceptions import NotFoundError
    incidente = await incident_repo.get_by_id(incident_id)
    if not incidente:
        raise NotFoundError("Incidente no encontrado.")
    return incidente
