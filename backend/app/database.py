import logging
import sqlite3
from pathlib import Path

from app.config import BACKEND_DIR, settings

logger = logging.getLogger(__name__)


def sqlite_path_from_url(
    database_url: str,
    base_dir: Path = BACKEND_DIR,
) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError(f"Unsupported database URL: {database_url}")

    path_part = database_url.removeprefix("sqlite:///")
    if path_part == ":memory:":
        return Path(":memory:")

    db_path = Path(path_part)
    if not db_path.is_absolute():
        db_path = base_dir / db_path
    return db_path


def check_connection(database_url: str | None = None) -> None:
    url = database_url or settings.database_url
    db_path = sqlite_path_from_url(url)

    if db_path == Path(":memory:"):
        with sqlite3.connect(":memory:") as conn:
            conn.execute("SELECT 1")
        logger.info("Database connection confirmed (in-memory)")
        return

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("SELECT 1")

    logger.info("Database connection confirmed at %s", db_path)
