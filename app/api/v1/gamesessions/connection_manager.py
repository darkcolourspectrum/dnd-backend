# app/api/v1/gamesessions/connection_manager.py
from fastapi import WebSocket
from typing import Dict, List, Optional
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        self.player_data: Dict[str, Dict[int, dict]] = {}
        self.gm_connections: Dict[str, int] = {}  # Храним GM для каждой сессии

    async def connect(self, session_id: str, user_id: int, websocket: WebSocket, is_gm: bool):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
            self.player_data[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
        self.player_data[session_id][user_id] = {
            "position": {"x": 0, "y": 0},
            "is_gm": is_gm
        }
        
        if is_gm:
            self.gm_connections[session_id] = user_id

    def disconnect(self, session_id: str, user_id: int):
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            del self.active_connections[session_id][user_id]
            if user_id in self.player_data.get(session_id, {}):
                del self.player_data[session_id][user_id]
            
            if session_id in self.gm_connections and self.gm_connections[session_id] == user_id:
                del self.gm_connections[session_id]

    def get_gm_for_session(self, session_id: str) -> Optional[int]:
        return self.gm_connections.get(session_id)

manager = ConnectionManager()