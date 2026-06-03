import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(_ENV_PATH)

DEFAULT_DATABASE_URL = "sqlite:///./genhealth.db"


DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


class Settings(BaseModel):
    app_name: str = Field(default="GenHealth API")
    debug: bool = Field(default=False)
    database_url: str = Field(default=DEFAULT_DATABASE_URL)
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default=DEFAULT_OPENAI_MODEL)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith("sqlite:///"):
            raise ValueError("DATABASE_URL must use the sqlite:/// scheme")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "GenHealth API"),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"},
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
    )


settings = get_settings()
