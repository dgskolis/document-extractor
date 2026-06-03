import pytest
from pydantic import ValidationError

from app.config import Settings
from app.schemas.order import OrderStatus


def test_settings_rejects_non_sqlite_url() -> None:
    with pytest.raises(ValidationError, match="sqlite:///"):
        Settings(database_url="postgres://localhost/db")


def test_settings_accepts_sqlite_url() -> None:
    settings = Settings(database_url="sqlite:///./genhealth.db")
    assert settings.database_url == "sqlite:///./genhealth.db"


def test_settings_openai_defaults() -> None:
    settings = Settings(database_url="sqlite:///./genhealth.db")
    assert settings.openai_api_key is None
    assert settings.openai_model == "gpt-4o-mini"


def test_settings_openai_values() -> None:
    settings = Settings(
        database_url="sqlite:///./genhealth.db",
        openai_api_key="sk-test",
        openai_model="gpt-4o",
    )
    assert settings.openai_api_key == "sk-test"
    assert settings.openai_model == "gpt-4o"


def test_settings_upload_and_timeout_defaults() -> None:
    settings = Settings(database_url="sqlite:///./genhealth.db")
    assert settings.max_upload_size_bytes == 25 * 1024 * 1024
    assert settings.openai_timeout_seconds == 60.0


def test_settings_debug_parsing() -> None:
    assert Settings(debug=True).debug is True
    settings = Settings.model_validate({"debug": False, "database_url": "sqlite:///./genhealth.db"})
    assert settings.debug is False


def test_order_status_values() -> None:
    assert OrderStatus.PENDING == "pending"
    assert OrderStatus.COMPLETED == "completed"
