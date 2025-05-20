from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.v1.npc import schemas, services
from app.db.session import get_db
from app.api.v1.gamesessions.dependencies import validate_session_ownership
from app.api.v1.models import GameSession

router = APIRouter(
    prefix="/npcs",
    tags=["npcs"]
)

@router.post("/", response_model=schemas.NPC)
async def create_npc(
    npc_data: schemas.NPCCreate,
    db: Session = Depends(get_db),
    session: GameSession = Depends(validate_session_ownership)  # Только GM может создавать NPC
):
    return services.create_npc(db, {
        **npc_data.dict(),
        "session_id": session.id
    })

@router.get("/{session_id}", response_model=list[schemas.NPC])
async def get_npcs(
    session_id: str,
    db: Session = Depends(get_db)
):
    return services.get_session_npcs(db, session_id)