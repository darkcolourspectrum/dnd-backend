import random
import re
from typing import Tuple
from .schemas import DiceRollResult, RollResultType

def roll_dice(dice_formula: str) -> DiceRollResult:
    """Парсит и выполняет бросок с учетом критических результатов"""
    num_dice, dice_type, modifier = parse_dice_formula(dice_formula)
    rolls = [random.randint(1, dice_type) for _ in range(num_dice)]
    total = sum(rolls) + modifier
    
    # Определяем тип результата
    result_type, message = check_critical(rolls, dice_type)
    
    return DiceRollResult(
        rolls=rolls,
        total=total,
        formula=dice_formula,
        dice_type=f"d{dice_type}",
        result_type=result_type,
        message=message
    )

def check_critical(rolls: list[int], dice_type: int) -> Tuple[RollResultType, str]:
    """Проверяет критические успехи/провалы"""
    if dice_type == 20:  
        if all(r == 20 for r in rolls):
            return (RollResultType.CRITICAL_SUCCESS, "Критический успех!")
        if all(r == 1 for r in rolls):
            return (RollResultType.CRITICAL_FAILURE, "Критический провал!")
    
    if dice_type == 100 and rolls[0] == 100:
        return (RollResultType.CRITICAL_FAILURE, "Провал на 100!")
    
    return (RollResultType.NORMAL, None)

def parse_dice_formula(formula: str) -> Tuple[int, int, int]:
    """Разбирает строку типа '2d6+3' на компоненты"""
    match = re.match(r"^(\d*)d(\d+)([+-]\d+)?$", formula.lower())
    if not match:
        raise ValueError("Invalid dice formula format")
    
    num = int(match.group(1)) if match.group(1) else 1
    dice_type = int(match.group(2))
    modifier = int(match.group(3)) if match.group(3) else 0
    
    valid_dice = [4, 6, 8, 10, 12, 20, 100]
    if dice_type not in valid_dice:
        raise ValueError(f"Invalid dice type. Use: {', '.join(f'd{t}' for t in valid_dice)}")
    
    return num, dice_type, modifier