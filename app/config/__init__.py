import os
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv


load_dotenv()


class CommonSettings(BaseSettings):
    APP_NAME: str = "KASULA"
    DEBUG_MODE: bool = bool(os.getenv("DEBUG_MODE", False))


class ServerSettings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = os.getenv("PORT", 8080)


class DatabaseSettings(BaseSettings):
    DB_URL: str = os.getenv("DB_URL")
    DB_NAME: str = os.getenv("DB_NAME")
    DB_TEST: str = os.getenv("DB_TEST")

    # De moment comentat, però potser seria millor que peti si no té el DB_NAME?
    # @validator("DB_NAME", pre=True, always=True)
    # def set_db_name(cls, db_name, values):
    #     if values.get("TEST_MODE"):
    #         return os.getenv("DB_TEST")
    #     return db_name


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()