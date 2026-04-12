from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API para la gestión del taller mecánico",
    version=settings.VERSION
)

# Configuración de CORS
origins = settings.BACKEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar manejadores de excepciones globales
setup_exception_handlers(app)

# Incluir el router principal que agrupa los demás
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Taller"}
