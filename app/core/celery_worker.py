from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "smart_mechanic_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

# Configurar Celery para auto-descubrir tareas en el paquete de emergencies
celery_app.conf.imports = [
    "app.packages.emergencies.application.tasks"
]

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='America/La_Paz',
    enable_utc=True,
)
