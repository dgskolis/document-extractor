import pytest
from pydantic import ValidationError
from unittest.mock import patch

from app.config import Settings, validate_settings
from app.schemas.order import OrderStatus


def test_settings_rejects_invalid_url_scheme() -> None:
    with pytest.raises(ValidationError, match="sqlite://"):
        Settings(database_url="mysql://localhost/db")


def test_settings_accepts_sqlite_url() -> None:
    settings = Settings(database_url="sqlite:////tmp/orders.db")
    assert settings.database_url == "sqlite:////tmp/orders.db"


def test_settings_accepts_postgresql_url() -> None:
    settings = Settings(database_url="postgresql://user:pass@localhost:5432/mydb")
    assert settings.database_url == "postgresql://user:pass@localhost:5432/mydb"


def test_settings_accepts_postgres_url() -> None:
    settings = Settings(database_url="postgres://user:pass@localhost:5432/mydb")
    assert settings.database_url == "postgres://user:pass@localhost:5432/mydb"


def test_settings_default_database_url() -> None:
    from app.config import DEFAULT_DATABASE_URL

    settings = Settings()
    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.database_url == "sqlite:////tmp/orders.db"


def test_settings_openai_defaults() -> None:
    settings = Settings(database_url="sqlite:////tmp/orders.db")
    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-4o-mini"


def test_settings_openai_values() -> None:
    settings = Settings(
        database_url="sqlite:////tmp/orders.db",
        openai_api_key="sk-test",
        openai_model="gpt-4o",
    )
    assert settings.openai_api_key == "sk-test"
    assert settings.openai_model == "gpt-4o"


def test_settings_upload_and_timeout_defaults() -> None:
    settings = Settings(database_url="sqlite:////tmp/orders.db")
    assert settings.max_upload_size_bytes == 25 * 1024 * 1024
    assert settings.openai_timeout_seconds == 60.0
    assert settings.activity_log_max_entries == 10_000
    assert settings.max_document_text_chars == 100_000
    assert settings.max_document_pages == 50
    assert settings.document_processing_timeout_seconds == 180.0
    assert settings.upload_max_workers == 2
    assert settings.openai_max_retries == 3
    assert settings.openai_retry_min_seconds == 1.0
    assert settings.openai_retry_max_seconds == 8.0
    assert settings.db_commit_max_retries == 5
    assert settings.db_commit_retry_min_seconds == 0.05
    assert settings.db_commit_retry_max_seconds == 0.5
    assert settings.sqlite_busy_timeout_ms == 30_000


def test_get_settings_reads_document_and_retry_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("MAX_DOCUMENT_PAGES", "10")
    monkeypatch.setenv("DOCUMENT_PROCESSING_TIMEOUT_SECONDS", "90")
    monkeypatch.setenv("UPLOAD_MAX_WORKERS", "4")
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "2")
    try:
        settings = get_settings()
        assert settings.max_document_pages == 10
        assert settings.document_processing_timeout_seconds == 90.0
        assert settings.upload_max_workers == 4
        assert settings.openai_max_retries == 2
    finally:
        get_settings.cache_clear()


def test_get_settings_rejects_invalid_int_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("MAX_UPLOAD_SIZE_BYTES", "not-a-number")
    try:
        with pytest.raises(ValueError, match="MAX_UPLOAD_SIZE_BYTES must be an integer"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_get_settings_rejects_invalid_float_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "abc")
    try:
        with pytest.raises(ValueError, match="OPENAI_TIMEOUT_SECONDS must be a number"):
            get_settings()
    finally:
        get_settings.cache_clear()


def test_validate_settings_requires_api_key() -> None:
    empty_settings = Settings(api_key=None, database_url="sqlite:////tmp/orders.db")
    with patch("app.config.settings", empty_settings):
        with pytest.raises(RuntimeError, match="API_KEY"):
            validate_settings()


def test_validate_settings_passes_with_api_key() -> None:
    configured = Settings(api_key="secret", database_url="sqlite:////tmp/orders.db")
    with patch("app.config.settings", configured):
        validate_settings()


def test_settings_debug_parsing() -> None:
    assert Settings(debug=True).debug is True
    settings = Settings.model_validate({"debug": False, "database_url": "sqlite:////tmp/orders.db"})
    assert settings.debug is False


def test_order_status_values() -> None:
    assert OrderStatus.PENDING == "pending"
    assert OrderStatus.COMPLETED == "completed"
