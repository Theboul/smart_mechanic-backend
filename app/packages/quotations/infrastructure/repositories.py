import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from app.packages.quotations.domain.models import (
    Cotizacion,
    SolicitudCotizacion,
    SolicitudCotizacionTaller,
)


class QuotationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_request_by_id(self, request_id: uuid.UUID) -> Optional[SolicitudCotizacion]:
        result = await self.session.execute(
            select(SolicitudCotizacion).where(SolicitudCotizacion.id_solicitud_cotizacion == request_id)
        )
        return result.scalars().first()

    async def get_request_with_details(self, request_id: uuid.UUID) -> Optional[SolicitudCotizacion]:
        result = await self.session.execute(
            select(SolicitudCotizacion)
            .options(
                joinedload(SolicitudCotizacion.vehiculo),
                joinedload(SolicitudCotizacion.cliente),
                selectinload(SolicitudCotizacion.talleres).joinedload(SolicitudCotizacionTaller.taller),
                selectinload(SolicitudCotizacion.talleres).joinedload(SolicitudCotizacionTaller.sucursal_representante),
                selectinload(SolicitudCotizacion.cotizaciones),
            )
            .where(SolicitudCotizacion.id_solicitud_cotizacion == request_id)
        )
        return result.unique().scalars().first()

    async def get_link_by_request_and_workshop(
        self,
        request_id: uuid.UUID,
        workshop_id: uuid.UUID,
        branch_id: Optional[uuid.UUID] = None,
    ) -> Optional[SolicitudCotizacionTaller]:
        stmt = select(SolicitudCotizacionTaller).where(
            SolicitudCotizacionTaller.id_solicitud_cotizacion == request_id,
            SolicitudCotizacionTaller.id_taller == workshop_id,
        )
        if branch_id is not None:
            stmt = stmt.where(SolicitudCotizacionTaller.id_sucursal_representante == branch_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_quote_by_id(self, quote_id: uuid.UUID) -> Optional[Cotizacion]:
        result = await self.session.execute(
            select(Cotizacion).where(Cotizacion.id_cotizacion == quote_id)
        )
        return result.scalars().first()

    async def get_quote_with_details(self, quote_id: uuid.UUID) -> Optional[Cotizacion]:
        result = await self.session.execute(
            select(Cotizacion)
            .options(
                joinedload(Cotizacion.taller),
                joinedload(Cotizacion.sucursal_representante),
                joinedload(Cotizacion.admin_responde),
            )
            .where(Cotizacion.id_cotizacion == quote_id)
        )
        return result.unique().scalars().first()

    async def get_active_quote_for_request_and_workshop(
        self,
        request_id: uuid.UUID,
        workshop_id: uuid.UUID,
        branch_id: Optional[uuid.UUID] = None,
    ) -> Optional[Cotizacion]:
        stmt = select(Cotizacion).where(
            Cotizacion.id_solicitud_cotizacion == request_id,
            Cotizacion.id_taller == workshop_id,
        )
        if branch_id is not None:
            stmt = stmt.where(Cotizacion.id_sucursal_representante == branch_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
