from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(Exception):
    """Excepción base para todos los errores de Lógica de Negocio (Dominio)."""
    def __init__(self, status_code: int, detail: str, error_code: str | None = None):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "APP_ERROR"


# --- Subclases semánticas para uso en capas de dominio y aplicación ---

class NotFoundError(AppException):
    """Lanzar cuando un recurso buscado no existe en la BD."""
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(status_code=404, detail=detail, error_code="NOT_FOUND")


class ConflictError(AppException):
    """Lanzar cuando se intenta crear un recurso que ya existe (unicidad)."""
    def __init__(self, detail: str = "El recurso ya existe"):
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT")


class ForbiddenError(AppException):
    """Lanzar cuando el usuario autenticado no tiene el rol o permiso necesario."""
    def __init__(self, detail: str = "No tiene permisos para realizar esta acción"):
        super().__init__(status_code=403, detail=detail, error_code="FORBIDDEN")


class UnauthorizedError(AppException):
    """Lanzar cuando las credenciales son inválidas o expiradas."""
    def __init__(self, detail: str = "Credenciales inválidas o expiradas"):
        super().__init__(status_code=401, detail=detail, error_code="UNAUTHORIZED")


class BadRequestError(AppException):
    """Lanzar cuando los datos de entrada no cumplen con la lógica de negocio."""
    def __init__(self, detail: str = "Los datos enviados no son válidos"):
        super().__init__(status_code=400, detail=detail, error_code="BAD_REQUEST")


def setup_exception_handlers(app: FastAPI):
    """Registra los manejadores globales para estandarizar las respuestas JSON de error."""

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
