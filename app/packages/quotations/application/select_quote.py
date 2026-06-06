import uuid
from datetime import datetime

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.core.notifications import manager
from app.packages.assignment.domain.models import AsignacionIncidente
from app.packages.emergencies.domain.models import HistorialIncidente, Incidente
from app.packages.identity.domain.models import Usuario
from app.packages.quotations.application.services import QuotationService, logger


class SelectQuotationUseCase(QuotationService):
    async def execute(
        self,
        *,
        current_user: Usuario,
        request_id: uuid.UUID,
        quote_id: uuid.UUID,
    ) -> Incidente:
        quote = await self.repo.get_quote_by_id(quote_id)
        if not quote:
            raise NotFoundError("Cotizacion no encontrada.")
        if quote.id_solicitud_cotizacion != request_id:
            raise BadRequestError("La cotizacion no pertenece a la solicitud seleccionada.")

        request = await self.repo.get_request_with_details(quote.id_solicitud_cotizacion)
        if not request:
            raise NotFoundError("Solicitud de cotizacion no encontrada.")
        if request.id_cliente != current_user.id_usuario:
            raise ForbiddenError("No tienes permisos para seleccionar esta cotizacion.")
        if request.estado not in ("ABIERTA", "SIN_PROPUESTAS"):
            raise BadRequestError("La solicitud ya no permite seleccionar cotizaciones.")
        if quote.estado not in ("PENDIENTE",):
            raise BadRequestError("La cotizacion ya no puede ser seleccionada.")
        if quote.vigencia_hasta < datetime.utcnow():
            quote.estado = "VENCIDA"
            await self.db.commit()
            raise BadRequestError("La cotizacion seleccionada ya vencio.")

        request.estado = "SELECCIONADA"
        quote.estado = "ACEPTADA"
        for sibling_quote in request.cotizaciones:
            if sibling_quote.id_cotizacion != quote.id_cotizacion and sibling_quote.estado == "PENDIENTE":
                sibling_quote.estado = "RECHAZADA"
        for link in request.talleres:
            if link.id_taller != quote.id_taller and link.estado_envio in ("ENVIADA", "RESPONDIDA"):
                link.estado_envio = "RECHAZADA"

        incident = Incidente(
            id_incidente=uuid.uuid4(),
            id_vehiculo=request.id_vehiculo,
            id_taller=quote.id_taller,
            id_sucursal=quote.id_sucursal_representante,
            id_usuario_cliente=request.id_cliente,
            ubicacion_emergencia=request.ubicacion_cliente,
            telefono=current_user.telefono,
            descripcion=request.descripcion or request.observaciones or "Cotizacion aceptada por el cliente",
            estado_incidente="TALLER_ASIGNADO",
            prioridad_incidente=request.prioridad,
            id_cotizacion_origen=quote.id_cotizacion,
            origen="COTIZACION",
        )

        assignment = AsignacionIncidente(
            id_asignacion=uuid.uuid4(),
            id_incidente=incident.id_incidente,
            id_taller=quote.id_taller,
            id_tecnico=None,
            estado_asignacion="PENDIENTE_ACEPTACION",
            distancia_km=None,
        )

        history = HistorialIncidente(
            id_incidente=incident.id_incidente,
            id_taller=quote.id_taller,
            id_sucursal=quote.id_sucursal_representante,
            incidente_estado_anterior="PENDIENTE",
            incidente_estado_nuevo="TALLER_ASIGNADO",
            historial_actor=f"CLIENTE:{current_user.nombre} (Cotizacion Aceptada)",
            id_usuario_actor=current_user.id_usuario,
        )

        self.db.add(incident)
        await self.db.flush()
        self.db.add(assignment)
        self.db.add(history)

        quote.id_incidente_generado = incident.id_incidente
        await self.db.commit()
        await self.db.refresh(incident)
        await self.db.refresh(quote)

        try:
            await manager.notify_workshop(
                str(quote.id_taller),
                {
                    "type": "QUOTATION_SELECTED",
                    "id_cotizacion": str(quote.id_cotizacion),
                    "id_incidente": str(incident.id_incidente),
                },
            )
            await manager.notify_user(
                str(current_user.id_usuario),
                {
                    "type": "QUOTATION_SELECTED",
                    "id_cotizacion": str(quote.id_cotizacion),
                    "id_incidente": str(incident.id_incidente),
                },
            )
            await manager.notify_admins(
                {
                    "type": "QUOTATION_SELECTED",
                    "id_cotizacion": str(quote.id_cotizacion),
                    "id_incidente": str(incident.id_incidente),
                }
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("No se pudieron enviar notificaciones de cotizacion seleccionada: %s", exc)

        return incident
