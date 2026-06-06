import uuid

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.notifications import manager
from app.packages.identity.domain.models import Usuario
from app.packages.quotations.application.services import QuotationService, logger


class CancelQuotationRequestUseCase(QuotationService):
    async def execute(
        self,
        *,
        current_user: Usuario,
        request_id: uuid.UUID,
    ):
        request = await self.repo.get_request_with_details(request_id)
        if not request:
            raise NotFoundError("Solicitud de cotizacion no encontrada.")
        if request.id_cliente != current_user.id_usuario:
            raise ForbiddenError("No tienes permisos para cancelar esta solicitud.")
        if request.estado in ("SELECCIONADA", "CERRADA"):
            raise BadRequestError("La solicitud ya no puede cancelarse porque ya fue atendida.")
        if request.estado == "CANCELADA":
            raise BadRequestError("La solicitud ya fue cancelada.")

        request.estado = "CANCELADA"

        for link in request.talleres:
            if link.estado_envio in ("ENVIADA", "RESPONDIDA"):
                link.estado_envio = "CANCELADA"

        for quote in request.cotizaciones:
            if quote.estado in ("PENDIENTE",):
                quote.estado = "CANCELADA"

        await self.db.commit()
        await self.db.refresh(request)

        for link in request.talleres:
            try:
                await manager.notify_workshop(
                    str(link.id_taller),
                    {
                        "type": "QUOTATION_REQUEST_CANCELLED",
                        "id_solicitud_cotizacion": str(request.id_solicitud_cotizacion),
                        "id_solicitud_taller": str(link.id_solicitud_taller),
                    },
                )
            except Exception as exc:  # pragma: no cover
                logger.warning(
                    "No se pudo notificar la cancelacion al taller %s: %s",
                    link.id_taller,
                    exc,
                )

        try:
            await manager.notify_user(
                str(current_user.id_usuario),
                {
                    "type": "QUOTATION_REQUEST_CANCELLED",
                    "id_solicitud_cotizacion": str(request.id_solicitud_cotizacion),
                },
            )
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "No se pudo notificar la cancelacion al cliente %s: %s",
                current_user.id_usuario,
                exc,
            )

        return request
