from uuid import UUID

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.notifications import manager
from app.packages.identity.domain.models import Usuario
from app.packages.quotations.application.services import QuotationService, logger


class RejectQuotationRequestUseCase(QuotationService):
    async def execute(
        self,
        *,
        current_user: Usuario,
        request_id: UUID,
        selected_branch_id: UUID | None = None,
        motivo: str | None = None,
    ):
        workshop = await self.workshop_repo.get_by_admin(current_user.id_usuario)
        if not workshop:
            raise ForbiddenError("No tienes un taller registrado.")

        link = await self.repo.get_link_by_request_and_workshop(
            request_id=request_id,
            workshop_id=workshop.id_taller,
            branch_id=selected_branch_id,
        )
        if not link:
            raise NotFoundError("La solicitud no fue enviada a esta sucursal.")
        if link.estado_envio != "ENVIADA":
            raise BadRequestError("Esta solicitud ya fue gestionada por esta sucursal.")

        link.estado_envio = "RECHAZADA"
        await self.db.commit()

        request = await self.repo.get_request_by_id(request_id)
        try:
            await manager.notify_user(
                str(request.id_cliente),
                {
                    "type": "QUOTATION_REJECTED",
                    "id_solicitud_cotizacion": str(request_id),
                    "motivo": motivo,
                },
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("No se pudo notificar rechazo a cliente %s: %s", request.id_cliente, exc)

        return link
