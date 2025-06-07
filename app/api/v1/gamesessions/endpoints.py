# app/api/v1/gamesessions/endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect, Body
from sqlalchemy.orm import Session
from app.db.session import get_db
from typing import Optional
from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.gamesessions import schemas, services
from app.api.v1.gamesessions.dependencies import (
    get_current_active_user,
    get_game_session_info,
    validate_game_session_access,
    validate_session_ownership
)
from app.api.v1.models import User
from .connection_manager import manager
from app.core.security import decode_access_token
from app.api.v1.models import GameSession, SessionPlayer
from fastapi.websockets import WebSocketDisconnect
from typing import List 

router = APIRouter(
    prefix="/gamesessions",
    tags=["game_sessions"]
)

@router.post("/", response_model=schemas.GameSession)
def create_game_session(
    session_data: schemas.GameSessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        session = services.create_gamesession(
            db, 
            current_user.id,
            max_players=session_data.max_players
        )
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{session_id}/gm-redirect", response_model=schemas.GameSession)
async def gm_redirect_to_session(
    session: GameSession = Depends(validate_session_ownership),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Специальный endpoint для перенаправления GM в сессию.
    Проверяет права GM и возвращает полные данные сессии.
    """
    # Дополнительная проверка, что пользователь действительно GM
    player = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session.id,
        SessionPlayer.user_id == current_user.id,
        SessionPlayer.is_gm == True
    ).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the GM of this session"
        )
    
    # Обновляем статус готовности GM
    player.is_ready = True
    db.commit()
    
    return session

@router.post("/{session_id}/join", response_model=schemas.SessionPlayer)
async def join_game_session(
    session_id: str,
    character_id: Optional[int] = Body(None, embed=True),  # Делаем опциональным
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Присоединение к игровой сессии
    Персонаж может быть выбран позже в лобби
    """
    try:
        return await services.add_player_to_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            character_id=character_id  # Может быть None
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{session_id}", response_model=schemas.GameSession)
def get_game_session(
    session: GameSession = Depends(get_game_session_info)  # Изменено! Теперь разрешает просмотр всем
):
    """
    Получение информации о сессии
    Доступно всем авторизованным пользователям для просмотра
    """
    return session

@router.post("/{session_id}/start", response_model=schemas.GameSession)
async def start_game_session(
    db: Session = Depends(get_db),
    session: GameSession = Depends(validate_session_ownership)
):
    try:
        # ИСПРАВЛЕНИЕ: добавлен await
        return await services.start_gamesession(
            db=db,
            session_id=session.id,
            user_id=session.creator_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
@router.get("/{session_id}/players", response_model=List[schemas.SessionPlayer])
def get_session_players(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Изменено! Разрешаем всем авторизованным
):
    """
    Получение списка игроков в сессии
    Доступно всем авторизованным пользователям
    """
    # Проверяем, что сессия существует
    session = db.query(GameSession).filter(GameSession.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    players = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id
    ).all()
    
    return players

@router.post("/{session_id}/ready", response_model=schemas.SessionPlayer)
def toggle_ready_status(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Изменение статуса готовности
    Требует членства в сессии
    """
    player = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id,
        SessionPlayer.user_id == current_user.id
    ).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found in this session"
        )
    
    player.is_ready = not player.is_ready
    db.commit()
    db.refresh(player)
    
    return player

@router.delete("/{session_id}", response_model=schemas.MessageResponse)
async def delete_game_session(
    db: Session = Depends(get_db),
    session: GameSession = Depends(validate_session_ownership)
):
    """
    Удаление игровой сессии (только для создателя сессии)
    Удаляет все связанные данные: игроков, NPC, карты
    """
    try:
        session_id = session.id
        
        # Отключаем всех игроков через WebSocket
        await manager.broadcast(
            session_id,
            {
                "type": "session_deleted",
                "data": {"message": "Сессия была удалена создателем"}
            }
        )
        
        # Удаляем все связанные записи (cascade должен работать, но делаем явно для надежности)
        
        # 1. Удаляем игроков сессии
        db.query(SessionPlayer).filter(SessionPlayer.session_id == session_id).delete()
        
        # 2. Удаляем NPC
        from app.api.v1.models import NPC
        db.query(NPC).filter(NPC.session_id == session_id).delete()
        
        # 3. Удаляем карты
        from app.api.v1.models import GameMap
        db.query(GameMap).filter(GameMap.session_id == session_id).delete()
        
        # 4. Удаляем саму сессию
        db.delete(session)
        
        # Коммитим все изменения
        db.commit()
        
        # Очищаем соединения в менеджере
        manager.cleanup_session(session_id)
        
        return {"message": f"Сессия {session_id} успешно удалена"}
        
    except Exception as e:
        db.rollback()
        print(f"Error deleting session {session.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении сессии: {str(e)}"
        )

@router.get("/my-sessions", response_model=List[schemas.GameSession])
def get_my_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Получение всех сессий, созданных текущим пользователем
    """
    try:
        sessions = db.query(GameSession).filter(
            GameSession.creator_id == current_user.id
        ).order_by(GameSession.created_at.desc()).all()
        
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при получении сессий: {str(e)}"
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
    
    # Проверка что пользователь участник сессии
    player = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id,
        SessionPlayer.user_id == user.id
    ).first()
    
    if not player:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Подключение к менеджеру
    await manager.connect(session_id, user.id, websocket, player.is_gm)
    
    try:
        # Отправляем текущее состояние сессии новому подключению
        initial_state = {
            "type": "initial_state",
            "data": {
                "session_id": session_id,
                "user_id": user.id,
                "is_gm": player.is_gm,
                "players": manager.get_session_players(session_id)
            }
        }
        await websocket.send_json(initial_state)
        
        # Уведомляем других игроков о новом подключении
        await manager.broadcast(
            session_id,
            {
                "type": "player_connected", 
                "data": {
                    "user_id": user.id,
                    "is_gm": player.is_gm
                }
            },
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
            elif data["type"] == "gm_command" and player.is_gm:
                await handle_gm_command(session_id, user.id, data["data"], db)
            elif data["type"] == "chat_message":
                await handle_chat_message(session_id, user.id, data["data"], db)
            
    except WebSocketDisconnect:
        manager.disconnect(session_id, user.id)
        await manager.broadcast(
            session_id,
            {
                "type": "player_disconnected", 
                "data": {"user_id": user.id}
            }
        )

async def handle_gm_command(session_id: str, user_id: int, command_data: dict, db: Session):
    """Обработка команд GM"""
    await manager.broadcast(
        session_id,
        {
            "type": "gm_command",
            "data": command_data
        }
    )

async def handle_chat_message(session_id: str, user_id: int, message_data: dict, db: Session):
    """Обработка сообщений чата"""
    await manager.broadcast(
        session_id,
        {
            "type": "chat_message",
            "data": {
                "user_id": user_id,
                "message": message_data.get("message", ""),
                "timestamp": message_data.get("timestamp")
            }
        }
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
    
    # Обновляем позицию в менеджере соединений
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
    if next_player_id:
        session.current_turn_user_id = next_player_id
        session.is_current_turn_active = True
        session.turn_number += 1
        db.commit()
    
    await manager.broadcast(
        session_id,
        {
            "type": "turn_ended",
            "data": {
                "current_player_id": user_id,
                "next_player_id": next_player_id,
                "turn_number": session.turn_number
            }
        }
    )

async def handle_dice_roll(session_id: str, user_id: int, roll_data: dict, db: Session):
    try:
        from app.api.v1.dice.services import roll_dice
        result = roll_dice(roll_data["dice_formula"])
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
    except ValueError as e:
        # Отправляем ошибку только отправителю
        await manager.send_to_user(
            session_id,
            user_id,
            {
                "type": "dice_error",
                "data": {"error": str(e)}
            }
        )

def get_next_player_id(session: GameSession) -> Optional[int]:
    """Определяет ID следующего игрока"""
    if not session.players_order:
        return None
    
    try:
        current_index = session.players_order.index(session.current_turn_user_id)
        next_index = (current_index + 1) % len(session.players_order)
        return session.players_order[next_index]
    except (ValueError, IndexError):
        return None

