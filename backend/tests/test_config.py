import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_rejects_non_sqlite_url() -> None:
    with pytest.raises(ValidationError, match="sqlite:///"):
        Settings(database_url="postgres://localhost/db")


def test_settings_accepts_sqlite_url() -> None:
    settings = Settings(database_url="sqlite:///./genhealth.db")
    assert settings.database_url == "sqlite:///./genhealth.db"


def test_settings_debug_parsing() -> None:
    assert Settings(debug=True).debug is True
    settings = Settings.model_validate({"debug": False, "database_url": "sqlite:///./genhealth.db"})
    assert settings.debug is False
