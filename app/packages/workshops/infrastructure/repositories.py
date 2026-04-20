from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
import uuid

from app.packages.workshops.domain.models import Taller, AdministradorTaller


class WorkshopRepository:
    """Operaciones de BD para la entidad Taller y sus relaciones."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_workshop(self, taller: Taller) -> Taller:
        try:
            self.session.add(taller)
            await self.session.commit()
            await self.session.refresh(taller)
            return taller
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("El NIT ya está registrado por otro taller.")

    async def get_by_id(self, taller_id: uuid.UUID) -> Optional[Taller]:
        result = await self.session.execute(
            select(Taller).where(Taller.id_taller == taller_id)
        )
        return result.scalars().first()

    async def get_by_nit(self, nit: str) -> Optional[Taller]:
        result = await self.session.execute(
            select(Taller).where(Taller.nit == nit)
        )
        return result.scalars().first()

    async def get_by_admin(self, user_id: uuid.UUID) -> Optional[Taller]:
        """Devuelve el taller vinculado a un administrador (relación 1:1 según el diseño)."""
        result = await self.session.execute(
            select(AdministradorTaller).where(AdministradorTaller.id_usuario == user_id)
        )
        admin_link = result.scalars().first()
        if not admin_link:
            return None
        return await self.get_by_id(admin_link.id_taller)

    async def link_admin(self, admin_link: AdministradorTaller) -> AdministradorTaller:
        self.session.add(admin_link)
        await self.session.commit()
        await self.session.refresh(admin_link)
        return admin_link