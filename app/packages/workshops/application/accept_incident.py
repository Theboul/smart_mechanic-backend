import uuid
import logging
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.assignment.infrastructure.repositories import AssignmentRepository
from app.packages.emergencies.domain.models import HistorialIncidente
from app.core.exceptions import NotFoundError, ForbiddenError

logger = logging.getLogger(__name__)

class AcceptIncidentUseCase:
    """
    Caso de Uso (CU): Aceptación de Incidente por Taller.
    El administrador del taller acepta la emergencia y asigna un técnico.
    """
    
    def __init__(
        self, 
        workshop_repo: WorkshopRepository, 
        incident_repo: IncidentRepository,
        assignment_repo: AssignmentRepository
    ):
        self.workshop_repo = workshop_repo
        self.incident_repo = incident_repo
        self.assignment_repo = assignment_repo

    async def execute(self, workshop_id: uuid.UUID, incident_id: uuid.UUID, tecnico_id: uuid.UUID):
        # 1. Validar Incidente y Asignación
        incident = await self.incident_repo.get_by_id(incident_id)
        if not incident:
            raise NotFoundError("Incidente no encontrado.")
            
        if incident.id_taller != workshop_id:
            raise ForbiddenError("Este incidente no está asignado a tu taller.")

        # 2. Validar Técnico (debe pertenecer al taller)
        tecnico = await self.workshop_repo.get_technician_by_id(tecnico_id)
        if not tecnico or tecnico.id_taller != workshop_id:
            raise ForbiddenError("El técnico no pertenece a tu taller.")

        # 3. Actualizar la asignación
        assignment = await self.assignment_repo.get_by_incident(incident_id)
        if not assignment:
            raise NotFoundError("No se encontró el registro de asignación.")
        
        assignment.id_tecnico = tecnico_id
        assignment.estado_asignacion = "ACEPTADO"

        # 4. Actualizar estado del incidente
        old_status = incident.estado_incidente
        incident.estado_incidente = "EN_CAMINO"
        
        # 5. Registrar Historial
        historial = HistorialIncidente(
            id_incidente=incident_id,
            incidente_estado_anterior=old_status,
            incidente_estado_nuevo="EN_CAMINO",
            historial_actor=f"TALLER_{workshop_id}",
            fecha=None
        )
        incident.historial.append(historial)

        await self.incident_repo.session.commit()
        
        # 6. Notificar al Cliente en Tiempo Real
        try:
            from app.core.notifications import manager
            if incident.vehiculo:
                await manager.notify_user(
                    str(incident.vehiculo.id_usuario),
                    {
                        "type": "INCIDENT_ACCEPTED",
                        "id": str(incident_id),
                        "message": f"Ayuda en camino. El técnico {tecnico.nombre} ha sido asignado.",
                        "tecnico": {
                            "nombre": tecnico.nombre,
                            "telefono": tecnico.telefono
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error al notificar aceptación por WebSocket: {str(e)}")

        return incident
