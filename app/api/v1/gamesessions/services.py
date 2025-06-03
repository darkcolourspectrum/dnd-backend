from sqlalchemy.orm import Session
from app.api.v1.models import GameSession, SessionPlayer, Character
from app.api.v1.gamesessions.utils import generate_session_id
from .connection_manager import manager
from datetime import datetime
from typing import List, Optional


def create_gamesession(db: Session, creator_id: int, max_players: int = 4) -> GameSession:
    session_id = generate_session_id()
    
    db_session = GameSession(
        id=session_id,
        creator_id=creator_id,
        status='waiting',
        max_players=max_players,
        created_at=datetime.utcnow(),
        current_turn_user_id=None,
        is_current_turn_active=False,
        turn_number=0
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    # Создаем запись игрока (GM)
    player = SessionPlayer(
        session_id=session_id,
        user_id=creator_id,
        is_ready=True,  # GM автоматически готов
        is_gm=True,
        character_id=None
    )
    
    db.add(player)
    db.commit()
    
    return db_session


async def add_player_to_session(
        db: Session,
        session_id: str,
        user_id: int,
        character_id: int
    ) -> SessionPlayer:
    """Добавление игрока в сессию"""
    # Проверяем, что сессия существует и в статусе waiting
    session = db.query(GameSession).filter(
        GameSession.id == session_id,
        GameSession.status == 'waiting'
    ).first()
    
    if not session:
        raise ValueError("Session not found or already started")
    

    character = db.query(Character).filter(
        Character.id == character_id,
        Character.owner_id == user_id
    ).first()
    
    if not character:
        raise ValueError("Character not found or doesn't belong to you")
    
    player = SessionPlayer(
        session_id=session_id,
        user_id=user_id,
        character_id=character_id,  # Добавляем
        is_ready=False
    )

    # Проверяем, что игроков не больше максимума
    current_players = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id
    ).count()
    
    if current_players >= session.max_players:
        raise ValueError("Session is full")
    
    # Проверяем, что игрок еще не в сессии
    existing_player = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id,
        SessionPlayer.user_id == user_id
    ).first()
    
    if existing_player:
        raise ValueError("Player already in session")
    
    # Добавляем игрока (используем SQLAlchemy модель)
    player = SessionPlayer(
        session_id=session_id,
        user_id=user_id,
        is_ready=False
    )
    
    db.add(player)
    db.commit()
    db.refresh(player)
    
    # Уведомляем всех о новом игроке
    await manager.broadcast(session_id, {
        "type": "player_joined",
        "data": {"user_id": user_id}
    })
    return player

def get_gamesession(db: Session, session_id: str) -> Optional[GameSession]:
    """Получение игровой сессии по ID"""
    return db.query(GameSession).filter(GameSession.id == session_id).first()

async def get_gamesessions(db: Session, skip: int = 0, limit: int = 100) -> List[GameSession]:
    return db.query(GameSession)\
        .filter(GameSession.status == 'waiting')\
        .offset(skip)\
        .limit(limit)\
        .all()


async def start_gamesession(db: Session, session_id: str, user_id: int) -> GameSession:
    """Начало игры (перевод статуса в 'active') с инициализацией порядка ходов"""
    session = db.query(GameSession).filter(
        GameSession.id == session_id,
        GameSession.creator_id == user_id,
        GameSession.status == 'waiting'
    ).first()
    
    if not session:
        raise ValueError("Session not found or you are not the creator")
    
    # Получаем список игроков и устанавливаем порядок ходов
    players = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id
    ).all()
    
    if not players:
        raise ValueError("No players in session")
    
    session.players_order = [player.user_id for player in players]
    session.current_turn_user_id = session.players_order[0]
    session.is_current_turn_active = True
    session.status = 'active'
    session.turn_number = 1
    
    db.commit()
    db.refresh(session)
    
    # Уведомляем всех о начале игры
    await manager.broadcast(session_id, {
        "type": "game_started",
        "data": {
            "turn_info": {
                "current_player_id": session.current_turn_user_id,
                "turn_number": session.turn_number,
                "players_order": session.players_order
            }
        }
    })
    
    return session

