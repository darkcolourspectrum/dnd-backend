from pydantic import BaseModel

class NPCBase(BaseModel):
    name: str
    image_url: str
    description: str | None = None

class NPCCreate(NPCBase):
    session_id: str

class NPC(NPCBase):
    id: int
    session_id: str
    
    class Config:
        from_attributes = True