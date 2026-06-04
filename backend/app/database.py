import logging
from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import BACKEND_DIR, settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


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


def get_sqlalchemy_database_url(database_url: str | None = None) -> str:
    url = database_url or settings.database_url
    if url.startswith("postgresql://") or url.startswith("postgres://"):
        return url
    if url.endswith(":memory:"):
        return url
    db_path = sqlite_path_from_url(url)
    if db_path == Path(":memory:"):
        return "sqlite:///:memory:"
    return f"sqlite:///{db_path}"


def is_sqlite_url(database_url: str) -> bool:
    return database_url.startswith("sqlite://")


def is_postgres_url(database_url: str) -> bool:
    return database_url.startswith("postgresql://") or database_url.startswith("postgres://")


def _configure_sqlite_connection(dbapi_connection, _connection_record=None) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute(f"PRAGMA busy_timeout={settings.sqlite_busy_timeout_ms}")
    cursor.close()


def _create_engine(database_url: str | None = None):
    url = get_sqlalchemy_database_url(database_url)
    source_url = database_url or settings.database_url

    if is_sqlite_url(source_url):
        connect_args = {
            "check_same_thread": False,
            "timeout": settings.sqlite_busy_timeout_ms / 1000,
        }
        eng = create_engine(url, connect_args=connect_args)
        event.listen(eng, "connect", _configure_sqlite_connection)
        return eng

    if is_postgres_url(source_url):
        return create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )

    return create_engine(url)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_connection(database_url: str | None = None) -> None:
    eng = _create_engine(database_url) if database_url else engine
    url = database_url or settings.database_url

    if url.startswith("postgresql://") or url.startswith("postgres://"):
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection confirmed (postgresql)")
        return

    db_path = sqlite_path_from_url(url)

    if db_path != Path(":memory:"):
        db_path.parent.mkdir(parents=True, exist_ok=True)

    with eng.connect() as conn:
        conn.execute(text("SELECT 1"))

    if db_path == Path(":memory:"):
        logger.info("Database connection confirmed (in-memory)")
    else:
        logger.info("Database connection confirmed at %s", db_path)


def check_schema_ready(database_url: str | None = None) -> None:
    eng = _create_engine(database_url) if database_url else engine
    inspector = inspect(eng)
    required_tables = {"orders", "activity_logs"}
    missing_tables = required_tables - set(inspector.get_table_names())
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"Required database tables are missing: {missing}")


def _index_exists(inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def run_migrations() -> None:
    from alembic.runtime.migration import MigrationContext

    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    # Avoid Alembic's fileConfig disabling uvicorn/app loggers during app startup.
    alembic_cfg.attributes["configure_logger"] = False

    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current_revision = context.get_current_revision()

    if current_revision is None:
        inspector = inspect(engine)
        if "orders" in inspector.get_table_names():
            if _index_exists(inspector, "orders", "ix_orders_created_at"):
                command.stamp(alembic_cfg, "head")
                logger.info("Stamped pre-existing database at head")
                return
            command.stamp(alembic_cfg, "001")
            logger.info("Stamped pre-existing database at revision 001")

    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied")
