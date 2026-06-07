import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class IncidentConnectionManager:
    """Administra conexiones WebSocket separadas por sala de incidente (incident_id)."""
    def __init__(self):
        # Mapea: id_incidente (string) -> set de WebSocket
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, incident_id: str, websocket: WebSocket):
        await websocket.accept()
        if incident_id not in self.active_connections:
            self.active_connections[incident_id] = set()
        self.active_connections[incident_id].add(websocket)
        logger.info(f"WebSocket conectado al incidente {incident_id}. Conexiones activas: {len(self.active_connections[incident_id])}")

    def disconnect(self, incident_id: str, websocket: WebSocket):
        if incident_id in self.active_connections:
            self.active_connections[incident_id].discard(websocket)
            logger.info(f"WebSocket desconectado del incidente {incident_id}.")
            if not self.active_connections[incident_id]:
                del self.active_connections[incident_id]
                logger.info(f"Sala de incidente {incident_id} removida por no tener conexiones activas.")

    async def broadcast_to_incident(self, incident_id: str, message: dict):
        """Envía un mensaje JSON a todas las conexiones registradas para un incidente específico."""
        if incident_id in self.active_connections:
            # Iterar sobre una copia del set para evitar concurrencias
            sockets = list(self.active_connections[incident_id])
            for websocket in sockets:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Error al enviar por WebSocket en incidente {incident_id}: {e}. Desconectando...")
                    self.disconnect(incident_id, websocket)

manager = IncidentConnectionManager()
