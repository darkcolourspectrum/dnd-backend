from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Race(str, Enum):
    human = "human"
    elf = "elf"
    dwarf = "dwarf"
    orc = "orc"

class Class(str, Enum):
    warrior = "warrior"
    mage = "mage"
    rogue = "rogue"
    cleric = "cleric"

class CharacterBase(BaseModel):
    name: str
    race: Race
    class_: Class  # class - зарезервированное слово, используем class_

class CharacterCreate(CharacterBase):
    strength: int = 1
    dexterity: int = 1
    intelligence: int = 1
    # Другие базовые параметры

class Character(CharacterBase):
    id: int
    owner_id: int
    strength: int
    dexterity: int
    intelligence: int
    level: int = 1
    experience: int = 0
    
    class Config:
        orm_mode = True

class CharacterUpdate(BaseModel):
    name: Optional[str] = None