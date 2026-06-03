import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.database import Base, get_db
from app.main import app
from app.models.order import Order  # noqa: F401


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session) -> TestClient:
    def override_get_db():
        try:
            yield db_session
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with patch("app.main.check_connection"), patch("app.main.run_migrations"):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_order_payload() -> dict[str, str]:
    return {
        "patient_first_name": "Jane",
        "patient_last_name": "Doe",
        "date_of_birth": "1990-05-15",
    }
