import uuid
from datetime import datetime, timedelta

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.notifications import manager
from app.packages.identity.domain.models import Usuario
from app.packages.quotations.application.services import QuotationService
from app.packages.quotations.domain.models import SolicitudCotizacion, SolicitudCotizacionTaller

QUOTE_EXPIRATION_HOURS = 48


class CreateQuotationRequestUseCase(QuotationService):
    async def execute(
        self,
        *,
        creator: Usuario,
        id_vehiculo: uuid.UUID,
        latitud: float,
        longitud: float,
        descripcion: str | None,
        observaciones: str | None,
        prioridad: str,
        categoria_servicio: str | None,
        radius_km: float,
    ):
        if creator.rol_nombre != "cliente":
            raise ForbiddenError("Solo un cliente puede crear una solicitud de cotizacion.")

        vehicle = await self.user_repo.get_vehicle_by_id(id_vehiculo)
        if not vehicle:
            raise NotFoundError("Vehiculo no encontrado.")
        if vehicle.id_usuario != creator.id_usuario:
            raise ForbiddenError("El vehiculo no pertenece al usuario autenticado.")

        compatible = await self.search_compatible_workshops(
            latitud=latitud,
            longitud=longitud,
            categoria_servicio=categoria_servicio,
            radius_km=radius_km,
        )

        request = SolicitudCotizacion(
            id_solicitud_cotizacion=uuid.uuid4(),
            id_cliente=creator.id_usuario,
            id_vehiculo=vehicle.id_vehiculo,
            ubicacion_cliente=self._point_wkt(latitud, longitud),
            descripcion=descripcion,
            observaciones=observaciones,
            prioridad=prioridad,
            categoria_servicio=categoria_servicio,
            estado="ABIERTA" if compatible else "SIN_PROPUESTAS",
            fecha_vencimiento=datetime.utcnow() + timedelta(hours=QUOTE_EXPIRATION_HOURS),
        )

        self.db.add(request)
        await self.db.flush()

        links: list[SolicitudCotizacionTaller] = []
        for branch, distance_km in compatible:
            link = SolicitudCotizacionTaller(
                id_solicitud_taller=uuid.uuid4(),
                id_solicitud_cotizacion=request.id_solicitud_cotizacion,
                id_taller=branch.id_taller,
                id_sucursal_representante=branch.id_sucursal,
                distancia_km=distance_km,
                estado_envio="ENVIADA",
            )
            self.db.add(link)
            links.append(link)

        await self.db.commit()
        await self.db.refresh(request)
        for link in links:
            await self.db.refresh(link)

        for branch, _distance in compatible:
            try:
                await manager.notify_workshop(
                    str(branch.id_taller),
                    {
                        "type": "NEW_QUOTATION_REQUEST",
                        "id_solicitud_cotizacion": str(request.id_solicitud_cotizacion),
                    },
                )
            except Exception as exc:  # pragma: no cover
                from app.packages.quotations.application.services import logger
                logger.warning("No se pudo notificar al taller %s: %s", branch.id_taller, exc)

        return request, links
