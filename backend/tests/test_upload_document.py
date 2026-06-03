from datetime import date
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.exceptions import (
    FileTooLargeError,
    PatientExtractionError,
    TextExtractionError,
    UnsupportedMediaTypeError,
)
from app.models.order import Order
from app.schemas.document import ExtractedPatientFields
from app.services import document_service


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


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_name_too_long(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
    db_session,
) -> None:
    mock_extract_text.return_value = "Patient data"
    mock_extract_patient_fields.return_value = ExtractedPatientFields(
        first_name="A" * 256,
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
    )

    response = _upload_file(client)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["message"] == "Could not extract all required patient fields from document"
    assert detail["extraction"]["first_name"] == "A" * 256
    order_count = db_session.scalar(select(func.count()).select_from(Order))
    assert order_count == 0


@patch("app.routes.orders.patient_extraction_service.extract_patient_fields")
@patch("app.routes.orders.document_service.extract_text")
def test_upload_document_whitespace_only_names(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
    db_session,
) -> None:
    mock_extract_text.return_value = "Patient data"
    mock_extract_patient_fields.return_value = ExtractedPatientFields(
        first_name="   ",
        last_name="Doe",
        date_of_birth=date(1990, 5, 15),
    )

    response = _upload_file(client)

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["extraction"]["first_name"] is None
    order_count = db_session.scalar(select(func.count()).select_from(Order))
    assert order_count == 0


def test_upload_document_unsupported_media_type(client: TestClient) -> None:
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
    assert response.json()["detail"] == {
        "message": "Unable to extract text from document",
    }


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
def test_upload_document_missing_openai_key(
    mock_extract_text,
    mock_extract_patient_fields,
    client: TestClient,
) -> None:
    mock_extract_text.return_value = "Patient: Jane Doe, DOB 1990-05-15"
    from app.exceptions import OpenAIConfigurationError

    mock_extract_patient_fields.side_effect = OpenAIConfigurationError("OpenAI API key not configured")

    response = _upload_file(client)

    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI API key not configured"


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


@patch("app.routes.orders.document_service.read_upload_content")
def test_upload_document_file_too_large(mock_read_upload_content, client: TestClient) -> None:
    mock_read_upload_content.side_effect = FileTooLargeError(
        "Uploaded file exceeds maximum size of 26214400 bytes",
    )

    response = _upload_file(client)

    assert response.status_code == 413


def test_upload_document_requires_file(client: TestClient) -> None:
    response = client.post("/api/v1/orders/upload-document")
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("content_type", "filename", "expected_filetype"),
    [
        ("application/pdf", "doc.pdf", "pdf"),
        ("image/jpeg", "photo.jpg", "jpeg"),
        ("image/jpg", "photo.jpg", "jpeg"),
        ("image/png", "scan.png", "png"),
        ("application/octet-stream", "scan.tiff", "tiff"),
    ],
)
def test_resolve_filetype(content_type: str, filename: str, expected_filetype: str) -> None:
    assert document_service.resolve_filetype(content_type, filename) == expected_filetype


def test_resolve_filetype_unsupported() -> None:
    with pytest.raises(UnsupportedMediaTypeError):
        document_service.resolve_filetype("text/plain", "notes.txt")


def test_extract_text_rejects_empty_content() -> None:
    with pytest.raises(TextExtractionError, match="Unable to extract text"):
        document_service.extract_text(b"", "application/pdf", "doc.pdf")


def test_normalize_extracted_fields_parses_invalid_dob_as_none() -> None:
    from app.services.patient_extraction_service import (
        _RawExtractedPatientFields,
        _normalize_extracted_fields,
    )

    result = _normalize_extracted_fields(
        _RawExtractedPatientFields(
            first_name="Jane",
            last_name="Doe",
            date_of_birth="not-a-date",
        )
    )
    assert result.first_name == "Jane"
    assert result.last_name == "Doe"
    assert result.date_of_birth is None


def test_normalize_extracted_fields_strips_names() -> None:
    from app.services.patient_extraction_service import (
        _RawExtractedPatientFields,
        _normalize_extracted_fields,
    )

    result = _normalize_extracted_fields(
        _RawExtractedPatientFields(
            first_name="  Jane  ",
            last_name="  Doe ",
            date_of_birth="1990-05-15",
        )
    )
    assert result.first_name == "Jane"
    assert result.last_name == "Doe"
    assert result.date_of_birth == date(1990, 5, 15)
