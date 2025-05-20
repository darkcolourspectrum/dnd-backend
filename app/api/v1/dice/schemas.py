from pydantic import BaseModel, field_validator
from typing import List, Literal, Optional
from enum import Enum

class RollResultType(str, Enum):
    NORMAL = "normal"
    CRITICAL_SUCCESS = "critical_success"
    CRITICAL_FAILURE = "critical_failure"

class DiceRollRequest(BaseModel):
    dice_formula: str  # Например: "2d6+3", "d20", "4d10-2"
    
    @field_validator('dice_formula')
    def validate_dice(cls, v):
        if not any(op in v for op in ['d', '+', '-']):
            raise ValueError("Invalid dice formula")
        return v

class DiceRollResult(BaseModel):
    rolls: List[int]
    total: int
    formula: str
    dice_type: Literal["d4", "d6", "d8", "d10", "d12", "d20", "d100"]
    result_type: RollResultType
    message: Optional[str] = None

    class Config:
        from_attributes = True