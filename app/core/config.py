from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://postgres:kirill1905@localhost:5432/dnd_database"

    class Config:
        env_file = ".env"

settings = Settings()