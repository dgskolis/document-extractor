from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, text

from app.config import BACKEND_DIR
from app.database import (
    check_connection,
    check_schema_ready,
    get_sqlalchemy_database_url,
    sqlite_path_from_url,
)


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


def test_get_sqlalchemy_database_url_resolves_relative_path() -> None:
    url = get_sqlalchemy_database_url("sqlite:///./genhealth.db")
    assert url == f"sqlite:///{BACKEND_DIR / 'genhealth.db'}"


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


def test_check_schema_ready_passes_when_orders_table_exists(tmp_path: Path) -> None:
    db_file = tmp_path / "schema_test.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(get_sqlalchemy_database_url(db_url), connect_args={"check_same_thread": False})

    from app.database import Base
    from app.models.order import Order  # noqa: F401

    Base.metadata.create_all(bind=engine)
    check_schema_ready(db_url)


def test_check_schema_ready_fails_when_orders_table_missing(tmp_path: Path) -> None:
    db_file = tmp_path / "empty.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(get_sqlalchemy_database_url(db_url), connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    with pytest.raises(RuntimeError, match="Required database tables are missing"):
        check_schema_ready(db_url)
