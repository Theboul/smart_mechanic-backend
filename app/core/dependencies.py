from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.core.config import settings
from app.core.database import get_db
from app.packages.identity.infrastructure.repositories import UserRepository
from app.packages.identity.domain.models import Usuario

# Esquema de seguridad que intercepta el Header "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/identity/auth/oauth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Usuario:
    """Extrae el UUID del JWT, lo valida y retorna el objeto Usuario real de la BD."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar sus credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_uuid: str = payload.get("sub")
        if user_uuid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repo = UserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_uuid))
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """Asegura que el usuario autenticado esté activo en el sistema."""
    if not current_user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no se encuentra activo."
        )
    return current_user
