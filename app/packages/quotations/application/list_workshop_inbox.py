from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload

from app.packages.quotations.application.services import QuotationService
from app.packages.quotations.domain.models import Cotizacion, SolicitudCotizacion, SolicitudCotizacionTaller


class ListWorkshopInboxUseCase(QuotationService):
    async def execute(self, *, workshop_id: UUID, branch_id: UUID | None = None):
        stmt = (
            select(SolicitudCotizacionTaller)
            .options(
                joinedload(SolicitudCotizacionTaller.solicitud).joinedload(SolicitudCotizacion.vehiculo),
                joinedload(SolicitudCotizacionTaller.solicitud).joinedload(SolicitudCotizacion.cliente),
                joinedload(SolicitudCotizacionTaller.solicitud).selectinload(SolicitudCotizacion.cotizaciones),
                joinedload(SolicitudCotizacionTaller.solicitud)
                .selectinload(SolicitudCotizacion.talleres)
                .joinedload(SolicitudCotizacionTaller.taller),
                joinedload(SolicitudCotizacionTaller.solicitud)
                .selectinload(SolicitudCotizacion.talleres)
                .joinedload(SolicitudCotizacionTaller.sucursal_representante),
                joinedload(SolicitudCotizacionTaller.taller),
                joinedload(SolicitudCotizacionTaller.sucursal_representante),
                joinedload(SolicitudCotizacionTaller.cotizacion).joinedload(Cotizacion.admin_responde),
            )
            .where(SolicitudCotizacionTaller.id_taller == workshop_id)
            .order_by(SolicitudCotizacionTaller.fecha_envio.desc())
        )
        if branch_id is not None:
            stmt = stmt.where(SolicitudCotizacionTaller.id_sucursal_representante == branch_id)

        result = await self.db.execute(stmt)
        return list(result.unique().scalars().all())
