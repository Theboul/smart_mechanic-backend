import uuid
import logging
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.emergencies.domain.models import HistorialIncidente
from app.core.exceptions import ForbiddenError, NotFoundError

logger = logging.getLogger(__name__)

class UpdateIncidentStatusUseCase:
    """
    Caso de Uso (CU): Actualizar estado de emergencia desde el taller.
    Permite al taller gestionar el flujo de atención.
    """
    
    def __init__(self, incident_repo: IncidentRepository):
        self.incident_repo = incident_repo

    async def execute(self, id_taller: uuid.UUID, id_incidente: uuid.UUID, nuevo_estado: str, actor_nombre: str):
        # 1. Obtener incidente
        incidente = await self.incident_repo.get_by_id(id_incidente)
        if not incidente:
            raise NotFoundError("Incidente no encontrado.")
            
        # 2. Validar Multi-Tenancy (El incidente debe estar asignado a este taller)
        if incidente.id_taller != id_taller:
            raise ForbiddenError("No tienes permiso para gestionar este incidente.")

        # 3. Registrar cambio en historial
        estado_anterior = incidente.estado_incidente
        incidente.estado_incidente = nuevo_estado
        
        historial = HistorialIncidente(
            id_incidente=id_incidente,
            incidente_estado_anterior=estado_anterior,
            incidente_estado_nuevo=nuevo_estado,
            historial_actor=actor_nombre,
            fecha=None
        )
        incidente.historial.append(historial)
        
        await self.incident_repo.session.commit()
        await self.incident_repo.session.refresh(incidente)
        
        logger.info(f"Incidente {id_incidente} actualizado a {nuevo_estado} por {actor_nombre}")
        return incidente
