from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Motor asíncrono de SQLAlchemy para PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # Ponlo en False en Producción para no llenar la consola de logs SQL
    future=True
)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Clase base de la que heredarán todos nuestros Modelos (entidades fisicas de DB)
Base = declarative_base()

# Dependencia para inyectar en las rutas de FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
