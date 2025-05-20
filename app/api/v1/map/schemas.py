from pydantic import BaseModel
from typing import List, Optional, Dict

class Position(BaseModel):
    x: int
    y: int

class Wall(BaseModel):
    start: Position
    end: Position

class MapCreate(BaseModel):
    name: str
    background_url: str
    grid_size: int = 50
    width: int
    height: int

class MapResponse(MapCreate):
    id: int
    session_id: str
    walls: List[Wall] = []
    obstacles: List[Dict] = []

class UpdateWallsRequest(BaseModel):
    walls: List[Wall]

class MoveCharacterRequest(BaseModel):
    character_id: int
    target_position: Position

class TurnRequest(BaseModel):
    session_id: str

class TurnInfo(BaseModel):
    current_player_id: int
    turn_number: int
    is_active: bool
    players_order: List[int]