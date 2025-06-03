from fastapi import FastAPI
from .api.v1.auth.endpoints import router as auth_router
from .api.v1.gamesessions.endpoints import router as sessions_router
from .api.v1.characters.endpoints import router as character_router
from .api.v1.npc.endpoints import router as npc_router
from .api.v1.dice.endpoints import router as dice_router
from .api.v1.map.endpoints import router as map_router
from fastapi.middleware.cors import CORSMiddleware
import sys

if "--reload" in sys.argv:
    import importlib
    importlib.invalidate_caches()

app = FastAPI(
    title="DnD Multiplayer API",
    description="API для авторизации и игровых сессий",
    version="1.3.0"
)

origins = [
    "http://localhost:3000",  
    "http://127.0.0.1:3000",  
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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