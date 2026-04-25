import asyncio
from sqlalchemy import text
from app.core.database import engine

async def update_schema():
    print("Conectando a la base de datos para actualizar el esquema...")
    async with engine.begin() as conn:
        # 1. Añadir id_tecnico a la tabla incidente
        print("Actualizando tabla 'incidente'...")
        try:
            await conn.execute(text("ALTER TABLE incidente ADD COLUMN id_tecnico UUID REFERENCES usuarios(id_usuario);"))
            print(" - Columna 'id_tecnico' añadida a 'incidente'.")
        except Exception as e:
            print(f" - Nota: {e}")

        # 2. Actualizar tabla asignacion_incidente (hacer id_tecnico opcional y añadir id_taller)
        print("Actualizando tabla 'asignacion_incidente'...")
        try:
            await conn.execute(text("ALTER TABLE asignacion_incidente ALTER COLUMN id_tecnico DROP NOT NULL;"))
            print(" - Columna 'id_tecnico' ahora es opcional en 'asignacion_incidente'.")
        except Exception as e:
            print(f" - Nota: {e}")

        try:
            await conn.execute(text("ALTER TABLE asignacion_incidente ADD COLUMN id_taller UUID REFERENCES taller(id_taller);"))
            print(" - Columna 'id_taller' añadida a 'asignacion_incidente'.")
        except Exception as e:
            print(f" - Nota: {e}")

    print("Esquema actualizado correctamente.")

if __name__ == "__main__":
    asyncio.run(update_schema())
