from sqlalchemy.orm import Session
from app.api.v1.models import GameMap
from app.api.v1.map.schemas import MapCreate, Wall, Position
from app.api.v1.models import GameSession
from typing import List

def create_map(db: Session, session_id: str, map_data: MapCreate) -> GameMap:
    db_map = GameMap(
        session_id=session_id,
        name=map_data.name,
        background_image=map_data.background_url,
        grid_size=map_data.grid_size,
        width=map_data.width,
        height=map_data.height
    )
    db.add(db_map)
    db.commit()
    db.refresh(db_map)
    return db_map

def get_map(db: Session, map_id: int) -> GameMap:
    return db.query(GameMap).filter(GameMap.id == map_id).first()

def update_walls(db: Session, map_id: int, walls: List[Wall]) -> GameMap:
    db_map = get_map(db, map_id)
    if not db_map:
        return None
    
    walls_data = [
        {"x1": wall.start.x, "y1": wall.start.y, 
         "x2": wall.end.x, "y2": wall.end.y}
        for wall in walls
    ]
    
    db_map.walls = walls_data
    db.commit()
    db.refresh(db_map)
    return db_map

def validate_move(map_data: GameMap, start: Position, end: Position) -> bool:
    if not (0 <= end.x < map_data.width and 0 <= end.y < map_data.height):
        return False
        
    for wall in map_data.walls or []:
        if crosses_wall(start, end, wall):
            return False
    return True

def crosses_wall(start: Position, end: Position, wall: dict) -> bool:
    # Можно запихать алгоритм пересечения
    return False

def is_gm(db: Session, user_id: int, session_id: str) -> bool:
    from app.api.v1.models import SessionPlayer 
    
    player = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id,
        SessionPlayer.user_id == user_id,
        SessionPlayer.is_gm == True
    ).first()
    
    return player is not None

def end_current_turn(db: Session, session: GameSession):
    """Завершает текущий ход"""
    session.is_current_turn_active = False
    db.commit()

def start_new_turn(db: Session, session: GameSession, user_id: int):
    """Начинает новый ход для указанного пользователя"""
    session.current_turn_user_id = user_id
    session.is_current_turn_active = True
    session.turn_number += 1
    db.commit()

def get_current_turn_info(db: Session, session_id: str) -> dict:
    """Возвращает информацию о текущем ходе"""
    session = db.query(GameSession).filter(
        GameSession.id == session_id
    ).first()
    
    if not session:
        return None
    
    return {
        "current_player_id": session.current_turn_user_id,
        "turn_number": session.turn_number,
        "is_active": session.is_current_turn_active
    }