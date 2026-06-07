import uuid
import logging
import asyncio
from app.core.database import AsyncSessionLocal
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.core.celery_worker import celery_app
from app.packages.assignment.infrastructure.repositories import AssignmentRepository
from app.packages.emergencies.application.analyze_incident_ai import AnalyzeIncidentAIUseCase
from app.packages.assignment.application.match_workshop import MatchWorkshopUseCase
from app.core.notifications import manager
from app.core.push_notifications import push_service

logger = logging.getLogger(__name__)

async def run_full_incident_pipeline(incident_id: uuid.UUID):
    """
    Tarea de fondo que ejecuta todo el flujo inteligente:
    1. Análisis de IA (Roboflow + Gemini)
    2. Asignación automática al taller más cercano
    """
    try:
        async with AsyncSessionLocal() as session:
            incident_repo = IncidentRepository(session)
            assignment_repo = AssignmentRepository(session)
            
            # 0. Notificación inmediata de "Solicitud Recibida"
            inc = await incident_repo.get_by_id(incident_id)
            if inc and inc.vehiculo and inc.vehiculo.propietario:
                token = inc.vehiculo.propietario.fcm_token
                if token:
                    logger.info(f"📲 PUSH: Enviando notificación de inicio a token: {token[:15]}...")
                    asyncio.create_task(push_service.send_push_notification(
                        token=token,
                        title="S.O.S RECIBIDO",
                        body="Estamos analizando tu situación con IA. Un momento por favor...",
                        data={"type": "SOS_RECEIVED", "incident_id": str(incident_id)}
                    ))
                else:
                    logger.warning(f"⚠️ PUSH: El usuario {inc.vehiculo.propietario.id_usuario} no tiene token FCM.")
            
            # 1. Análisis de IA
            logger.info(f"🤖 PIPELINE: Iniciando fase IA para incidente {incident_id}")
            ai_use_case = AnalyzeIncidentAIUseCase(incident_repo)
            incident = await ai_use_case.execute(incident_id)
            
            if not incident:
                logger.error(f"❌ PIPELINE: Falló en fase IA para {incident_id}")
                return

            user_id = str(incident.vehiculo.id_usuario)
            fcm_token = incident.vehiculo.propietario.fcm_token if incident.vehiculo.propietario else None

            # INTERCEPTOR: Si los datos están incompletos, abortamos la asignación del taller
            if incident.estado_incidente == "DATOS_INCOMPLETOS":
                logger.warning(f"⚠️ PIPELINE: Datos incompletos para {incident_id}. Abortando fase de asignación de taller.")
                
                # A. WebSocket
                await manager.notify_user(user_id, {
                    "type": "SLOT_FILLING_REQUIRED",
                    "incident_id": str(incident_id),
                    "resumen_ia": incident.resumen_ia
                })
                
                # B. Push
                if fcm_token:
                    logger.info(f"📲 PUSH: Enviando Solicitud de Slot Filling a token: {fcm_token[:15]}...")
                    asyncio.create_task(push_service.send_push_notification(
                        token=fcm_token,
                        title="Información Necesaria",
                        body=incident.resumen_ia or "Se requiere más información de tu emergencia.",
                        data={"type": "SLOT_FILLING_REQUIRED", "incident_id": str(incident_id)}
                    ))
                return
            
            # A. WebSocket
            await manager.notify_user(user_id, {
                "type": "ANALYSIS_COMPLETED",
                "id": str(incident_id),
                "resumen_ia": incident.resumen_ia,
                "analisis_consolidado": incident.analisis_consolidado
            })
            
            # B. Push
            if fcm_token:
                logger.info(f"📲 PUSH: Enviando Análisis IA a token: {fcm_token[:15]}...")
                asyncio.create_task(push_service.send_push_notification(
                    token=fcm_token,
                    title="Análisis de IA Completado",
                    body=f"Hemos analizado tu emergencia: {incident.resumen_ia or 'Revisa los detalles.'}",
                    data={"type": "ANALYSIS_COMPLETED", "incident_id": str(incident_id)}
                ))

            # 2. Asignación automática
            logger.info(f"🛠️ PIPELINE: Iniciando fase de asignación para {incident_id}")
            match_use_case = MatchWorkshopUseCase(assignment_repo, incident_repo)
            assignment = await match_use_case.execute(incident_id)
            
            # Recuperar el taller de forma segura usando el repositorio optimizado
            workshop = None
            if assignment and assignment.id_taller:
                from app.packages.workshops.infrastructure.repositories import WorkshopRepository
                ws_repo = WorkshopRepository(session)
                workshop = await ws_repo.get_by_id(assignment.id_taller)

            if workshop:
                logger.info(f"✅ PIPELINE: Asignado al taller {workshop.nombre}")

                # A. Notificar al taller (Push)
                # El repositorio ya cargó los administradores y sus usuarios gracias al eager loading
                if workshop.administradores:
                    for admin in workshop.administradores:
                        if admin.usuario and admin.usuario.fcm_token:
                            logger.info(f"📲 PUSH: Notificando a admin del taller: {admin.usuario.nombre}")
                            asyncio.create_task(push_service.send_push_notification(
                                token=admin.usuario.fcm_token,
                                title="¡NUEVA EMERGENCIA!",
                                body=f"Vehículo {incident.vehiculo.marca} {incident.vehiculo.modelo} necesita ayuda.",
                                data={"type": "NEW_INCIDENT", "incident_id": str(incident_id)}
                            ))
                
                # B. Notificar al usuario (WebSocket + Push)
                await manager.notify_user(user_id, {
                    "type": "EMERGENCY_ASSIGNED",
                    "incident_id": str(incident_id),
                    "workshop_name": workshop.nombre
                })

                if fcm_token:
                    logger.info(f"📲 PUSH: Enviando Taller Asignado a token: {fcm_token[:15]}...")
                    asyncio.create_task(push_service.send_push_notification(
                        token=fcm_token,
                        title="Taller Asignado",
                        body=f"Tu solicitud ha sido enviada a {workshop.nombre}. Esperando aceptación.",
                        data={"type": "WORKSHOP_ASSIGNED", "incident_id": str(incident_id)}
                    ))
                
                logger.info(f"🏆 PIPELINE: Completado con éxito para {incident_id}")
            else:
                logger.warning(f"⚠️ PIPELINE: Incidente {incident_id} analizado pero no se pudo asignar taller.")

    except Exception as e:
        logger.error(f"💥 PIPELINE ERROR CRITICO: {str(e)}", exc_info=True)

@celery_app.task(name="app.packages.emergencies.application.tasks.run_full_incident_pipeline_task")
def run_full_incident_pipeline_task(incident_id_str: str):
    incident_id = uuid.UUID(incident_id_str)
    asyncio.run(run_full_incident_pipeline(incident_id))
