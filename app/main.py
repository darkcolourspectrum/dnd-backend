from fastapi import FastAPI
from .api.v1.auth.endpoints import router as auth_router
import sys

if "--reload" in sys.argv:
    import importlib
    importlib.invalidate_caches()

app = FastAPI(
    title="DnD Multiplayer API",
    description="API для авторизации и игровых сессий",
    version="1.0.0"
)

app.include_router(auth_router)

# Тестовый эндпоинт для проверки работы
@app.get("/")
def read_root():
    return {"message": "DnD Multiplayer API v1 with auth"}