from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.workshops.presentation.schemas import TallerCreate
from app.packages.workshops.domain.models import Taller
from app.packages.identity.domain.models import Usuario, ROL_ADMIN_TALLER
from app.core.exceptions import ForbiddenError, NotFoundError

class UpdateWorkshopUseCase:
    def __init__(self, workshop_repository: WorkshopRepository):
        self.workshop_repository = workshop_repository

    async def execute(self, admin_user: Usuario, taller_in: TallerCreate) -> Taller:
        """Actualizar los datos del taller administrado por el usuario actual."""
        if admin_user.rol_nombre != ROL_ADMIN_TALLER:
            raise ForbiddenError("Solo los administradores de taller pueden editar el negocio.")

        taller = await self.workshop_repository.get_by_admin(admin_user.id_usuario)
        if not taller:
            raise NotFoundError("No tienes un taller registrado para editar.")

        # Convertir lat/lon a formato WKT válido para GeoAlchemy2/PostGIS
        point_wkt = f"POINT({taller_in.longitud} {taller_in.latitud})"

        # Actualizar campos
        taller.nombre = taller_in.nombre
        taller.telefono = taller_in.telefono
        taller.email = taller_in.email
        taller.direccion = taller_in.direccion
        taller.ubicacion = point_wkt
        
        # NOTA: En este diseño, no permitimos cambiar el NIT porque suele ser
        # un identificador fiscal estricto. Si se necesita, habría que validar
        # que el nuevo NIT no pertenezca a otro taller.

        await self.workshop_repository.session.commit()
        await self.workshop_repository.session.refresh(taller)

        return taller
