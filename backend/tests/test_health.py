from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError


def test_health_liveness(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_liveness_without_origin_header(client: TestClient) -> None:
    response = client.get("/health", headers={})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_readiness(client: TestClient) -> None:
    with patch("app.routes.health.check_connection"), patch("app.routes.health.check_schema_ready"):
        response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_readiness_returns_503_when_db_unavailable(client: TestClient) -> None:
    with patch("app.routes.health.check_connection", side_effect=SQLAlchemyError("locked")):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"


def test_health_readiness_returns_503_when_schema_missing(client: TestClient) -> None:
    with patch("app.routes.health.check_connection"), patch(
        "app.routes.health.check_schema_ready",
        side_effect=RuntimeError("Required database tables are missing"),
    ):
        response = client.get("/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == "Database unavailable"
