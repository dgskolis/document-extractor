from fastapi.testclient import TestClient

from tests.conftest import TEST_API_KEY


def test_api_v1_requires_api_key(client: TestClient) -> None:
    response = client.get("/api/v1/orders/", headers={"X-API-Key": ""})
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_api_v1_rejects_invalid_api_key(client: TestClient) -> None:
    response = client.get("/api/v1/orders/", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert response.json() == {"error": "Invalid or missing API key"}


def test_health_does_not_require_api_key(client: TestClient) -> None:
    response = client.get("/health", headers={})
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_accepts_valid_api_key(client: TestClient) -> None:
    response = client.get("/api/v1/orders/", headers={"X-API-Key": TEST_API_KEY})
    assert response.status_code == 200
