# Guía de Testing - Smart Mechanic Backend

Este documento describe la arquitectura de pruebas implementada para validar la lógica de negocio del Ciclo 2.

## Arquitectura de Pruebas

Se ha optado por **Tests Unitarios** utilizando Mocks para aislar los casos de uso. Esto permite:
1.  Ejecución extremadamente rápida.
2.  No dependencia de una base de datos real o APIs externas (Roboflow/Gemini).
3.  Validación pura de las reglas de negocio.

## Estructura de Archivos

```text
tests/
├── packages/
│   ├── emergencies/
│   │   └── test_analyze_incident_ai.py    # Test del "Cerebro" IA
│   ├── assignment/
│   │   └── test_match_workshop.py         # Test del Motor de Asignación
│   ├── workshops/
│   │   └── test_update_status.py          # Test de Operativa y Multi-Tenancy
│   └── finance/
│       └── test_close_incident.py         # Test de Comisiones y Pagos
```

## Requisitos

Asegúrate de tener instaladas las dependencias de desarrollo:

```bash
pip install pytest pytest-asyncio
```

## Cómo Ejecutar los Tests

### Ejecutar todos los tests
```bash
pytest tests/
```

### Ejecutar un paquete específico
```bash
pytest tests/packages/emergencies/
```

### Ver salida detallada (Verbose)
```bash
pytest -v tests/
```

## Consideraciones de SaaS y Multi-Tenancy

Los tests en `tests/packages/workshops/test_update_status.py` incluyen validaciones de seguridad donde se intenta forzar el acceso a un incidente desde un taller no autorizado, esperando que el sistema lance una `ForbiddenError`. Esto garantiza la integridad de los datos en un entorno compartido.
