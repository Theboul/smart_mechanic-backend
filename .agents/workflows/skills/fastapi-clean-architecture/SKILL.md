---
description: Guía al agente para estructurar código en FastAPI usando Clean Architecture orientada a paquetes. Usar al crear nuevos endpoints, servicios, casos de uso o entidades de dominio.
---

---
name: fastapi-clean-architecture
description: Guía al agente para estructurar código en FastAPI usando Clean Architecture orientada a paquetes. Usar al crear nuevos endpoints, servicios, casos de uso o entidades de dominio.
---

# FastAPI Clean Architecture

Instrucciones detalladas para estructurar módulos de negocio en el backend de Smart Mechanic.

## When to use this skill
- Use this when creando un nuevo paquete de características (ej. `workshops`, `emergencies`).
- Use this when refactorizando lógica de negocio o añadiendo nuevos endpoints HTTP en FastAPI.
- This is helpful for mantener la separación de responsabilidades estricta entre BD, Lógica y Presentación.

## How to use it

Sigue este árbol de decisión para saber dónde colocar el código:

1. **¿Es un modelo de Base de Datos o conexión a API externa?**
   -> Colócalo en `app/packages/[nombre]/infrastructure/`.
2. **¿Es la lógica central, reglas de negocio o llamado a la IA (Gemini/Roboflow)?**
   -> Colócalo en `app/packages/[nombre]/application/`.
3. **¿Es una regla pura o definición de entidad independiente de librerías?**
   -> Colócalo en `app/packages/[nombre]/domain/`.
4. **¿Es un endpoint de FastAPI o validación de entrada/salida?**
   -> Colócalo en `app/packages/[nombre]/presentation/` (en `routers.py` o `schemas.py`).

**Convenciones obligatorias:**
- NUNCA devuelvas modelos de SQLAlchemy desde la capa de `presentation`. Debes serializarlos usando Pydantic.
- NUNCA lances `HTTPException` en la capa `application` o `domain`. Lanza excepciones de dominio (ej. `ItemNotFoundError`) y captúralas en `app/core/exceptions.py`.
- Todo el código debe ser asíncrono (`async def` y `await`).