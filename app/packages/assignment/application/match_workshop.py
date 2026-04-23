import uuid
import logging
from app.packages.assignment.infrastructure.repositories import AssignmentRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.assignment.domain.models import AsignacionIncidente
from app.packages.emergencies.domain.models import HistorialIncidente

logger = logging.getLogger(__name__)

class MatchWorkshopUseCase:
    """
    Caso de Uso (CU): Asignación Automática de Taller.
    Busca el taller más cercano al incidente y crea la asignación.
    """
    
    def __init__(self, assignment_repo: AssignmentRepository, incident_repo: IncidentRepository):
        self.assignment_repo = assignment_repo
        self.incident_repo = incident_repo

    async def execute(self, id_incidente: uuid.UUID):
        # 1. Obtener el incidente analizado
        incidente = await self.incident_repo.get_by_id(id_incidente)
        if not incidente or not incidente.ubicacion_emergencia:
            logger.warning(f"Incidente {id_incidente} no apto para asignación (falta ubicación)")
            return None
            
        if incidente.id_taller:
            logger.info(f"Incidente {id_incidente} ya tiene taller asignado.")
            return None

        logger.info(f"Buscando taller para incidente {id_incidente} en {incidente.ubicacion_emergencia}")

        # 2. Buscar talleres cercanos (Radio 15km)
        nearby = await self.assignment_repo.get_nearby_workshops(
            point=incidente.ubicacion_emergencia,
            radius_km=15.0,
            limit=1
        )
        
        if not nearby:
            logger.error(f"No se encontraron talleres cerca del incidente {id_incidente}")
            incidente.estado_incidente = "SIN_TALLER_DISPONIBLE"
            await self.incident_repo.session.commit()
            return None

        # Tomamos el primero (el más cercano)
        best_taller, distance_meters = nearby[0]
        
        logger.info(f"Taller encontrado: {best_taller.nombre} a {distance_meters:.2f}m")

        # 3. Crear asignación
        new_assignment = AsignacionIncidente(
            id_incidente=id_incidente,
            id_tecnico=None, # Aún no asignado a un técnico específico, se asigna al taller primero
            estado_asignacion="PENDIENTE_ACEPTACION",
            distancia_km=distance_meters / 1000.0
        )
        
        # Nota: Mi modelo AsignacionIncidente actualmente apunta a id_tecnico.
        # En una lógica real, tal vez necesitemos id_taller en AsignacionIncidente, 
        # o que el primer registro sea al AdministradorTaller.
        # Por ahora, vinculamos el incidente al taller directamente.
        
        incidente.id_taller = best_taller.id_taller
        incidente.estado_incidente = "TALLER_ASIGNADO"
        
        # Historial
        historial = HistorialIncidente(
            id_incidente=id_incidente,
            incidente_estado_anterior="ANALIZADO",
            incidente_estado_nuevo="TALLER_ASIGNADO",
            historial_actor="MATCH_ENGINE_AUTO",
            fecha=None
        )
        incidente.historial.append(historial)

        await self.assignment_repo.create_assignment(new_assignment)
        await self.incident_repo.session.commit()
        
        return new_assignment
