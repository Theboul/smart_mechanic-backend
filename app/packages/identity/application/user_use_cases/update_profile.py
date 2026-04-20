from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.presentation.schemas.user_schemas import UserProfileUpdate
from app.packages.identity.domain.models import Usuario


class UpdateProfileUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, current_user: Usuario, profile_in: UserProfileUpdate) -> Usuario:
        """(CU3) Actualizar campos del perfil del usuario autenticado."""
        if profile_in.nombre is not None:
            current_user.nombre = profile_in.nombre
        if profile_in.telefono is not None:
            current_user.telefono = profile_in.telefono

        return await self.user_repository.update_user(current_user)