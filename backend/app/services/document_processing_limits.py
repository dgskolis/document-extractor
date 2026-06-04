import logging
import time

import fitz

from app.config import settings
from app.exceptions import DocumentPageLimitExceededError, DocumentProcessingTimeoutError
from app.logging_context import log_upload_event
from app.schemas.upload_errors import (
    REASON_DOCUMENT_PAGE_LIMIT,
    REASON_DOCUMENT_PROCESSING_TIMEOUT,
)


def processing_deadline() -> float:
    return time.monotonic() + settings.document_processing_timeout_seconds


def assert_page_limit(
    document: fitz.Document,
    *,
    reference_id: str | None = None,
    content_type: str | None = None,
    content_length: int | None = None,
) -> None:
    page_count = len(document)
    if page_count <= settings.max_document_pages:
        return
    if reference_id is not None:
        log_upload_event(
            logging.WARNING,
            "Document exceeds configured page limit",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_DOCUMENT_PAGE_LIMIT,
            content_type=content_type,
            content_length=content_length,
        )
    raise DocumentPageLimitExceededError(
        f"Document has {page_count} pages; maximum is {settings.max_document_pages}",
    )


def check_processing_deadline(
    deadline: float,
    *,
    reference_id: str | None = None,
    content_type: str | None = None,
    content_length: int | None = None,
) -> None:
    if time.monotonic() <= deadline:
        return
    if reference_id is not None:
        log_upload_event(
            logging.WARNING,
            "Document processing exceeded configured timeout",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_DOCUMENT_PROCESSING_TIMEOUT,
            content_type=content_type,
            content_length=content_length,
        )
    raise DocumentProcessingTimeoutError("Document processing exceeded configured timeout")
