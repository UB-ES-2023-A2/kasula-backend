import os
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

# Carregar variables d'entorn
load_dotenv('app/config/.env')


class CommonSettings(BaseSettings):
    APP_NAME: str = "KASULA"
    DEBUG_MODE: bool = os.getenv("DEBUG_MODE", False)


class ServerSettings(BaseSettings):
    HOST: str = os.getenv("HOST")
    PORT: int = os.getenv("PORT")


class DatabaseSettings(BaseSettings):
    DB_URL: str = os.getenv("DB_URL")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_TEST: str | None = os.getenv("DB_TEST")


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()