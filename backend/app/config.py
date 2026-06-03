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
DEFAULT_MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
DEFAULT_ACTIVITY_LOG_MAX_ENTRIES = 10_000
READ_CHUNK_SIZE_BYTES = 1024 * 1024


class Settings(BaseModel):
    app_name: str = Field(default="GenHealth API")
    debug: bool = Field(default=False)
    database_url: str = Field(default=DEFAULT_DATABASE_URL)
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default=DEFAULT_OPENAI_MODEL)
    max_upload_size_bytes: int = Field(default=DEFAULT_MAX_UPLOAD_SIZE_BYTES, gt=0)
    openai_timeout_seconds: float = Field(default=DEFAULT_OPENAI_TIMEOUT_SECONDS, gt=0)
    activity_log_max_entries: int = Field(default=DEFAULT_ACTIVITY_LOG_MAX_ENTRIES, gt=0)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith("sqlite:///"):
            raise ValueError("DATABASE_URL must use the sqlite:/// scheme")
        return value


@lru_cache
def get_settings() -> Settings:
    max_upload_size = os.getenv("MAX_UPLOAD_SIZE_BYTES", str(DEFAULT_MAX_UPLOAD_SIZE_BYTES))
    openai_timeout = os.getenv("OPENAI_TIMEOUT_SECONDS", str(DEFAULT_OPENAI_TIMEOUT_SECONDS))
    activity_log_max_entries = os.getenv(
        "ACTIVITY_LOG_MAX_ENTRIES",
        str(DEFAULT_ACTIVITY_LOG_MAX_ENTRIES),
    )
    return Settings(
        app_name=os.getenv("APP_NAME", "GenHealth API"),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"},
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        max_upload_size_bytes=int(max_upload_size),
        openai_timeout_seconds=float(openai_timeout),
        activity_log_max_entries=int(activity_log_max_entries),
    )


settings = get_settings()
