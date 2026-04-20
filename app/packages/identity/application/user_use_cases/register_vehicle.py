from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.presentation.schemas.user_schemas import VehicleCreate
from app.packages.identity.domain.models import Usuario, Vehiculo, ROL_CLIENTE
from app.core.exceptions import ForbiddenError, ConflictError


class RegisterVehicleUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, owner: Usuario, vehicle_in: VehicleCreate) -> Vehiculo:
        """(CU4) Registrar un vehículo en el garaje de un usuario Cliente."""
        if owner.rol_nombre != ROL_CLIENTE:
            raise ForbiddenError("Solo los clientes pueden registrar vehículos privados.")

        new_vehicle = Vehiculo(
            matricula=vehicle_in.matricula.strip().upper(),
            marca=vehicle_in.marca,
            modelo=vehicle_in.modelo,
            ano=vehicle_in.ano,
            color=vehicle_in.color,
            id_usuario=owner.id_usuario
        )

        try:
            return await self.user_repository.create_vehicle(new_vehicle)
        except ValueError as e:
            raise ConflictError(str(e))