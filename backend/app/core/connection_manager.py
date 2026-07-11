from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # queue_id -> list of active websocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, queue_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(queue_id, []).append(websocket)

    def disconnect(self, queue_id: str, websocket: WebSocket):
        if queue_id in self.active_connections:
            self.active_connections[queue_id].remove(websocket)
            if not self.active_connections[queue_id]:
                del self.active_connections[queue_id]

    async def broadcast(self, queue_id: str, message: dict):
        for connection in self.active_connections.get(queue_id, []):
            await connection.send_json(message)

    async def send_personal(self, websocket: WebSocket, message: dict):
        await websocket.send_json(message)


manager = ConnectionManager()
