import logging
from sqlalchemy import insert
from app.core.database import AsyncSessionLocal
from app.packages.identity.domain.models import Bitacora

logger = logging.getLogger(__name__)

async def save_audit_log(user_id: str, ip: str, method: str, path: str, status_code: int, descripcion: str = None):
    """Tarea en segundo plano para guardar la bitácora de auditoría."""
    async with AsyncSessionLocal() as db:
        try:
            stmt = insert(Bitacora).values(
                id_usuario=user_id,
                ip=ip,
                accion=f"{method} {path}",
                descripcion=descripcion or f"Status: {status_code}"
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            logger.error(f"Error guardando bitácora: {str(e)}")
