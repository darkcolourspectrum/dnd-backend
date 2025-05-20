# app/api/v1/gamesessions/connection_manager.py
from fastapi import WebSocket
from typing import Dict, List, Optional
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        self.player_data: Dict[str, Dict[int, dict]] = {}

    async def connect(self, session_id: str, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
            self.player_data[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
        self.player_data[session_id][user_id] = {"position": {"x": 0, "y": 0}}

    def disconnect(self, session_id: str, user_id: int):
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            del self.active_connections[session_id][user_id]
            if user_id in self.player_data.get(session_id, {}):
                del self.player_data[session_id][user_id]

    async def broadcast(self, session_id: str, message: dict, exclude_user_id: Optional[int] = None):
        if session_id in self.active_connections:
            for user_id, connection in self.active_connections[session_id].items():
                if user_id != exclude_user_id:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        print(f"Error sending message to user {user_id}: {e}")
                        self.disconnect(session_id, user_id)

    async def send_personal_message(self, user_id: int, message: dict):
        for session in self.active_connections.values():
            if user_id in session:
                await session[user_id].send_json(message)
                break

    def update_player_position(self, session_id: str, user_id: int, position: dict):
        if session_id in self.player_data and user_id in self.player_data[session_id]:
            self.player_data[session_id][user_id]["position"] = position

    def get_session_state(self, session_id: str) -> dict:
        return {
            "players": self.player_data.get(session_id, {}),
            "turn": None  # Будем заполнять позже
        }

manager = ConnectionManager()