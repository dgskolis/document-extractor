from datetime import date
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.exceptions import PatientExtractionError, TextExtractionError, UnsupportedMediaTypeError
from app.models.order import Order
from app.schemas.document import ExtractedPatientFields


def _upload_file(
    client: TestClient,
    *,
    content: bytes = b"fake-pdf-content",
    filename: str = "document.pdf",
    content_type: str = "application/pdf",
):
    return client.post(
        "/api/v1/orders/upload-document",
        files={"file": (filename, BytesIO(content), content_type)},
    )


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_success(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
) -> None:
    mock_extract_text.return_value = "Patient: Jane Doe, DOB 1990-05-15"
    mock_extract_patient_fields.return_value = ExtractedPatientFields(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
    )

    response = _upload_file(client)

    assert response.status_code == 201
    data = response.json()
    assert data["extraction"] == {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1990-05-15",
    }
    assert data["order"]["patient_first_name"] == "Jane"
    assert data["order"]["patient_last_name"] == "Doe"
    assert data["order"]["date_of_birth"] == "1990-05-15"
    assert data["order"]["status"] == "pending"


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_partial_extraction(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
    db_session,
) -> None:
    mock_extract_text.return_value = "Patient: Jane, DOB 1990-05-15"
    mock_extract_patient_fields.return_value = ExtractedPatientFields(
        first_name="Jane",
        last_name=None,
        date_of_birth=date(1990, 5, 15),
    )

    response = _upload_file(client)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["message"] == "Could not extract all required patient fields from document"
    assert detail["extraction"]["first_name"] == "Jane"
    assert detail["extraction"]["last_name"] is None
    assert detail["extraction"]["date_of_birth"] == "1990-05-15"

    order_count = db_session.scalar(select(func.count()).select_from(Order))
    assert order_count == 0


@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_unsupported_media_type(mock_extract_text, client: TestClient) -> None:
    mock_extract_text.side_effect = UnsupportedMediaTypeError("Unsupported file type")

    response = _upload_file(
        client,
        filename="document.txt",
        content_type="text/plain",
    )

    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported file type"


@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_empty_text_extraction(mock_extract_text, client: TestClient) -> None:
    mock_extract_text.side_effect = TextExtractionError("Unable to extract text from document")

    response = _upload_file(client)

    assert response.status_code == 422
    assert response.json()["detail"] == "Unable to extract text from document"


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_llm_failure(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
) -> None:
    mock_extract_text.return_value = "Patient: Jane Doe"
    mock_extract_patient_fields.side_effect = PatientExtractionError("Patient field extraction failed")

    response = _upload_file(client)

    assert response.status_code == 502
    assert response.json()["detail"] == "Patient field extraction failed"


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_route_not_treated_as_order_id(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
) -> None:
    mock_extract_text.return_value = "Patient: Jane Doe, DOB 1990-05-15"
    mock_extract_patient_fields.return_value = ExtractedPatientFields(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
    )

    response = _upload_file(client)

    assert response.status_code == 201
    assert "order" in response.json()


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_future_dob_treated_as_partial(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
    db_session,
) -> None:
    mock_extract_text.return_value = "Patient: Jane Doe"
    mock_extract_patient_fields.return_value = ExtractedPatientFields(
        first_name="Jane",
        last_name="Doe",
        date_of_birth=None,
    )

    response = _upload_file(client)

    assert response.status_code == 422
    assert response.json()["detail"]["extraction"]["date_of_birth"] is None
    order_count = db_session.scalar(select(func.count()).select_from(Order))
    assert order_count == 0


def test_upload_document_requires_file(client: TestClient) -> None:
    response = client.post("/api/v1/orders/upload-document")
    assert response.status_code == 422
