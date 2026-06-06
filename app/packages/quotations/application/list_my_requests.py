from uuid import UUID

from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import select

from app.packages.quotations.application.services import QuotationService
from app.packages.quotations.domain.models import SolicitudCotizacion, SolicitudCotizacionTaller


class ListMyQuotationRequestsUseCase(QuotationService):
    async def execute(self, client_id: UUID):
        result = await self.db.execute(
            select(SolicitudCotizacion)
            .options(
                joinedload(SolicitudCotizacion.cliente),
                joinedload(SolicitudCotizacion.vehiculo),
                selectinload(SolicitudCotizacion.talleres)
                .joinedload(SolicitudCotizacionTaller.taller),
                selectinload(SolicitudCotizacion.talleres)
                .joinedload(SolicitudCotizacionTaller.sucursal_representante),
                selectinload(SolicitudCotizacion.cotizaciones),
            )
            .where(SolicitudCotizacion.id_cliente == client_id)
            .order_by(SolicitudCotizacion.fecha_creacion.desc())
        )
        return list(result.unique().scalars().all())
