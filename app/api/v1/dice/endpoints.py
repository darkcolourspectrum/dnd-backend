from fastapi import APIRouter, HTTPException, Depends
from .schemas import DiceRollRequest, DiceRollResult  # Явно импортируем схемы
from . import services
from app.api.v1.auth.dependencies import get_current_active_user
from app.api.v1.models import User

router = APIRouter(
    prefix="/dice",
    tags=["dice"]
)

@router.post("/roll", response_model=DiceRollResult)
async def roll_dice_endpoint(
    request: DiceRollRequest,
    current_user: User = Depends(get_current_active_user)  # Единообразно используем current_user
):
    """Бросок костей в D&D стиле"""
    try:
        return services.roll_dice(request.dice_formula)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )