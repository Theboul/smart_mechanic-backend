from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.exceptions import ForbiddenError, NotFoundError
from app.packages.quotations.application.services import QuotationService
from app.packages.quotations.domain.models import Cotizacion, SolicitudCotizacion


class GetQuotationRequestQuotesUseCase(QuotationService):
    async def execute(self, *, request_id: UUID, client_id: UUID):
        result = await self.repo.get_request_by_id(request_id)
        if not result:
            raise NotFoundError("Solicitud de cotizacion no encontrada.")
        if result.id_cliente != client_id:
            raise ForbiddenError("No tienes permisos para ver esta solicitud.")

        query = await self.db.execute(
            select(Cotizacion)
            .options(
                joinedload(Cotizacion.taller),
                joinedload(Cotizacion.sucursal_representante),
                joinedload(Cotizacion.admin_responde),
            )
            .where(Cotizacion.id_solicitud_cotizacion == request_id)
            .order_by(Cotizacion.fecha_creacion.desc())
        )
        return list(query.unique().scalars().all())
