import shutil
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import settings

# Directorio base para almacenamiento local (dentro del proyecto para desarrollo)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def upload_file_local(file_obj, filename: str) -> str:
    """
    Guarda un archivo de forma local en el servidor.
    Retorna la ruta relativa o absoluta donde quedó guardado.
    """
    try:
        # Asegurar que el subdirectorio existe (ej: "evidencias/123-abc/")
        dest_path = UPLOAD_DIR / filename
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar el contenido del archivo
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        # Retornamos la ruta como string (en producción esto sería una URL o ruta de volumen)
        return str(dest_path)
    except Exception as e:
        print(f"Error guardando archivo localmente: {e}")
        return None
