from fastapi import APIRouter

from .auth_router import auth_router
from .users_router import users_router

router = APIRouter()

# Unimos los sub-routers en el router principal de este paquete
router.include_router(auth_router, prefix="/auth", tags=["Autenticación"])
router.include_router(users_router, prefix="/users", tags=["Usuarios"])
