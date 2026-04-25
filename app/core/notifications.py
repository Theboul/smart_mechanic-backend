from fastapi import WebSocket
from typing import Dict, List, Optional
import json

class ConnectionManager:
    def __init__(self):
        # Mapeo de user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Mapeo de workshop_id -> List[WebSocket] (para cuando haya varios admins por taller)
        self.workshop_channels: Dict[str, List[WebSocket]] = {}
        # Lista de conexiones de SuperAdmins
        self.admin_connections: List[WebSocket] = []

    async def connect(self, user_id: str, is_admin: bool, websocket: WebSocket, workshop_id: Optional[str] = None):
        await websocket.accept()
        if is_admin:
            self.admin_connections.append(websocket)
        else:
            self.active_connections[user_id] = websocket
            if workshop_id:
                if workshop_id not in self.workshop_channels:
                    self.workshop_channels[workshop_id] = []
                self.workshop_channels[workshop_id].append(websocket)

    def disconnect(self, user_id: str, is_admin: bool, websocket: WebSocket, workshop_id: Optional[str] = None):
        if is_admin:
            if websocket in self.admin_connections:
                self.admin_connections.remove(websocket)
        else:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            if workshop_id and workshop_id in self.workshop_channels:
                if websocket in self.workshop_channels[workshop_id]:
                    self.workshop_channels[workshop_id].remove(websocket)

    async def notify_workshop(self, workshop_id: str, message: dict):
        """Envía un mensaje a todos los conectados de un taller específico"""
        if workshop_id in self.workshop_channels:
            for connection in self.workshop_channels[workshop_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    self.workshop_channels[workshop_id].remove(connection)

    async def notify_user(self, user_id: str, message: dict):
        """Envía un mensaje a un usuario específico"""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(json.dumps(message))
            except Exception:
                del self.active_connections[user_id]

    async def notify_admins(self, message: dict):
        """Envía un mensaje a todos los SuperAdmins"""
        for connection in self.admin_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                self.admin_connections.remove(connection)

# Instancia única para toda la aplicación
manager = ConnectionManager()
