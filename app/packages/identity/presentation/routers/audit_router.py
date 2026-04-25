from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario, Bitacora, ROL_SUPERADMIN
from app.packages.identity.presentation.schemas.audit_schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit"])


def _get_real_ip(request: Request) -> str:
    """Obtiene la IP real del cliente, considerando proxies (X-Forwarded-For)."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For puede ser una lista separada por comas; tomamos la primera
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
    # --- Filtros ---
    accion: Optional[str] = Query(None, description="Filtrar por nombre de acción"),
    usuario_nombre: Optional[str] = Query(None, description="Buscar por nombre de usuario"),
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    # --- Paginación ---
    page: int = Query(0, ge=0),
    size: int = Query(20, ge=1, le=100),
):
    """(CU24) Consultar la bitácora del sistema con filtros y paginación. Solo SuperAdmin."""
    if current_user.rol_nombre != ROL_SUPERADMIN:
        raise HTTPException(status_code=403, detail="No tiene permisos para ver la bitácora")

    # JOIN con Usuario para traer el nombre
    stmt = (
        select(Bitacora, Usuario.nombre.label("nombre_usuario"))
        .join(Usuario, Bitacora.id_usuario == Usuario.id_usuario)
        .order_by(Bitacora.fecha_hora.desc())
    )

    # Aplicar filtros opcionales
    if accion:
        stmt = stmt.where(Bitacora.accion.ilike(f"%{accion}%"))
    if usuario_nombre:
        stmt = stmt.where(Usuario.nombre.ilike(f"%{usuario_nombre}%"))
    if fecha_inicio:
        stmt = stmt.where(Bitacora.fecha_hora >= fecha_inicio)
    if fecha_fin:
        stmt = stmt.where(Bitacora.fecha_hora <= fecha_fin)

    # Paginación
    stmt = stmt.offset(page * size).limit(size)

    result = await db.execute(stmt)
    rows = result.all()

    # Construir la respuesta enriquecida manualmente
    logs = []
    for row in rows:
        bitacora, nombre_usuario = row
        logs.append(AuditLogResponse(
            id_bitacora=bitacora.id_bitacora,
            id_usuario=bitacora.id_usuario,
            nombre_usuario=nombre_usuario,
            ip=bitacora.ip,
            accion=bitacora.accion,
            descripcion=bitacora.descripcion,
            fecha_hora=bitacora.fecha_hora,
        ))

    return logs

