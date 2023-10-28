import os
from pydantic_settings import BaseSettings
from pydantic import root_validator
from dotenv import load_dotenv


load_dotenv()


class CommonSettings(BaseSettings):
    APP_NAME: str = "KASULA"
    DEBUG_MODE: bool = bool(os.getenv("DEBUG_MODE", False))


class ServerSettings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_URL: str = os.getenv("DB_URL")
    TEST_MODE: bool = bool(os.getenv("TEST_MODE", False))
    DB_NAME: str = None

    @root_validator(pre=True)
    def set_db_name(cls, values):
        if values.get("TEST_MODE"):
            return {"DB_NAME": os.getenv("DB_TEST")}
        return {"DB_NAME": os.getenv("DB_NAME")}


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()