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

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class DatabaseCleanupMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request error: {e}")
            raise
        finally:
            try:
                from app.db.session import engine
                if hasattr(engine.pool, 'invalidate'):
                    pass  
            except Exception:
                pass

app.add_middleware(DatabaseCleanupMiddleware)

app.include_router(auth_router)
app.include_router(sessions_router)
app.include_router(character_router)
app.include_router(npc_router)
app.include_router(dice_router)
app.include_router(map_router)

@app.get("/")
def read_root():
    return {"message": "DnD Multiplayer API v1 with auth"}

@app.get("/health/db")
def check_database():
    try:
        from app.db.session import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return {
            "status": "healthy",
            "pool_size": engine.pool.size(),
            "pool_checked_in": engine.pool.checkedin(),
            "pool_checked_out": engine.pool.checkedout(),
            "pool_overflow": engine.pool.overflow(),
            "pool_invalid": engine.pool.invalid()
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}