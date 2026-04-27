from pydantic_settings import BaseSettings
import os

class NaspySettings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    class Config:
        env_file = ".env"

settings = NaspySettings()