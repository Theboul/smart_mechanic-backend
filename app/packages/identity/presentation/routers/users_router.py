from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario
from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.presentation.schemas.auth_schemas import UserResponse
from app.packages.identity.presentation.schemas.user_schemas import UserProfileUpdate, VehicleCreate, VehicleResponse
from app.packages.identity.application.user_use_cases.update_profile import UpdateProfileUseCase
from app.packages.identity.application.user_use_cases.register_vehicle import RegisterVehicleUseCase

users_router = APIRouter(tags=["Perfil del Usuario y Sus Vehículos"])

def get_user_repository(session: AsyncSession = Depends(get_db)):
    return UserRepository(session)

@users_router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Usuario = Depends(get_current_active_user)):
    """Visulizar Perfil: Retorna el usuario extraído del JWT."""
    return current_user

@users_router.put("/me", response_model=UserResponse)
async def update_users_me(
    profile_in: UserProfileUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """(CU3) Gestionar Perfil: Actualizar información personal del usuario JWT."""
    use_case = UpdateProfileUseCase(repo)
    updated_user = await use_case.execute(current_user, profile_in)
    return updated_user

@users_router.post("/me/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle_for_me(
    vehicle_in: VehicleCreate,
    current_user: Usuario = Depends(get_current_active_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """(CU4) Registrar Vehículo: Agrega un vehículo al garaje del cliente autenticado JWT."""
    use_case = RegisterVehicleUseCase(repo)
    vehicle = await use_case.execute(current_user, vehicle_in)
    return vehicle

@users_router.get("/me/vehicles", response_model=List[VehicleResponse])
async def list_my_vehicles(
    current_user: Usuario = Depends(get_current_active_user),
    repo: UserRepository = Depends(get_user_repository)
):
    """Consultar Vehículos: Retorna toda la flota del cliente."""
    return await repo.get_vehicles_by_user(current_user.id_usuario)
