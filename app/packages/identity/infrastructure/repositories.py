from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
import uuid

from app.packages.identity.domain.models import Usuario, Vehiculo, Rol


class UserRepository:
    """Operaciones de BD asíncronas para Usuario, Vehiculo y Rol."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Rol ---

    async def get_rol_by_nombre(self, nombre: str) -> Optional[Rol]:
        """Busca un Rol por su nombre (ej: 'cliente', 'admin_taller')."""
        result = await self.session.execute(select(Rol).where(Rol.nombre == nombre))
        return result.scalars().first()

    # --- Usuario ---

    async def get_by_email(self, email: str) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.correo == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[Usuario]:
        result = await self.session.execute(select(Usuario).where(Usuario.id_usuario == user_id))
        return result.scalars().first()

    async def create_user(self, user: Usuario) -> Usuario:
        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("El correo electrónico ya está registrado.")

    async def update_user(self, user: Usuario) -> Usuario:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # --- Vehiculo ---

    async def create_vehicle(self, vehicle: Vehiculo) -> Vehiculo:
        try:
            self.session.add(vehicle)
            await self.session.commit()
            await self.session.refresh(vehicle)
            return vehicle
        except IntegrityError:
            await self.session.rollback()
            raise ValueError("La matrícula ya se encuentra registrada en otro vehículo.")

    async def get_vehicles_by_user(self, user_id: uuid.UUID) -> List[Vehiculo]:
        result = await self.session.execute(
            select(Vehiculo).where(Vehiculo.id_usuario == user_id)
        )
        return result.scalars().all()

    async def get_vehicle_by_id(self, vehicle_id: uuid.UUID) -> Optional[Vehiculo]:
        result = await self.session.execute(
            select(Vehiculo).where(Vehiculo.id_vehiculo == vehicle_id)
        )
        return result.scalars().first()