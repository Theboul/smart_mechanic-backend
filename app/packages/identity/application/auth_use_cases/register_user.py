from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.presentation.schemas.auth_schemas import UserCreate
from app.packages.identity.domain.models import Usuario, ROL_CLIENTE
from app.core.security import get_password_hash
from app.core.exceptions import ConflictError, NotFoundError


class RegisterUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_in: UserCreate, rol_nombre: str = ROL_CLIENTE) -> Usuario:
        """(CU1) Registrar un nuevo usuario, validando unicidad de correo y buscando el rol por nombre."""
        # Verificar si existe el usuario
        existing_user = await self.user_repository.get_by_email(user_in.correo)
        if existing_user:
            raise ConflictError("El correo electrónico ya está en uso.")

        # Buscar el objeto Rol en la BD por nombre
        rol = await self.user_repository.get_rol_by_nombre(rol_nombre)
        if not rol:
            raise NotFoundError(f"El rol '{rol_nombre}' no está configurado en el sistema.")

        # Crear la entidad hasheando el password
        new_user = Usuario(
            nombre=user_in.nombre,
            correo=user_in.correo,
            telefono=user_in.telefono,
            contrasena=get_password_hash(user_in.contrasena),
            id_rol=rol.id_rol
        )

        return await self.user_repository.create_user(new_user)
