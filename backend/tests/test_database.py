import sqlite3
from pathlib import Path

import pytest

from app.config import BACKEND_DIR
from app.database import check_connection, sqlite_path_from_url


def test_sqlite_path_resolves_relative_to_backend_dir() -> None:
    db_path = sqlite_path_from_url("sqlite:///./genhealth.db")
    assert db_path == BACKEND_DIR / "genhealth.db"


def test_sqlite_path_keeps_absolute_paths() -> None:
    db_path = sqlite_path_from_url("sqlite:////tmp/genhealth.db")
    assert db_path == Path("/tmp/genhealth.db")


def test_sqlite_path_supports_in_memory() -> None:
    db_path = sqlite_path_from_url("sqlite:///:memory:")
    assert db_path == Path(":memory:")


def test_sqlite_path_rejects_unsupported_scheme() -> None:
    with pytest.raises(ValueError, match="Unsupported database URL"):
        sqlite_path_from_url("postgres://localhost/db")


def test_check_connection_with_temp_file(tmp_path: Path) -> None:
    db_file = tmp_path / "test.db"
    check_connection(f"sqlite:///{db_file}")
    assert db_file.exists()


def test_check_connection_in_memory() -> None:
    check_connection("sqlite:///:memory:")


def test_check_connection_creates_parent_directories(tmp_path: Path) -> None:
    db_file = tmp_path / "nested" / "dir" / "test.db"
    check_connection(f"sqlite:///{db_file}")
    assert db_file.exists()
