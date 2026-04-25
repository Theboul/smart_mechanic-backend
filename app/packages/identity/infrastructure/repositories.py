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

    # --- Filtrado Multi-tenant ---

    async def get_all_with_filters(self, role: Optional[str] = None, workshop_id: Optional[uuid.UUID] = None) -> List[Usuario]:
        """
        Obtiene usuarios filtrados por rol y/o taller.
        Si hay workshop_id, filtra administradores, técnicos y clientes atendidos por dicho taller.
        """
        from app.packages.workshops.domain.models import AdministradorTaller, Tecnico
        from app.packages.emergencies.domain.models import Incidente
        from sqlalchemy import or_

        query = select(Usuario).join(Rol, Usuario.id_rol == Rol.id_rol)

        if role:
            query = query.where(Rol.nombre == role)

        if workshop_id:
            # Filtro complejo: Usuarios vinculados al taller por admin, técnico o incidentes (clientes)
            query = query.outerjoin(AdministradorTaller, Usuario.id_usuario == AdministradorTaller.id_usuario)
            query = query.outerjoin(Tecnico, Usuario.id_usuario == Tecnico.id_usuario)
            query = query.outerjoin(Vehiculo, Usuario.id_usuario == Vehiculo.id_usuario)
            query = query.outerjoin(Incidente, Vehiculo.id_vehiculo == Incidente.id_vehiculo)

            query = query.where(
                or_(
                    AdministradorTaller.id_taller == workshop_id,
                    Tecnico.id_taller == workshop_id,
                    Incidente.id_taller == workshop_id
                )
            )

        result = await self.session.execute(query.distinct())
        return list(result.scalars().all())