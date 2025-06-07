from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """
    Middleware для управления сессиями базы данных
    Гарантирует, что все соединения будут закрыты после обработки запроса
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            raise
        finally:
            try:
                from app.db.session import engine
                engine.dispose()  # Закрываем все соединения в пуле
            except Exception as cleanup_error:
                logger.warning(f"Database cleanup error: {cleanup_error}")
