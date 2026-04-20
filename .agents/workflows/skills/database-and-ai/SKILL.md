---
description: Instruye al agente sobre el manejo de base de datos asíncrona con SQLAlchemy/PostGIS y la integración de IA (Gemini/Roboflow). Usar al interactuar con datos geoespaciales o prompts de IA.
---

---
name: database-and-ai
description: Instruye al agente sobre el manejo de base de datos asíncrona con SQLAlchemy/PostGIS y la integración de IA (Gemini/Roboflow). Usar al interactuar con datos geoespaciales o prompts de IA.
---

# Database (PostGIS) & AI Integration

Convenciones para persistencia de datos espaciales y comunicación con modelos de Inteligencia Artificial.

## When to use this skill
- Use this when creando tablas o modelos que requieran ubicaciones GPS.
- Use this when implementando la lógica de clasificación de imágenes (Roboflow) o NLP (Gemini).
- This is helpful for asegurar que las coordenadas se guarden correctamente para búsquedas de cercanía.

## How to use it

**Patrones de Base de Datos:**
- Utiliza SIEMPRE UUID (v4) para las claves primarias (`id`), nunca enteros.
- Utiliza SIEMPRE `Geography('POINT', 4326)` de `GeoAlchemy2` para latitud y longitud.

**Patrones de Integración IA (Gemini):**
- Al redactar prompts para la API de LLM, exige el retorno estricto de un JSON.
- Implementa el patrón "Slot Filling": Si faltan datos en la transcripción, la IA debe devolver `{"estado_completado": false, "mensaje_respuesta": "Pregunta por el dato faltante"}`.

**Patrones de Integración IA (Roboflow):**
- Extrae únicamente la clase con mayor índice de `confidence` del array de predicciones. Descartar el resto.