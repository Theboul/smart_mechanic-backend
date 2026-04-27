import time
import json
from fastapi import Request, BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_token
from app.core.database import AsyncSessionLocal
from app.packages.identity.domain.models import Bitacora
from app.core.audit import save_audit_log
import logging

logger = logging.getLogger(__name__)

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Ejecutar la petición
        response = await call_next(request)

        # 2. Métodos a auditar (Escritura por defecto, podemos añadir GET si es crítico)
        methods_to_audit = ["POST", "PUT", "DELETE", "PATCH"]
        
        if request.method in methods_to_audit:
            try:
                user_id = None
                
                # 3. Extraer usuario del Token JWT (Peticiones con sesión iniciada)
                auth_header = request.headers.get("Authorization")
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
                    try:
                        payload = decode_token(token)
                        user_id = payload.get("sub")
                    except Exception as e:
                        logger.warning(f"Auditoría: Token inválido en {request.url.path}: {e}")

                # 4. Caso Especial: Login exitoso
                if not user_id and response.status_code == 200 and "login" in request.url.path:
                    # En el login, el usuario no envía token, lo recibe. 
                    # Pero podemos registrar que hubo un intento de login exitoso.
                    # Como no tenemos el user_id fácilmente aquí sin re-leer el stream,
                    # marcamos como 'SISTEMA:LOGIN' o similar si es crítico.
                    # MEJORA: El backend de login ahora puede inyectar el ID en los headers de respuesta para el middleware.
                    user_id = response.headers.get("X-Audit-User-ID") or "LOGIN_PENDING"

                # 5. Registrar si tenemos el ID o es una acción crítica
                if user_id:
                    ip = request.client.host if request.client else "unknown"
                    path = request.url.path
                    
                    # Descripción personalizada para acciones conocidas
                    desc = f"Status: {response.status_code}"
                    if "login" in path:
                        desc = "Inicio de sesión exitoso"
                    
                    import asyncio
                    asyncio.create_task(save_audit_log(
                        user_id=user_id if user_id != "LOGIN_PENDING" else "00000000-0000-0000-0000-000000000000", # System user or placeholder
                        ip=ip,
                        method=request.method,
                        path=path,
                        status_code=response.status_code,
                        descripcion=desc
                    ))
                
                # OPCIONAL: Si quieres capturar TODO (incluyendo GET) de forma masiva
                # descomenta las siguientes líneas, pero ten cuidado con la saturación de la BD.
                # if request.method == "GET" and user_id:
                #     ... (misma lógica de save_audit_log)

            except Exception as e:
                logger.error(f"Error crítico en AuditMiddleware: {str(e)}")

        return response
