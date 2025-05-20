from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth.dependencies import get_current_active_user
from app.api.v1.map.schemas import (
    MapCreate, 
    MapResponse, 
    UpdateWallsRequest, 
    MoveCharacterRequest,
    TurnRequest,
    TurnInfo
)
from app.api.v1.map.services import (
    create_map,
    get_map,
    update_walls,
    validate_move,
    is_gm,
    end_current_turn,
    start_new_turn,
    get_current_turn_info
)
from app.api.v1.models import User, GameSession, SessionPlayer

router = APIRouter(prefix="/game/map", tags=["game_map"])

@router.post("/", response_model=MapResponse)
def create_game_map(
    map_data: MapCreate,
    session_id: str,  
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создание новой карты (только для GM)"""
    if not is_gm(db, current_user.id, session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Game Master can create maps"
        )
    
    return create_map(db, session_id, map_data)

@router.get("/{map_id}", response_model=MapResponse)
def get_game_map(
    map_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о карте"""
    map_data = get_map(db, map_id)
    if not map_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found"
        )
    
    # Проверка что пользователь участник сессии
    player = db.query(SessionPlayer).filter(
        SessionPlayer.user_id == current_user.id,
        SessionPlayer.session_id == map_data.session_id
    ).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this session"
        )
    
    return map_data

@router.post("/{map_id}/walls", response_model=MapResponse)
def update_map_walls(
    map_id: int,
    walls_data: UpdateWallsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновление стен на карте (только для GM)"""
    map_data = get_map(db, map_id)
    if not map_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found"
        )
    
    if not is_gm(db, current_user.id, map_data.session_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Game Master can edit walls"
        )
    
    return update_walls(db, map_id, walls_data.walls)

@router.post("/move", response_model=dict)
def move_character(
    move_data: MoveCharacterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Перемещение персонажа (только во время своего хода)"""
    # Проверка активного хода
    session = db.query(GameSession).filter(
        GameSession.id == move_data.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    
    if session.current_turn_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not your turn"
        )
    
    if not session.is_current_turn_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active turn"
        )
    
    # Проверка возможности хода
    if not validate_move(db, move_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid move"
        )
    
    return {
        "status": "success",
        "new_position": move_data.target_position,
        "remaining_actions": 2  
    }

@router.post("/end-turn", response_model=dict)
def end_turn(
    turn_data: TurnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Завершение текущего хода"""
    session = db.query(GameSession).filter(
        GameSession.id == turn_data.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session.current_turn_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not your turn"
        )
    
    end_current_turn(db, session)
    
    return {
        "status": "success",
        "message": "Turn ended",
        "next_player_id": get_next_player_id(session)
    }

@router.post("/start-turn", response_model=dict)
def start_turn(
    turn_data: TurnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Начало нового хода"""
    session = db.query(GameSession).filter(
        GameSession.id == turn_data.session_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Проверка что это действительно следующий игрок
    next_player_id = get_next_player_id(session)
    if next_player_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not your turn to start"
        )
    
    start_new_turn(db, session, current_user.id)
    
    return {
        "status": "success",
        "message": "Turn started",
        "turn_info": get_current_turn_info(db, turn_data.session_id)
    }

@router.get("/turn-info/{session_id}", response_model=TurnInfo)
def get_turn_info(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получение информации о текущем ходе"""
    info = get_current_turn_info(db, session_id)
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Проверка что пользователь участник сессии
    player = db.query(SessionPlayer).filter(
        SessionPlayer.user_id == current_user.id,
        SessionPlayer.session_id == session_id
    ).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this session"
        )
    
    return info

# Вспомогательная функция
def get_next_player_id(session: GameSession) -> int:
    """Определяет ID следующего игрока"""
    if not session.players_order:
        return None
    
    current_index = session.players_order.index(session.current_turn_user_id)
    next_index = (current_index + 1) % len(session.players_order)
    return session.players_order[next_index]