import uuid
import logging
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.emergencies.application.services.vision_service import VisionService
from app.packages.emergencies.application.services.nlp_service import NLPService
from app.packages.emergencies.domain.models import HistorialIncidente

logger = logging.getLogger(__name__)

class AnalyzeIncidentAIUseCase:
    """
    Caso de Uso (CU): Consolidar análisis de IA.
    Toma las evidencias (imágenes/audio) de un incidente y genera un resumen inteligente.
    """
    
    def __init__(self, repo: IncidentRepository):
        self.repo = repo
        self.vision_service = VisionService()
        self.nlp_service = NLPService()

    async def execute(self, id_incidente: uuid.UUID):
        # 1. Obtener el incidente y sus evidencias
        incidente = await self.repo.get_by_id(id_incidente)
        if not incidente:
            return None
        
        logger.info(f"Iniciando análisis inteligente para incidente {id_incidente}")
        
        # 2. Procesar evidencias
        # Buscamos la última foto y el último audio subido (si existen)
        last_photo = next((e for e in reversed(incidente.evidencias) if e.evidencia_tipo == "foto"), None)
        last_audio = next((e for e in reversed(incidente.evidencias) if e.evidencia_tipo == "audio"), None)
        
        vision_results = {}
        nlp_results = {}
        
        if last_photo:
            vision_results = await self.vision_service.analyze_image(last_photo.archivo_url)
            # Actualizar la evidencia con el análisis
            last_photo.analisis_imagen = f"Detectado: {vision_results.get('top_class')}"
            last_photo.confianza_deteccion = vision_results.get("confidence")

        # Siempre analizamos la descripción del incidente con Gemini
        nlp_results = await self.nlp_service.process_report(incidente.descripcion)
        
        if last_audio and nlp_results:
            last_audio.transcripcion = nlp_results.get("summary")
        
        # 3. Consolidar resultados
        # Generamos el resumen inteligente final
        resumen_ia = (
            f"DIAGNÓSTICO IA: {nlp_results.get('summary', 'Reporte verbal no disponible')}. "
            f"EVIDENCIA VISUAL: {vision_results.get('top_class', 'No analizada')}. "
            f"Sugerencia: {nlp_results.get('entities', {}).get('falla', 'Revisión general necesaria')}"
        )
        
        # 4. Actualizar incidente
        incidente.resumen_ia = resumen_ia
        incidente.estado_incidente = "ANALIZADO"
        
        # Guardar historial
        historial = HistorialIncidente(
            id_incidente=id_incidente,
            incidente_estado_anterior="PENDIENTE",
            incidente_estado_nuevo="ANALIZADO",
            historial_actor="AI_BOT",
            fecha=None # El modelo puede tener default
        )
        incidente.historial.append(historial)
        
        await self.repo.session.commit()
        await self.repo.session.refresh(incidente)
        
        logger.info(f"Incidente {id_incidente} analizado correctamente por IA")

        # 5. (CU12) Disparar Asignación Inteligente Automática
        try:
            from app.packages.assignment.application.match_workshop import MatchWorkshopUseCase
            from app.packages.assignment.infrastructure.repositories import AssignmentRepository
            
            assignment_repo = AssignmentRepository(self.repo.session)
            match_use_case = MatchWorkshopUseCase(assignment_repo, self.repo)
            await match_use_case.execute(id_incidente)
            logger.info(f"Asignación automática disparada para incidente {id_incidente}")
        except Exception as e:
            logger.error(f"Error al disparar la asignación automática: {str(e)}")

        return incidente
