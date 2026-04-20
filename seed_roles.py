import asyncio
import uuid
from app.core.database import AsyncSessionLocal
from app.packages.identity.domain.models import Rol, ROL_CLIENTE, ROL_ADMIN_TALLER, ROL_SUPERADMIN, ROL_TECNICO

async def seed_roles():
    print("Iniciando seed de roles...")
    async with AsyncSessionLocal() as session:
        roles_to_create = [
            ROL_CLIENTE,
            ROL_ADMIN_TALLER,
            ROL_SUPERADMIN,
            ROL_TECNICO
        ]
        
        for role_name in roles_to_create:
            # Verificar si ya existe
            from sqlalchemy import select
            result = await session.execute(select(Rol).where(Rol.nombre == role_name))
            if not result.scalars().first():
                new_role = Rol(
                    nombre=role_name,
                    descripcion=f"Rol para {role_name}",
                    estado=True
                )
                session.add(new_role)
                print(f"Agregando rol: {role_name}")
            else:
                print(f"Rol ya existe: {role_name}")
        
        await session.commit()
    print("Seed finalizado.")

if __name__ == "__main__":
    asyncio.run(seed_roles())
