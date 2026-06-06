from app.packages.quotations.application.services import QuotationService


class SearchCompatibleWorkshopsUseCase(QuotationService):
    async def execute(
        self,
        *,
        latitud: float,
        longitud: float,
        categoria_servicio: str | None = None,
        radius_km: float = 10.0,
    ):
        return await self.search_compatible_workshops(
            latitud=latitud,
            longitud=longitud,
            categoria_servicio=categoria_servicio,
            radius_km=radius_km,
        )
