from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.presentation.schemas.auth_schemas import UserLogin, TokenSchema, UserResponse
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedError, ForbiddenError


class LoginUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_in: UserLogin, ip: str = None) -> TokenSchema:
        """(CU2) Autenticar usuario con correo y contraseña, devolviendo un JWT."""
        user = await self.user_repository.get_by_email(user_in.correo)

        if not user or not verify_password(user_in.contrasena, user.contrasena):
            raise UnauthorizedError("Correo electrónico o contraseña incorrectos.")

        if not user.estado:
            raise ForbiddenError("La cuenta de usuario está desactivada.")

        # El 'sub' lleva el UUID del usuario; 'role' lleva el nombre del rol para el frontend
        access_token = create_access_token(
            data={"sub": str(user.id_usuario), "role": user.rol_nombre}
        )


        return TokenSchema(
            access_token=access_token,
            user=UserResponse.model_validate(user)
        )