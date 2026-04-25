import uuid
from fastapi import APIRouter, Depends, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import to_shape

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.packages.identity.domain.models import Usuario
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.workshops.domain.models import Taller
from app.packages.workshops.presentation.schemas import TallerCreate, TallerResponse, StatusUpdate, IncidentAccept, TecnicoResponse, TecnicoCreate, TecnicoUpdate
from app.packages.emergencies.presentation.schemas import IncidentResponse, EvidenceResponse
from app.packages.workshops.application.register_workshop import RegisterWorkshopUseCase
from app.packages.workshops.application.update_status import UpdateIncidentStatusUseCase

router = APIRouter()


# ─── Helpers ────────────────────────────────────────────────────────────────

def get_workshop_repository(session: AsyncSession = Depends(get_db)) -> WorkshopRepository:
    return WorkshopRepository(session)


@router.patch("/{workshop_id}/status", response_model=TallerResponse)
async def toggle_workshop_status(
    workshop_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    repo: WorkshopRepository = Depends(get_workshop_repository),
):
    """Cambia el estado de activación de un taller. Reservado para SuperAdmin."""
    from app.packages.identity.domain.models import ROL_SUPERADMIN
    if current_user.rol_nombre != ROL_SUPERADMIN:
        raise ForbiddenError("Solo el SuperAdmin puede cambiar el estado de los talleres.")
    
    taller = await repo.get_by_id(workshop_id)
    if not taller:
        raise NotFoundError("Taller no encontrado.")
    
    # Toggle del estado
    taller.is_active = not taller.is_active
    updated_taller = await repo.update_workshop(taller)
    return _build_taller_response(updated_taller)


def _build_taller_response(taller: Taller) -> TallerResponse:
    """
    Construye el TallerResponse extrayendo latitud y longitud del campo
    Geography (PostGIS) del modelo. Si el campo es None, retorna None en ambos.
    """
    latitud = None
    longitud = None

    if taller.ubicacion is not None:
        try:
            point = to_shape(taller.ubicacion)
            # Geography POINT se almacena como POINT(longitud latitud)
            longitud = point.x
            latitud = point.y
        except Exception:
            pass  # Si el campo no puede parsearse, retornamos None

    return TallerResponse(
        id_taller=taller.id_taller,
        nombre=taller.nombre,
        nit=taller.nit,
        telefono=taller.telefono,
        email=taller.email,
        direccion=taller.direccion,
        latitud=latitud,
        longitud=longitud,
        is_active=taller.is_active,
    )


def _build_incident_response(incident) -> IncidentResponse:
    """
    Transforma un objeto Incidente a IncidentResponse,
    extrayendo coordenadas de PostGIS y formateando fechas.
    """
    latitud = None
    longitud = None

    if incident.ubicacion_emergencia is not None:
        try:
            point = to_shape(incident.ubicacion_emergencia)
            longitud = point.x
            latitud = point.y
        except Exception:
            pass

    return IncidentResponse(
        id_incidente=incident.id_incidente,
        id_vehiculo=incident.id_vehiculo,
        id_taller=incident.id_taller,
        descripcion=incident.descripcion,
        telefono=incident.telefono,
        estado_incidente=incident.estado_incidente,
        prioridad_incidente=incident.prioridad_incidente,
        transcripcion_audio=incident.transcripcion_audio,
        resumen_ia=incident.resumen_ia,
        analisis_consolidado=incident.analisis_consolidado,
        fecha_reporte=incident.fecha_reporte.isoformat() if incident.fecha_reporte else None,
        latitud=latitud,
        longitud=longitud,
        evidencias=[EvidenceResponse.model_validate(e) for e in incident.evidencias]
    )


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[TallerResponse])
async def list_all_workshops(
    current_user: Usuario = Depends(get_current_active_user),
    repo: WorkshopRepository = Depends(get_workshop_repository),
):
    """Listado global de talleres. Reservado para SuperAdmin."""
    from app.packages.identity.domain.models import ROL_SUPERADMIN
    if current_user.rol_nombre != ROL_SUPERADMIN:
        raise ForbiddenError("Solo el SuperAdmin puede ver la lista global de talleres.")
    
    talleres = await repo.get_all()
    return [_build_taller_response(t) for t in talleres]


@router.post("/", response_model=TallerResponse, status_code=status.HTTP_201_CREATED)
async def register_workshop(
    taller_in: TallerCreate,
    current_user: Usuario = Depends(get_current_active_user),
    repo: WorkshopRepository = Depends(get_workshop_repository)
):
    """(CU13) Registrar un nuevo taller. Requiere rol admin_taller."""
    use_case = RegisterWorkshopUseCase(repo)
    taller = await use_case.execute(current_user, taller_in)
    return _build_taller_response(taller)


@router.get("/me", response_model=TallerResponse)
async def get_my_workshop(
    current_user: Usuario = Depends(get_current_active_user),
    repo: WorkshopRepository = Depends(get_workshop_repository),
):
    """
    Retorna el taller administrado por el usuario autenticado.
    Incluye latitud y longitud extraídas del campo Geography de PostGIS
    para que el frontend pueda renderizarlas en el mapa de Leaflet.
    """
    taller = await repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise NotFoundError("No tienes ningún taller registrado.")
    return _build_taller_response(taller)

@router.put("/me", response_model=TallerResponse)
async def update_my_workshop(
    taller_in: TallerCreate,
    current_user: Usuario = Depends(get_current_active_user),
    repo: WorkshopRepository = Depends(get_workshop_repository),
):
    """(CU extra) Actualizar los datos del taller del usuario logueado."""
    from app.packages.workshops.application.update_workshop import UpdateWorkshopUseCase
    use_case = UpdateWorkshopUseCase(repo)
    taller = await use_case.execute(current_user, taller_in)
    return _build_taller_response(taller)


@router.get("/{taller_id}", response_model=TallerResponse)
async def get_workshop(
    taller_id: uuid.UUID,
    repo: WorkshopRepository = Depends(get_workshop_repository),
):
    """Consultar un taller por su ID."""
    taller = await repo.get_by_id(taller_id)
    if not taller:
        raise NotFoundError("Taller no encontrado.")
    return _build_taller_response(taller)


@router.get("/me/assignments", response_model=list[IncidentResponse])
async def list_my_assignments(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Lista las emergencias del taller vinculado al usuario logueado."""
    workshop_repo = WorkshopRepository(db)
    incident_repo = IncidentRepository(db)

    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")

    incidentes = await incident_repo.get_by_workshop(taller.id_taller)
    return [_build_incident_response(i) for i in incidentes]


@router.patch("/me/assignments/{incident_id}/status", response_model=IncidentResponse)
async def update_assignment_status(
    incident_id: uuid.UUID,
    update_in: StatusUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza el estado de un incidente asignado al taller del usuario autenticado."""
    workshop_repo = WorkshopRepository(db)
    incident_repo = IncidentRepository(db)

    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")

    use_case = UpdateIncidentStatusUseCase(incident_repo)
    incident = await use_case.execute(
        id_taller=taller.id_taller,
        id_incidente=incident_id,
        nuevo_estado=update_in.nuevo_estado,
        actor_nombre=current_user.nombre,
    )

    # Notificar
    from app.core.notifications import manager
    await manager.notify_workshop(str(taller.id_taller), {"type": "STATUS_UPDATED", "id": str(incident_id)})
    await manager.notify_admins({"type": "STATUS_UPDATED", "id": str(incident_id)})

    return _build_incident_response(incident)

# --- Técnicos ---

@router.post("/me/technicians", response_model=TecnicoResponse, status_code=status.HTTP_201_CREATED)
async def register_technician(
    tecnico_in: TecnicoCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU14) Registrar un nuevo mecánico para el taller del usuario logueado."""
    from app.packages.workshops.application.manage_technicians import ManageTechniciansUseCase
    from app.packages.identity.infrastructure.repositories import UserRepository
    
    use_case = ManageTechniciansUseCase(WorkshopRepository(db), UserRepository(db))
    return await use_case.add_technician(current_user, tecnico_in)

@router.get("/me/technicians", response_model=list[TecnicoResponse])
async def list_technicians(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU14) Listar todos los mecánicos del taller del usuario logueado."""
    from app.packages.workshops.application.manage_technicians import ManageTechniciansUseCase
    from app.packages.identity.infrastructure.repositories import UserRepository
    
    use_case = ManageTechniciansUseCase(WorkshopRepository(db), UserRepository(db))
    return await use_case.list_technicians(current_user)


@router.put("/me/technicians/{tecnico_id}", response_model=TecnicoResponse)
async def update_technician(
    tecnico_id: uuid.UUID,
    tecnico_in: "TecnicoUpdate",
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU14) Actualizar nombre y teléfono de un técnico del taller."""
    from app.packages.workshops.domain.models import Tecnico
    from sqlalchemy.future import select

    workshop_repo = WorkshopRepository(db)
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")

    result = await db.execute(
        select(Tecnico).where(
            Tecnico.id_tecnico == tecnico_id,
            Tecnico.id_taller == taller.id_taller
        )
    )
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise NotFoundError("Técnico no encontrado en este taller.")

    if tecnico_in.nombre is not None:
        tecnico.nombre = tecnico_in.nombre
    if tecnico_in.telefono is not None:
        tecnico.telefono = tecnico_in.telefono

    db.add(tecnico)
    await db.commit()
    await db.refresh(tecnico)
    return tecnico


@router.patch("/me/technicians/{tecnico_id}/status", response_model=TecnicoResponse)
async def toggle_technician_status(
    tecnico_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU14) Soft Delete: Activar o desactivar un técnico del taller."""
    from app.packages.workshops.domain.models import Tecnico
    from sqlalchemy.future import select

    workshop_repo = WorkshopRepository(db)
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")

    result = await db.execute(
        select(Tecnico).where(
            Tecnico.id_tecnico == tecnico_id,
            Tecnico.id_taller == taller.id_taller
        )
    )
    tecnico = result.scalar_one_or_none()
    if not tecnico:
        raise NotFoundError("Técnico no encontrado en este taller.")

    tecnico.estado = not tecnico.estado  # Toggle
    db.add(tecnico)
    await db.commit()
    await db.refresh(tecnico)
    return tecnico


@router.post("/me/assignments/{incident_id}/accept", response_model=IncidentResponse)
async def accept_assignment(
    incident_id: uuid.UUID,
    accept_in: IncidentAccept,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU16) Aceptar un incidente y asignar un técnico."""
    from app.packages.workshops.application.accept_reject_incident import AcceptRejectIncidentUseCase
    from app.packages.assignment.infrastructure.repositories import AssignmentRepository
    
    workshop_repo = WorkshopRepository(db)
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")
        
    use_case = AcceptRejectIncidentUseCase(IncidentRepository(db), AssignmentRepository(db))
    incident = await use_case.accept(taller.id_taller, incident_id, accept_in.id_tecnico, current_user.nombre)

    # Notificar
    from app.core.notifications import manager
    await manager.notify_workshop(str(taller.id_taller), {"type": "ASSIGNMENT_ACCEPTED", "id": str(incident_id)})
    await manager.notify_admins({"type": "ASSIGNMENT_ACCEPTED", "id": str(incident_id)})

    return _build_incident_response(incident)

@router.post("/me/assignments/{incident_id}/reject", response_model=Optional[IncidentResponse])
async def reject_assignment(
    incident_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU16) Rechazar un incidente. Dispara la re-asignación inteligente."""
    from app.packages.workshops.application.accept_reject_incident import AcceptRejectIncidentUseCase
    from app.packages.assignment.infrastructure.repositories import AssignmentRepository
    
    workshop_repo = WorkshopRepository(db)
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")
        
    use_case = AcceptRejectIncidentUseCase(IncidentRepository(db), AssignmentRepository(db))
    # Al rechazar, el resultado podría ser una nueva asignación o None si no hay más talleres
    await use_case.reject(taller.id_taller, incident_id, current_user.nombre)
    
    # Retornamos el incidente actualizado (ahora con id_taller=None o nuevo id_taller)
    incident = await IncidentRepository(db).get_by_id(incident_id)
    
    # Notificar
    from app.core.notifications import manager
    await manager.notify_workshop(str(taller.id_taller), {"type": "ASSIGNMENT_REJECTED", "id": str(incident_id)})
    await manager.notify_admins({"type": "ASSIGNMENT_REJECTED", "id": str(incident_id)})
    
    return _build_incident_response(incident) if incident else None
