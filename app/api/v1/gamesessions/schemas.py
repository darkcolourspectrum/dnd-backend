from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal, Optional

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
    current_turn_user_id: Optional[int] = None
    is_current_turn_active: bool = False
    turn_number: int = 0
    
    class Config:
        from_attributes = True

class SessionPlayerBase(BaseModel):
    is_ready: bool = False

class SessionPlayerCreate(SessionPlayerBase):
    pass

class SessionPlayer(SessionPlayerBase):
    id: int
    session_id: str
    user_id: int
    character_id: int | None 
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