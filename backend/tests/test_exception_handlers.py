import uuid
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.schemas.upload_errors import GENERIC_UPLOAD_ERROR


def test_format_http_exception_content_includes_extraction_and_reference_id() -> None:
    from app.exception_handlers import format_http_exception_content

    content = format_http_exception_content(
        {
            "message": GENERIC_UPLOAD_ERROR,
            "reference_id": "ref-123",
            "extraction": {
                "first_name": "Jane",
                "last_name": None,
                "date_of_birth": "1990-05-15",
            },
        }
    )
    assert content == {
        "error": GENERIC_UPLOAD_ERROR,
        "reference_id": "ref-123",
        "extraction": {
            "first_name": "Jane",
            "last_name": None,
            "date_of_birth": "1990-05-15",
        },
    }


def test_validation_error_returns_error_field(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orders/",
        json={"patient_first_name": "Jane"},
    )
    assert response.status_code == 422
    body = response.json()
    assert "error" in body
    assert "detail" not in body
    assert "patient_last_name" in body["error"]


def test_not_found_returns_error_field(client: TestClient) -> None:
    response = client.get(f"/api/v1/orders/{uuid.uuid4()}")
    assert response.status_code == 404
    assert response.json() == {"error": "Order not found"}


def test_http_exception_with_extraction_returns_extraction_field(client: TestClient) -> None:
    from datetime import date

    from app.schemas.document import ExtractedPatientFields

    with patch("app.services.upload_pipeline.document_service.extract_text", return_value="Patient data"), patch(
        "app.services.upload_pipeline.patient_extraction_service.extract_patient_fields",
        return_value=ExtractedPatientFields(
            first_name="Jane",
            last_name=None,
            date_of_birth=date(1990, 5, 15),
        ),
    ):
        response = client.post(
            "/api/v1/orders/upload-document",
            files={"file": ("document.pdf", BytesIO(b"fake-pdf-content"), "application/pdf")},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == GENERIC_UPLOAD_ERROR
    assert body["reference_id"]
    assert body["extraction"] == {
        "first_name": "Jane",
        "last_name": None,
        "date_of_birth": "1990-05-15",
    }
