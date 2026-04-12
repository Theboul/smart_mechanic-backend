from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class AppException(Exception):
    """
    Excepción base para todos los errores de Lógica de Negocio (Dominio).
    Úsala en tus Casos de Uso para no tener que depender de las excepciones de FastAPI.
    """
    def __init__(self, status_code: int, detail: str, error_code: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "APP_ERROR"


def setup_exception_handlers(app: FastAPI):
    """
    Registra los manejadores globales para estandarizar las respuestas JSON de error en toda la aplicación.
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Los datos enviados son inválidos o están incompletos.",
                    "details": exc.errors()
                }
            }
        )
