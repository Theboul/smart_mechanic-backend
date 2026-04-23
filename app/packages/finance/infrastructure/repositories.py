from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
import uuid

from app.packages.finance.domain.models import Pago

class FinanceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_payment(self, pago: Pago) -> Pago:
        self.session.add(pago)
        await self.session.commit()
        await self.session.refresh(pago)
        return pago

    async def get_payment_by_incident(self, id_incidente: uuid.UUID) -> Optional[Pago]:
        result = await self.session.execute(
            select(Pago).where(Pago.id_incidente == id_incidente)
        )
        return result.scalars().first()
