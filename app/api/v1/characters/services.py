from sqlalchemy.orm import Session
from  app.api.v1.characters import schemas
from app.api.v1.models import Character
from typing import List

def create_character(
    db: Session, 
    character_data: schemas.CharacterCreate, 
    owner_id: int
) -> Character:
    # Проверка суммы характеристик (15 очков)
    total_points = (
        character_data.strength + 
        character_data.dexterity + 
        character_data.intelligence
    )
    if total_points > 15:
        raise ValueError("Total points cannot exceed 15")
    
    db_character = Character(
        owner_id=owner_id,
        **character_data.dict()
    )
    
    db.add(db_character)
    db.commit()
    db.refresh(db_character)
    return db_character

def get_characters(db: Session, owner_id: int) -> List[Character]:
    return db.query(Character).filter(Character.owner_id == owner_id).all()

def get_character(db: Session, character_id: int, owner_id: int) -> Character:
    return db.query(Character).filter(
        Character.id == character_id,
        Character.owner_id == owner_id
    ).first()