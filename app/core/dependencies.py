from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db

# Esquema de seguridad que interceptará los HTTP Headers en busca del "Authorization: Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/identity/auth/login")

async def get_current_user_token(token: str = Depends(oauth2_scheme)):
    """Valida el JWT entrante y retorna su contenido crudo (payload)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except jwt.PyJWTError:
        raise credentials_exception


async def get_current_user(payload: dict = Depends(get_current_user_token), db: AsyncSession = Depends(get_db)):
    """
    Toma el token JWT validado y busca al usuario en la base de datos real.
    """
    user_id = payload.get("sub")
    
    # [TO-DO]: Retornar un objeto User real de la base de datos cuando tengamos los modelos
    # Ejemplo real:
    # user = await db.scalar(select(User).where(User.id == user_id))
    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")
    # return user
    
    # Por ahora retornamos un diccionario simulado
    return {"id": user_id, "username": payload.get("username", "Unknown"), "active": True}
