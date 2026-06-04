import logging

from fastapi import UploadFile

from app.exceptions import (
    FileTooLargeError,
    OpenAIConfigurationError,
    PatientExtractionError,
    TextExtractionError,
    UnsupportedMediaTypeError,
)
from app.logging_context import log_upload_event
from app.schemas.document import DocumentUploadResponse, ExtractedPatientFields, build_order_create_from_extraction
from app.schemas.upload_errors import (
    REASON_FILE_TOO_LARGE,
    REASON_LLM_EXTRACTION_FAILED,
    REASON_OPENAI_NOT_CONFIGURED,
    REASON_PARTIAL_EXTRACTION,
    REASON_TEXT_EXTRACTION_FAILED,
    REASON_UNSUPPORTED_MEDIA_TYPE,
)
from app.services import document_service, patient_extraction_service


def process_upload_sync(file: UploadFile, reference_id: str) -> DocumentUploadResponse:
    content_type = file.content_type

    try:
        content = document_service.read_upload_content(file)
    except FileTooLargeError as exc:
        log_upload_event(
            logging.WARNING,
            "Upload rejected because file exceeds size limit",
            reference_id=reference_id,
            stage="upload_read",
            reason_code=REASON_FILE_TOO_LARGE,
            content_type=content_type,
        )
        raise exc

    try:
        document_text = document_service.extract_text(
            content,
            content_type=content_type,
            filename=file.filename,
            reference_id=reference_id,
        )
    except UnsupportedMediaTypeError as exc:
        log_upload_event(
            logging.WARNING,
            "Upload rejected due to unsupported media type",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_UNSUPPORTED_MEDIA_TYPE,
            content_type=content_type,
            content_length=len(content),
        )
        raise exc
    except TextExtractionError as exc:
        log_upload_event(
            logging.WARNING,
            "Upload failed during text extraction",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_TEXT_EXTRACTION_FAILED,
            content_type=content_type,
            content_length=len(content),
        )
        raise exc

    try:
        extracted_fields = patient_extraction_service.extract_patient_fields(
            document_text,
            reference_id=reference_id,
        )
    except OpenAIConfigurationError as exc:
        log_upload_event(
            logging.ERROR,
            "Upload failed because OpenAI is not configured",
            reference_id=reference_id,
            stage="patient_extraction",
            reason_code=REASON_OPENAI_NOT_CONFIGURED,
            text_length=len(document_text),
        )
        raise exc
    except PatientExtractionError as exc:
        log_upload_event(
            logging.ERROR,
            "Upload failed during patient field extraction",
            reference_id=reference_id,
            stage="patient_extraction",
            reason_code=REASON_LLM_EXTRACTION_FAILED,
            text_length=len(document_text),
        )
        raise exc

    order_in = build_order_create_from_extraction(extracted_fields, reference_id=reference_id)
    if order_in is None:
        log_upload_event(
            logging.WARNING,
            "Upload completed with partial patient field extraction",
            reference_id=reference_id,
            stage="order_validation",
            reason_code=REASON_PARTIAL_EXTRACTION,
            text_length=len(document_text),
        )
        raise PartialExtractionError(extracted_fields, reference_id=reference_id)

    log_upload_event(
        logging.INFO,
        "Upload completed successfully",
        reference_id=reference_id,
        stage="complete",
        reason_code="upload_completed",
        content_type=content_type,
        content_length=len(content),
        text_length=len(document_text),
    )
    return DocumentUploadResponse(extraction=extracted_fields)


class PartialExtractionError(Exception):
    """Raised when extraction succeeded but required fields are incomplete."""

    def __init__(self, extraction: ExtractedPatientFields, *, reference_id: str) -> None:
        self.extraction = extraction
        self.reference_id = reference_id
        super().__init__("Partial patient field extraction")
