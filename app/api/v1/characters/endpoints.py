from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.api.v1.auth.dependencies import get_current_user  # Используем get_current_user
from app.api.v1.gamesessions.schemas import SessionPlayer
from app.api.v1.models import User
from app.api.v1.characters import schemas, services

router = APIRouter(
    prefix="/characters",
    tags=["characters"]
)

@router.post("/", response_model=schemas.Character)
async def create_new_character(
    character_data: schemas.CharacterCreate,
    current_user: User = Depends(get_current_user),  # Исправлено
    db: Session = Depends(get_db)
):
    try:
        return services.create_character(
            db=db,
            character_data=character_data,
            owner_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[schemas.Character])
async def get_user_characters(
    current_user: User = Depends(get_current_user),  # Исправлено
    db: Session = Depends(get_db)
):
    return services.get_characters(db, current_user.id)

@router.get("/{character_id}", response_model=schemas.Character)
async def get_character_details(
    character_id: int,
    current_user: User = Depends(get_current_user),  # Исправлено
    db: Session = Depends(get_db)
):
    character = services.get_character(db, character_id, current_user.id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    return character

@router.post("/{character_id}/select", response_model=SessionPlayer)
async def select_character_for_session(
    character_id: int,
    session_id: str,
    current_user: User = Depends(get_current_user),  # Исправлено
    db: Session = Depends(get_db)
):
    """
    Выбор персонажа для игровой сессии
    """
    character = services.get_character(db, character_id, current_user.id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    
    player = db.query(SessionPlayer).filter(
        SessionPlayer.session_id == session_id,
        SessionPlayer.user_id == current_user.id
    ).first()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not in session"
        )
    
    if player.is_gm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GM cannot select character"
        )
    
    player.character_id = character_id
    db.commit()
    db.refresh(player)
    
    return player