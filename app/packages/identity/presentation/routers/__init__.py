from fastapi import APIRouter

from .auth_router import auth_router
from .users_router import users_router
from .audit_router import router as audit_router

router = APIRouter()

# Unimos los sub-routers en el router principal de este paquete
router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
router.include_router(users_router, prefix="/users", tags=["Usuarios"])
router.include_router(audit_router)
