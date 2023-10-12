import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class CommonSettings(BaseSettings):
    APP_NAME: str = "KASULA"
    DEBUG_MODE: bool = bool(os.getenv("DEBUG_MODE", False))


class ServerSettings(BaseSettings):
    HOST: str = "0.0.0.0"
    PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_URL: str = os.getenv("DB_URL")
    DB_NAME: str = os.getenv("DB_NAME")


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()