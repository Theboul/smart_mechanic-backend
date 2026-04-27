import uuid
import logging
import asyncio
from app.core.database import AsyncSessionLocal
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
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
    async with AsyncSessionLocal() as session:
        incident_repo = IncidentRepository(session)
        assignment_repo = AssignmentRepository(session)
        
        # 0. Notificación inmediata de "Solicitud Recibida"
        from app.packages.emergencies.infrastructure.repositories import IncidentRepository
        inc = await incident_repo.get_by_id(incident_id)
        if inc and inc.vehiculo and inc.vehiculo.propietario and inc.vehiculo.propietario.fcm_token:
            asyncio.create_task(push_service.send_push_notification(
                token=inc.vehiculo.propietario.fcm_token,
                title="S.O.S RECIBIDO",
                body="Estamos analizando tu situación con IA. Un momento por favor...",
                data={"type": "SOS_RECEIVED", "incident_id": str(incident_id)}
            ))
        
        # 1. Análisis de IA
        ai_use_case = AnalyzeIncidentAIUseCase(incident_repo)
        incident = await ai_use_case.execute(incident_id)
        
        if not incident:
            logger.error(f"Pipeline falló en análisis de IA para {incident_id}")
            return

        # Notificar al cliente que el análisis de IA está listo (WebSocket + Push)
        if incident.vehiculo and incident.vehiculo.id_usuario:
            user_id = str(incident.vehiculo.id_usuario)
            # Buscamos el token del propietario
            fcm_token = None
            if hasattr(incident.vehiculo, 'propietario') and incident.vehiculo.propietario:
                fcm_token = incident.vehiculo.propietario.fcm_token
            
            logger.info(f"Notificando análisis de IA al usuario {user_id}")
            
            # A. WebSocket
            await manager.notify_user(user_id, {
                "type": "ANALYSIS_COMPLETED",
                "id": str(incident_id),
                "resumen_ia": incident.resumen_ia,
                "analisis_consolidado": incident.analisis_consolidado
            })
            
            # B. Push
            if fcm_token:
                asyncio.create_task(push_service.send_push_notification(
                    token=fcm_token,
                    title="Análisis de IA Completado",
                    body=f"Hemos analizado tu emergencia: {incident.resumen_ia or 'Revisa los detalles.'}",
                    data={"type": "ANALYSIS_COMPLETED", "incident_id": str(incident_id)}
                ))

        # 2. Asignación automática
        match_use_case = MatchWorkshopUseCase(assignment_repo, incident_repo)
        assignment = await match_use_case.execute(incident_id)
        
        if assignment and assignment.taller:
            workshop = assignment.taller
            logger.info(f"Incidente {incident_id} asignado al taller {workshop.nombre}")

            # A. Notificar al taller (Push)
            if workshop.administradores and workshop.administradores[0].usuario.fcm_token:
                target_fcm = workshop.administradores[0].usuario.fcm_token
                asyncio.create_task(push_service.send_push_notification(
                    token=target_fcm,
                    title="¡NUEVA EMERGENCIA!",
                    body=f"Vehículo {incident.vehiculo.marca} {incident.vehiculo.modelo} necesita ayuda."
                ))
            
            # B. Notificar al usuario (WebSocket + Push)
            user_id = str(incident.vehiculo.id_usuario)
            await manager.notify_user(user_id, {
                "type": "EMERGENCY_ASSIGNED",
                "incident_id": str(incident_id),
                "workshop_name": workshop.nombre
            })

            if hasattr(incident.vehiculo, 'propietario') and incident.vehiculo.propietario and incident.vehiculo.propietario.fcm_token:
                asyncio.create_task(push_service.send_push_notification(
                    token=incident.vehiculo.propietario.fcm_token,
                    title="Taller Asignado",
                    body=f"Tu solicitud ha sido enviada a {workshop.nombre}. Esperando aceptación.",
                    data={"type": "WORKSHOP_ASSIGNED", "incident_id": str(incident_id)}
                ))
            
            logger.info(f"Pipeline completado con éxito para incidente {incident_id}")
        else:
            logger.warning(f"Pipeline: Incidente {incident_id} analizado pero no se pudo asignar taller.")
