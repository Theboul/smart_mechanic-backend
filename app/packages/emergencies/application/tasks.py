import uuid
import logging
from app.core.database import AsyncSessionLocal
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.assignment.infrastructure.repositories import AssignmentRepository
from app.packages.emergencies.application.analyze_incident_ai import AnalyzeIncidentAIUseCase
from app.packages.assignment.application.match_workshop import MatchWorkshopUseCase

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
        
        # 1. Análisis de IA
        ai_use_case = AnalyzeIncidentAIUseCase(incident_repo)
        incident = await ai_use_case.execute(incident_id)
        
        if not incident:
            logger.error(f"Pipeline falló en análisis de IA para {incident_id}")
            return

        # 2. Asignación automática
        match_use_case = MatchWorkshopUseCase(assignment_repo, incident_repo)
        assignment = await match_use_case.execute(incident_id)
        
        if assignment:
            logger.info(f"Pipeline completado: Incidente {incident_id} asignado automáticamente.")
        else:
            logger.warning(f"Pipeline: Incidente {incident_id} analizado pero no se encontró taller.")
