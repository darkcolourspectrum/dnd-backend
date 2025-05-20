from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.session import get_db
from typing import Optional
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.gamesessions import schemas, services
from app.api.v1.gamesessions.dependencies import (
    get_current_active_user,
    validate_game_session_access,
    validate_session_ownership
)
from app.api.v1.models import User
from .connection_manager import manager
from app.core.security import decode_access_token
from app.api.v1.models import GameSession
from fastapi.websockets import WebSocketDisconnect

router = APIRouter(
    prefix="/gamesessions",
    tags=["game_sessions"]
)

@router.post("/", response_model=schemas.GameSession)
async def create_game_session(
    session_data: schemas.GameSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание новой игровой сессии"""
    return services.create_gamesession(
        db=db,
        creator_id=current_user.id,
        max_players=session_data.max_players
    )

@router.get("/{session_id}", response_model=schemas.GameSession)
async def get_game_session(
    session: schemas.GameSession = Depends(validate_game_session_access)
):
    """Получение информации о сессии"""
    return session

@router.post("/{session_id}/join", response_model=schemas.SessionPlayer)
async def join_game_session(
    session_id: str,
    character_id: int,  # Добавляем параметр
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Присоединение к существующей сессии с указанием персонажа"""
    try:
        return services.add_player_to_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            character_id=character_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/{session_id}/start", response_model=schemas.GameSession)
async def start_game_session(
    db: Session = Depends(get_db),
    session: schemas.GameSession = Depends(validate_session_ownership)
):
    """Начало игры (перевод статуса в 'active')"""
    try:
        return services.start_gamesession(
            db=db,
            session_id=session.id,
            user_id=session.creator_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.websocket("/{session_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    # Проверка токена
    user = await authenticate_websocket_user(db, token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Подключение к менеджеру
    await manager.connect(session_id, user.id, websocket)
    
    try:
        # Отправляем текущее состояние сессии новому подключению
        initial_state = {
            "type": "initial_state",
            "data": manager.get_session_state(session_id)
        }
        await websocket.send_json(initial_state)
        
        # Уведомляем других игроков о новом подключении
        await manager.broadcast(
            session_id,
            {"type": "player_connected", "data": {"user_id": user.id}},
            exclude_user_id=user.id
        )
        
        while True:
            data = await websocket.receive_json()
            
            # Обработка разных типов сообщений
            if data["type"] == "move":
                await handle_move(session_id, user.id, data["data"], db)
            elif data["type"] == "end_turn":
                await handle_end_turn(session_id, user.id, db)
            elif data["type"] == "roll_dice":
                await handle_dice_roll(session_id, user.id, data["data"], db)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, user.id)
        await manager.broadcast(
            session_id,
            {"type": "player_disconnected", "data": {"user_id": user.id}}
        )

async def authenticate_websocket_user(db: Session, token: str) -> Optional[User]:
    payload = decode_access_token(token)
    if not payload:
        return None
    
    email = payload.get("sub")
    if not email:
        return None
    
    return db.query(User).filter(User.email == email).first()

async def handle_move(session_id: str, user_id: int, move_data: dict, db: Session):
    # Проверяем, может ли игрок ходить
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session or session.current_turn_user_id != user_id or not session.is_current_turn_active:
        return
    
    # Обновляем позицию
    manager.update_player_position(session_id, user_id, move_data["position"])
    
    # Рассылаем обновление
    await manager.broadcast(
        session_id,
        {
            "type": "player_moved",
            "data": {
                "user_id": user_id,
                "position": move_data["position"]
            }
        }
    )

async def handle_end_turn(session_id: str, user_id: int, db: Session):
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session or session.current_turn_user_id != user_id:
        return
    
    # Логика завершения хода
    session.is_current_turn_active = False
    db.commit()
    
    # Определяем следующего игрока
    next_player_id = get_next_player_id(session)
    
    await manager.broadcast(
        session_id,
        {
            "type": "turn_ended",
            "data": {
                "current_player_id": user_id,
                "next_player_id": next_player_id
            }
        }
    )

async def handle_dice_roll(session_id: str, user_id: int, roll_data: dict, db: Session):
    try:
        result = services.roll_dice(roll_data["dice_formula"])
        await manager.broadcast(
            session_id,
            {
                "type": "dice_rolled",
                "data": {
                    "user_id": user_id,
                    "result": result.dict(),
                    "formula": roll_data["dice_formula"]
                }
            }
        )
    except ValueError:
        pass

def get_next_player_id(session: GameSession) -> int:
    """Определяет ID следующего игрока"""
    if not session.players_order:
        return None
    
    current_index = session.players_order.index(session.current_turn_user_id)
    next_index = (current_index + 1) % len(session.players_order)
    return session.players_order[next_index]