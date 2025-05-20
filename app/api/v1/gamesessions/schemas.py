from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal

class GameSessionBase(BaseModel):
    max_players: int = 4

class GameSessionCreate(GameSessionBase):
    pass

class GameSession(GameSessionBase):
    id: str
    creator_id: int
    status: str  # 'waiting', 'active', 'finished'
    created_at: datetime
    players: List['SessionPlayer']
    
    class Config:
        orm_mode = True

class SessionPlayerBase(BaseModel):
    is_ready: bool = False

class SessionPlayerCreate(SessionPlayerBase):
    pass

class SessionPlayer(SessionPlayerBase):
    id: int
    session_id: str
    user_id: int
    character_id: int
    is_gm: bool
    
    class Config:
        from_attributes = True

class WSMessage(BaseModel):
    type: Literal[
        "player_joined",
        "player_left", 
        "character_selected",
        "game_started"
    ]
    data: dict