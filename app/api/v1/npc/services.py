from sqlalchemy.orm import Session
from app.api.v1.models import NPC

def create_npc(db: Session, npc_data: dict):
    db_npc = NPC(**npc_data)
    db.add(db_npc)
    db.commit()
    db.refresh(db_npc)
    return db_npc

def get_session_npcs(db: Session, session_id: str):
    return db.query(NPC).filter(NPC.session_id == session_id).all()