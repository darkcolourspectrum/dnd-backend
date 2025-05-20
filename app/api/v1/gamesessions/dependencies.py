from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Annotated
from app.api.v1.auth.dependencies import get_current_user
from app.db.session import get_db
from app.api.v1.gamesessions.services import get_gamesession
from app.api.v1.models import GameSession, SessionPlayer
from app.api.v1.models import User

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Зависимость для получения активного пользователя"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def validate_game_session_access(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> GameSession:
    """Зависимость для проверки доступа к игровой сессии"""
    try:
        session = get_gamesession(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found"
            )

        # Проверяем, является ли пользователь участником сессии
        player = db.query(SessionPlayer).filter(
            SessionPlayer.session_id == session_id,
            SessionPlayer.user_id == current_user.id
        ).first()

        if not player:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this session"
            )

        return session

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e


async def validate_session_ownership(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> GameSession:
    """Зависимость для проверки, что пользователь - создатель сессии"""
    try:
        session = get_gamesession(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found"
            )

        if session.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only session creator can perform this action"
            )

        return session

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) from e