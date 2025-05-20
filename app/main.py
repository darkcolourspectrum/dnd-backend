from fastapi import FastAPI
from .api.v1.auth.endpoints import router as auth_router
from .api.v1.gamesessions.endpoints import router as sessions_router
from .api.v1.characters.endpoints import router as character_router
from .api.v1.npc.endpoints import router as npc_router
from .api.v1.dice.endpoints import router as dice_router
from .api.v1.map.endpoints import router as map_router
import sys

if "--reload" in sys.argv:
    import importlib
    importlib.invalidate_caches()

app = FastAPI(
    title="DnD Multiplayer API",
    description="API для авторизации и игровых сессий",
    version="1.3.0"

    
)

app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(character_router)
app.include_router(npc_router)
app.include_router(dice_router)
app.include_router(map_router)

@app.get("/")
def read_root():
    return {"message": "DnD Multiplayer API v1 with auth"}