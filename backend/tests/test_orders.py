import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_create_order(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    response = client.post("/api/v1/orders/", json=sample_order_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["patient_first_name"] == "Jane"
    assert data["patient_last_name"] == "Doe"
    assert data["date_of_birth"] == "1990-05-15"
    assert data["status"] == "pending"
    assert uuid.UUID(data["id"])
    assert "created_at" in data
    assert "updated_at" in data


def test_create_order_ignores_client_status(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    response = client.post(
        "/api/v1/orders/",
        json={**sample_order_payload, "status": "completed"},
    )
    assert response.status_code == 422


def test_create_order_rejects_future_dob(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    future_dob = (date.today() + timedelta(days=1)).isoformat()
    response = client.post(
        "/api/v1/orders/",
        json={**sample_order_payload, "date_of_birth": future_dob},
    )
    assert response.status_code == 422


def test_list_orders(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    client.post("/api/v1/orders/", json=sample_order_payload)
    client.post(
        "/api/v1/orders/",
        json={**sample_order_payload, "patient_first_name": "John"},
    )

    response = client.get("/api/v1/orders/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["limit"] == 100
    assert data["offset"] == 0


def test_list_orders_pagination(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    for index in range(3):
        client.post(
            "/api/v1/orders/",
            json={**sample_order_payload, "patient_first_name": f"Patient{index}"},
        )

    response = client.get("/api/v1/orders/?limit=2&offset=1")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 1


def test_get_order(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    create_response = client.post("/api/v1/orders/", json=sample_order_payload)
    order_id = create_response.json()["id"]

    response = client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


def test_get_order_not_found(client: TestClient) -> None:
    order_id = uuid.uuid4()
    response = client.get(f"/api/v1/orders/{order_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_update_order(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    create_response = client.post("/api/v1/orders/", json=sample_order_payload)
    order_id = create_response.json()["id"]
    original_updated_at = create_response.json()["updated_at"]

    response = client.put(
        f"/api/v1/orders/{order_id}",
        json={"status": "completed", "patient_first_name": "Janet"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["patient_first_name"] == "Janet"
    assert data["patient_last_name"] == "Doe"
    assert data["updated_at"] >= original_updated_at


def test_update_order_rejects_null_field(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    create_response = client.post("/api/v1/orders/", json=sample_order_payload)
    order_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/orders/{order_id}",
        json={"patient_first_name": None},
    )
    assert response.status_code == 422


def test_update_order_rejects_invalid_status(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    create_response = client.post("/api/v1/orders/", json=sample_order_payload)
    order_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/orders/{order_id}",
        json={"status": "invalid"},
    )
    assert response.status_code == 422


def test_update_order_not_found(client: TestClient) -> None:
    order_id = uuid.uuid4()
    response = client.put(
        f"/api/v1/orders/{order_id}",
        json={"status": "completed"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_delete_order(client: TestClient, sample_order_payload: dict[str, str]) -> None:
    create_response = client.post("/api/v1/orders/", json=sample_order_payload)
    order_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/orders/{order_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/orders/{order_id}")
    assert get_response.status_code == 404


def test_delete_order_not_found(client: TestClient) -> None:
    order_id = uuid.uuid4()
    response = client.delete(f"/api/v1/orders/{order_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_create_order_validation_error(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orders/",
        json={
            "patient_first_name": "",
            "patient_last_name": "Doe",
            "date_of_birth": "1990-05-15",
        },
    )
    assert response.status_code == 422
