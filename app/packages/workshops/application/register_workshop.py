from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.workshops.presentation.schemas import TallerCreate, TallerResponse
from app.packages.workshops.domain.models import Taller, AdministradorTaller
from app.packages.identity.domain.models import Usuario, ROL_ADMIN_TALLER
from app.core.exceptions import ForbiddenError, ConflictError, BadRequestError


class RegisterWorkshopUseCase:
    def __init__(self, workshop_repository: WorkshopRepository):
        self.workshop_repository = workshop_repository

    async def execute(self, admin_user: Usuario, taller_in: TallerCreate) -> Taller:
        """(CU13) Validar el rol, verificar unicidad del NIT y persistir el taller con coordenadas PostGIS."""
        if admin_user.rol_nombre != ROL_ADMIN_TALLER:
            raise ForbiddenError("Solo los administradores de taller pueden registrar un negocio.")

        # Validación: un admin solo puede tener 1 taller vinculado
        existing_taller = await self.workshop_repository.get_by_admin(admin_user.id_usuario)
        if existing_taller:
            raise ConflictError("El administrador ya tiene un taller asociado.")

        # Comprobar que el NIT sea único
        if await self.workshop_repository.get_by_nit(taller_in.nit):
            raise ConflictError(f"El NIT '{taller_in.nit}' ya está registrado.")

        # Convertir lat/lon a formato WKT válido para GeoAlchemy2/PostGIS
        # IMPORTANTE: El estándar es POINT(Longitud Latitud)
        point_wkt = f"POINT({taller_in.longitud} {taller_in.latitud})"

        new_taller = Taller(
            nombre=taller_in.nombre,
            nit=taller_in.nit,
            telefono=taller_in.telefono,
            email=taller_in.email,
            direccion=taller_in.direccion,
            ubicacion=point_wkt,
        )

        try:
            taller_creado = await self.workshop_repository.create_workshop(new_taller)
        except ValueError as e:
            raise BadRequestError(str(e))

        # Crear el vínculo en la tabla AdministradorTaller
        admin_link = AdministradorTaller(
            id_usuario=admin_user.id_usuario,
            id_taller=taller_creado.id_taller
        )
        await self.workshop_repository.link_admin(admin_link)

        return taller_creado