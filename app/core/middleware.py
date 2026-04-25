import time
import json
from fastapi import Request, BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_token
from app.core.database import AsyncSessionLocal
from app.packages.identity.domain.models import Bitacora
from sqlalchemy import insert
import logging

logger = logging.getLogger(__name__)

async def save_audit_log(user_id: str, ip: str, method: str, path: str, status_code: int):
    """Tarea en segundo plano para guardar la bitácora."""
    async with AsyncSessionLocal() as db:
        try:
            stmt = insert(Bitacora).values(
                id_usuario=user_id,
                ip=ip,
                accion=f"{method} {path}",
                descripcion=f"Status: {status_code}"
            )
            await db.execute(stmt)
            await db.commit()
        except Exception as e:
            logger.error(f"Error guardando bitácora: {str(e)}")

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Ejecutar la petición
        response = await call_next(request)

        # 2. Solo auditar métodos de escritura y peticiones exitosas (o intentos serios)
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            try:
                # 3. Intentar obtener el usuario del token
                auth_header = request.headers.get("Authorization")
                user_id = None
                
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        payload = decode_token(token)
                        user_id = payload.get("sub")
                    except:
                        pass # Token inválido o expirado
                
                # 4. Si tenemos usuario, registramos en segundo plano
                if user_id:
                    ip = request.client.host if request.client else "unknown"
                    path = request.url.path
                    
                    # Usamos background tasks del request si están disponibles
                    # En middlewares de BaseHTTPMiddleware, las background tasks se manejan distinto
                    # pero podemos disparar el coroutine directamente o usar un task de asyncio
                    import asyncio
                    asyncio.create_task(save_audit_log(
                        user_id=user_id,
                        ip=ip,
                        method=request.method,
                        path=path,
                        status_code=response.status_code
                    ))
            except Exception as e:
                logger.error(f"Error en AuditMiddleware: {str(e)}")

        return response
