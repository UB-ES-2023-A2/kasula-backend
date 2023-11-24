import os
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv

# Carregar variables d'entorn
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# Sobreescriure amb possibles variables locals
dotenv_path_local = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(dotenv_path_local, override=True)


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
    TEST_ENV: bool = bool(os.getenv("TEST_ENV", False))


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()