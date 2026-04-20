from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.presentation.schemas.auth_schemas import UserCreate, UserResponse, TokenSchema, UserLogin
from app.packages.identity.domain.models import ROL_CLIENTE

from app.packages.identity.application.auth_use_cases.register_user import RegisterUserUseCase
from app.packages.identity.application.auth_use_cases.login_user import LoginUserUseCase

auth_router = APIRouter()

def get_user_repository(session: AsyncSession = Depends(get_db)):
    return UserRepository(session)

@auth_router.post("/register/cliente", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_cliente(user_in: UserCreate, repo: UserRepository = Depends(get_user_repository)):
    """(CU1) Endpoint para el registro público de nuevos clientes"""
    use_case = RegisterUserUseCase(repo)
    user = await use_case.execute(user_in, rol_nombre=ROL_CLIENTE)
    return user

@auth_router.post("/login", response_model=TokenSchema)
async def login_for_access_token(
    user_cred: UserLogin, 
    repo: UserRepository = Depends(get_user_repository)
):
    """(CU2) Iniciar Sesión con Correo y Contraseña directamente (JSON)"""
    use_case = LoginUserUseCase(repo)
    return await use_case.execute(user_cred)

@auth_router.post("/oauth/token", response_model=TokenSchema, include_in_schema=False)
async def login_oauth_flow(
    form_data: OAuth2PasswordRequestForm = Depends(),
    repo: UserRepository = Depends(get_user_repository)
):
    """(CU2 alternativo) OAuth2 flow requerido internamente por dependencias"""
    user_cred = UserLogin(correo=form_data.username, contrasena=form_data.password)
    use_case = LoginUserUseCase(repo)
    return await use_case.execute(user_cred)
