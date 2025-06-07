# app/api/v1/gamesessions/connection_manager.py
from fastapi import WebSocket
from typing import Dict, List, Optional
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}
        self.player_data: Dict[str, Dict[int, dict]] = {}
        self.gm_connections: Dict[str, int] = {}  # Храним GM для каждой сессии

    async def connect(self, session_id: str, user_id: int, websocket: WebSocket, is_gm: bool = False):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = {}
            self.player_data[session_id] = {}
        
        self.active_connections[session_id][user_id] = websocket
        self.player_data[session_id][user_id] = {
            "position": {"x": 0, "y": 0},
            "is_gm": is_gm,
            "connected": True
        }
        
        if is_gm:
            self.gm_connections[session_id] = user_id

    def disconnect(self, session_id: str, user_id: int):
        if session_id in self.active_connections and user_id in self.active_connections[session_id]:
            del self.active_connections[session_id][user_id]
            
        if user_id in self.player_data.get(session_id, {}):
            self.player_data[session_id][user_id]["connected"] = False
            
        if session_id in self.gm_connections and self.gm_connections[session_id] == user_id:
            del self.gm_connections[session_id]
            
        # Очищаем пустые сессии
        if session_id in self.active_connections and not self.active_connections[session_id]:
            del self.active_connections[session_id]
            if session_id in self.player_data:
                del self.player_data[session_id]

    async def send_to_user(self, session_id: str, user_id: int, message: dict):
        """Отправка сообщения конкретному пользователю"""
        if (session_id in self.active_connections and 
            user_id in self.active_connections[session_id]):
            try:
                await self.active_connections[session_id][user_id].send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                # Отключаем пользователя при ошибке
                self.disconnect(session_id, user_id)

    async def broadcast(self, session_id: str, message: dict, exclude_user_id: Optional[int] = None):
        """Рассылка сообщения всем подключенным пользователям в сессии"""
        if session_id not in self.active_connections:
            return
            
        disconnected_users = []
        
        for user_id, websocket in self.active_connections[session_id].items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
                
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to user {user_id}: {e}")
                disconnected_users.append(user_id)
        
        # Очищаем отключенных пользователей
        for user_id in disconnected_users:
            self.disconnect(session_id, user_id)

    def get_gm_for_session(self, session_id: str) -> Optional[int]:
        """Получение GM для сессии"""
        return self.gm_connections.get(session_id)

    def get_session_players(self, session_id: str) -> List[dict]:
        """Получение списка игроков в сессии"""
        if session_id not in self.player_data:
            return []
            
        players = []
        for user_id, data in self.player_data[session_id].items():
            players.append({
                "user_id": user_id,
                "position": data["position"],
                "is_gm": data["is_gm"],
                "connected": data["connected"]
            })
        return players

    def update_player_position(self, session_id: str, user_id: int, position: dict):
        """Обновление позиции игрока"""
        if (session_id in self.player_data and 
            user_id in self.player_data[session_id]):
            self.player_data[session_id][user_id]["position"] = position

    def get_session_state(self, session_id: str) -> dict:
        """Получение полного состояния сессии"""
        return {
            "players": self.get_session_players(session_id),
            "gm_id": self.get_gm_for_session(session_id)
        }

    def is_user_connected(self, session_id: str, user_id: int) -> bool:
        """Проверка подключения пользователя"""
        return (session_id in self.active_connections and 
                user_id in self.active_connections[session_id])

    def get_connected_users_count(self, session_id: str) -> int:
        """Количество подключенных пользователей"""
        return len(self.active_connections.get(session_id, {}))

    def cleanup_session(self, session_id: str):
        """Полная очистка сессии"""
        if session_id in self.active_connections:
            # Закрываем все соединения
            for websocket in self.active_connections[session_id].values():
                try:
                    websocket.close()
                except:
                    pass
            del self.active_connections[session_id]
            
        if session_id in self.player_data:
            del self.player_data[session_id]
            
        if session_id in self.gm_connections:
            del self.gm_connections[session_id]

manager = ConnectionManager()