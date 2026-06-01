import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.core.config import settings

async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check users
        print("--- USUARIOS ---")
        result = await session.execute(text("SELECT id_usuario, nombre, correo, id_rol FROM usuarios"))
        users = result.fetchall()
        for u in users:
            print(u)
            
        print("\n--- ROLES ---")
        result = await session.execute(text("SELECT id_rol, nombre FROM roles"))
        roles = result.fetchall()
        for r in roles:
            print(r)
            
        print("\n--- ADMINISTRADORTALLER ---")
        result = await session.execute(text("SELECT id_admin_taller, id_usuario, id_taller FROM administradortaller"))
        admins = result.fetchall()
        for a in admins:
            print(a)
            
        print("\n--- USUARIO_TALLER ---")
        result = await session.execute(text("SELECT id_usuario_taller, id_usuario, id_taller, id_sucursal, rol_contexto FROM usuario_taller"))
        ut = result.fetchall()
        for record in ut:
            print(record)

        print("\n--- TALLER ---")
        result = await session.execute(text("SELECT id_taller, nombre, email FROM taller"))
        t = result.fetchall()
        for record in t:
            print(record)

        print("\n--- SUCURSAL_TALLER ---")
        result = await session.execute(text("SELECT id_sucursal, id_taller, nombre, direccion FROM sucursal_taller"))
        st = result.fetchall()
        for record in st:
            print(record)
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
