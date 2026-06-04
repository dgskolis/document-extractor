import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(_ENV_PATH)

DEFAULT_DATABASE_URL = "sqlite:////tmp/orders.db"


DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
DEFAULT_ACTIVITY_LOG_MAX_ENTRIES = 10_000
DEFAULT_MAX_DOCUMENT_TEXT_CHARS = 100_000
DEFAULT_OCR_DPI = 300
DEFAULT_TESSERACT_LANG = "eng"
DEFAULT_MAX_DOCUMENT_PAGES = 50
DEFAULT_DOCUMENT_PROCESSING_TIMEOUT_SECONDS = 180.0
DEFAULT_UPLOAD_MAX_WORKERS = 2
DEFAULT_OPENAI_MAX_RETRIES = 3
DEFAULT_OPENAI_RETRY_MIN_SECONDS = 1.0
DEFAULT_OPENAI_RETRY_MAX_SECONDS = 8.0
DEFAULT_DB_COMMIT_MAX_RETRIES = 5
DEFAULT_DB_COMMIT_RETRY_MIN_SECONDS = 0.05
DEFAULT_DB_COMMIT_RETRY_MAX_SECONDS = 0.5
DEFAULT_SQLITE_BUSY_TIMEOUT_MS = 30_000
READ_CHUNK_SIZE_BYTES = 1024 * 1024


class Settings(BaseModel):
    app_name: str = Field(default="GenHealth API")
    debug: bool = Field(default=False)
    database_url: str = Field(default=DEFAULT_DATABASE_URL)
    api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default=DEFAULT_OPENAI_MODEL)
    max_upload_size_bytes: int = Field(default=DEFAULT_MAX_UPLOAD_SIZE_BYTES, gt=0)
    openai_timeout_seconds: float = Field(default=DEFAULT_OPENAI_TIMEOUT_SECONDS, gt=0)
    activity_log_max_entries: int = Field(default=DEFAULT_ACTIVITY_LOG_MAX_ENTRIES, gt=0)
    max_document_text_chars: int = Field(default=DEFAULT_MAX_DOCUMENT_TEXT_CHARS, gt=0)
    tesseract_cmd: str | None = Field(default=None)
    tesseract_lang: str = Field(default=DEFAULT_TESSERACT_LANG)
    ocr_dpi: int = Field(default=DEFAULT_OCR_DPI, gt=0)
    max_document_pages: int = Field(default=DEFAULT_MAX_DOCUMENT_PAGES, gt=0)
    document_processing_timeout_seconds: float = Field(
        default=DEFAULT_DOCUMENT_PROCESSING_TIMEOUT_SECONDS,
        gt=0,
    )
    upload_max_workers: int = Field(default=DEFAULT_UPLOAD_MAX_WORKERS, gt=0)
    openai_max_retries: int = Field(default=DEFAULT_OPENAI_MAX_RETRIES, ge=0)
    openai_retry_min_seconds: float = Field(default=DEFAULT_OPENAI_RETRY_MIN_SECONDS, gt=0)
    openai_retry_max_seconds: float = Field(default=DEFAULT_OPENAI_RETRY_MAX_SECONDS, gt=0)
    db_commit_max_retries: int = Field(default=DEFAULT_DB_COMMIT_MAX_RETRIES, ge=0)
    db_commit_retry_min_seconds: float = Field(default=DEFAULT_DB_COMMIT_RETRY_MIN_SECONDS, gt=0)
    db_commit_retry_max_seconds: float = Field(default=DEFAULT_DB_COMMIT_RETRY_MAX_SECONDS, gt=0)
    sqlite_busy_timeout_ms: int = Field(default=DEFAULT_SQLITE_BUSY_TIMEOUT_MS, gt=0)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        valid_schemes = ("sqlite://", "postgresql://", "postgres://")
        if not any(value.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(
                "DATABASE_URL must use the sqlite://, postgresql://, or postgres:// scheme"
            )
        return value


def _strip_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_int_env(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _parse_float_env(name: str, default: float) -> float:
    raw = os.getenv(name, str(default))
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "GenHealth API"),
        debug=os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"},
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        api_key=_strip_optional_env("API_KEY"),
        openai_api_key=_strip_optional_env("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        max_upload_size_bytes=_parse_int_env("MAX_UPLOAD_SIZE_BYTES", DEFAULT_MAX_UPLOAD_SIZE_BYTES),
        openai_timeout_seconds=_parse_float_env("OPENAI_TIMEOUT_SECONDS", DEFAULT_OPENAI_TIMEOUT_SECONDS),
        activity_log_max_entries=_parse_int_env(
            "ACTIVITY_LOG_MAX_ENTRIES",
            DEFAULT_ACTIVITY_LOG_MAX_ENTRIES,
        ),
        max_document_text_chars=_parse_int_env(
            "MAX_DOCUMENT_TEXT_CHARS",
            DEFAULT_MAX_DOCUMENT_TEXT_CHARS,
        ),
        tesseract_cmd=_strip_optional_env("TESSERACT_CMD"),
        tesseract_lang=os.getenv("TESSERACT_LANG", DEFAULT_TESSERACT_LANG),
        ocr_dpi=_parse_int_env("OCR_DPI", DEFAULT_OCR_DPI),
        max_document_pages=_parse_int_env("MAX_DOCUMENT_PAGES", DEFAULT_MAX_DOCUMENT_PAGES),
        document_processing_timeout_seconds=_parse_float_env(
            "DOCUMENT_PROCESSING_TIMEOUT_SECONDS",
            DEFAULT_DOCUMENT_PROCESSING_TIMEOUT_SECONDS,
        ),
        upload_max_workers=_parse_int_env("UPLOAD_MAX_WORKERS", DEFAULT_UPLOAD_MAX_WORKERS),
        openai_max_retries=_parse_int_env("OPENAI_MAX_RETRIES", DEFAULT_OPENAI_MAX_RETRIES),
        openai_retry_min_seconds=_parse_float_env(
            "OPENAI_RETRY_MIN_SECONDS",
            DEFAULT_OPENAI_RETRY_MIN_SECONDS,
        ),
        openai_retry_max_seconds=_parse_float_env(
            "OPENAI_RETRY_MAX_SECONDS",
            DEFAULT_OPENAI_RETRY_MAX_SECONDS,
        ),
        db_commit_max_retries=_parse_int_env("DB_COMMIT_MAX_RETRIES", DEFAULT_DB_COMMIT_MAX_RETRIES),
        db_commit_retry_min_seconds=_parse_float_env(
            "DB_COMMIT_RETRY_MIN_SECONDS",
            DEFAULT_DB_COMMIT_RETRY_MIN_SECONDS,
        ),
        db_commit_retry_max_seconds=_parse_float_env(
            "DB_COMMIT_RETRY_MAX_SECONDS",
            DEFAULT_DB_COMMIT_RETRY_MAX_SECONDS,
        ),
        sqlite_busy_timeout_ms=_parse_int_env(
            "SQLITE_BUSY_TIMEOUT_MS",
            DEFAULT_SQLITE_BUSY_TIMEOUT_MS,
        ),
    )


settings = get_settings()


def validate_settings() -> None:
    if not settings.api_key:
        raise RuntimeError("API_KEY environment variable is required")
