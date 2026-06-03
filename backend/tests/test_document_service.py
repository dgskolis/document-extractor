import fitz
import pytest
from pytesseract import TesseractNotFoundError
from unittest.mock import patch

from app.exceptions import TextExtractionError
from app.services import document_service, ocr_service


def _build_text_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    content = document.tobytes()
    document.close()
    return content


def _build_blank_pdf() -> bytes:
    document = fitz.open()
    document.new_page()
    content = document.tobytes()
    document.close()
    return content


def test_extract_text_returns_native_pdf_text_without_ocr() -> None:
    pdf_content = _build_text_pdf("Patient: Jane Doe, DOB 1990-05-15")

    with patch("app.services.document_service.ocr_service.ocr_document") as mock_ocr:
        text = document_service.extract_text(pdf_content, "application/pdf", "doc.pdf")

    assert text == "Patient: Jane Doe, DOB 1990-05-15"
    mock_ocr.assert_not_called()


def test_extract_text_uses_ocr_when_native_pdf_text_is_empty() -> None:
    pdf_content = _build_blank_pdf()

    with patch(
        "app.services.document_service.ocr_service.ocr_document",
        return_value="Patient: Jane Doe, DOB 1990-05-15",
    ) as mock_ocr:
        text = document_service.extract_text(
            pdf_content,
            "application/pdf",
            "scan.pdf",
            reference_id="ref-ocr",
        )

    assert text == "Patient: Jane Doe, DOB 1990-05-15"
    mock_ocr.assert_called_once()


def test_extract_text_raises_when_native_and_ocr_text_are_empty() -> None:
    pdf_content = _build_blank_pdf()

    with patch("app.services.document_service.ocr_service.ocr_document", return_value=""):
        with pytest.raises(TextExtractionError, match="Unable to extract text"):
            document_service.extract_text(pdf_content, "application/pdf", "scan.pdf")


def test_ocr_document_joins_non_empty_page_text() -> None:
    document = fitz.open()
    document.new_page()
    document.new_page()

    with patch(
        "app.services.ocr_service.ocr_page",
        side_effect=["First page", "Second page"],
    ):
        text = ocr_service.ocr_document(document)

    assert text == "First page\nSecond page"


def test_ocr_document_raises_when_tesseract_is_unavailable() -> None:
    document = fitz.open()
    document.new_page()

    with patch(
        "app.services.ocr_service.pytesseract.image_to_string",
        side_effect=TesseractNotFoundError(),
    ):
        with pytest.raises(TesseractNotFoundError):
            ocr_service.ocr_document(document, reference_id="ref-missing-tesseract")
