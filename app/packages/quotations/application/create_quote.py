import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.notifications import manager
from app.packages.identity.domain.models import Usuario
from app.packages.quotations.application.services import QuotationService, logger
from app.packages.quotations.domain.models import Cotizacion


class CreateWorkshopQuotationUseCase(QuotationService):
    async def execute(
        self,
        *,
        current_user: Usuario,
        request_id: uuid.UUID,
        payload,
        selected_branch_id: uuid.UUID | None = None,
    ):
        workshop = await self.workshop_repo.get_by_admin(current_user.id_usuario)
        if not workshop:
            raise ForbiddenError("No tienes un taller registrado.")

        request = await self.repo.get_request_by_id(request_id)
        if not request:
            raise NotFoundError("Solicitud de cotizacion no encontrada.")
        if request.estado not in ("ABIERTA", "SIN_PROPUESTAS"):
            raise BadRequestError("La solicitud ya no admite nuevas cotizaciones.")

        link = await self.repo.get_link_by_request_and_workshop(
            request_id=request_id,
            workshop_id=workshop.id_taller,
            branch_id=selected_branch_id,
        )
        if not link:
            raise ForbiddenError("Esta solicitud no fue enviada a su taller o sucursal.")
        if link.estado_envio not in ("ENVIADA",):
            raise BadRequestError("Esta solicitud ya fue respondida o rechazada por esta sucursal.")

        existing = await self.repo.get_active_quote_for_request_and_workshop(
            request_id=request_id,
            workshop_id=workshop.id_taller,
            branch_id=link.id_sucursal_representante,
        )
        if existing:
            raise BadRequestError("Ya existe una cotizacion para esta solicitud y taller.")

        total_esperado = (Decimal(payload.mano_obra_estimado) + Decimal(payload.repuestos_estimado)).quantize(Decimal("0.01"))
        total_enviado = Decimal(payload.total_estimado).quantize(Decimal("0.01"))
        if total_enviado != total_esperado:
            raise BadRequestError("El total estimado debe coincidir con mano de obra + repuestos.")

        if request.fecha_vencimiento < datetime.utcnow():
            link.estado_envio = "VENCIDA"
            await self.db.commit()
            raise BadRequestError("La solicitud ya vencio.")

        quote = Cotizacion(
            id_cotizacion=uuid.uuid4(),
            id_solicitud_cotizacion=request.id_solicitud_cotizacion,
            id_solicitud_taller=link.id_solicitud_taller,
            id_taller=workshop.id_taller,
            id_sucursal_representante=link.id_sucursal_representante,
            id_admin_responde=current_user.id_usuario,
            mano_obra_estimado=payload.mano_obra_estimado,
            repuestos_estimado=payload.repuestos_estimado,
            total_estimado=payload.total_estimado,
            tiempo_estimado_minutos=payload.tiempo_estimado_minutos,
            observaciones=payload.observaciones,
            vigencia_hasta=datetime.utcnow() + timedelta(hours=payload.vigencia_horas),
            estado="PENDIENTE",
        )

        link.estado_envio = "RESPONDIDA"
        self.db.add(quote)
        await self.db.commit()
        await self.db.refresh(quote)

        try:
            await manager.notify_user(
                str(request.id_cliente),
                {
                    "type": "NEW_QUOTATION",
                    "id_solicitud_cotizacion": str(request.id_solicitud_cotizacion),
                    "id_cotizacion": str(quote.id_cotizacion),
                },
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("No se pudo notificar al cliente %s: %s", request.id_cliente, exc)

        return quote
