import logging
from pathlib import PurePath

import fitz
from fastapi import UploadFile
from pytesseract import TesseractNotFoundError

from app.config import READ_CHUNK_SIZE_BYTES, settings
from app.exceptions import (
    DocumentPageLimitExceededError,
    DocumentProcessingTimeoutError,
    FileTooLargeError,
    TextExtractionError,
    UnsupportedMediaTypeError,
)
from app.logging_context import log_upload_event
from app.schemas.upload_errors import (
    REASON_OCR_FALLBACK,
    REASON_OCR_TEXT_EXTRACTED,
    REASON_TEXT_EXTRACTION_FAILED,
    REASON_UNSUPPORTED_MEDIA_TYPE,
)
from app.services import ocr_service
from app.services.document_processing_limits import (
    assert_page_limit,
    check_processing_deadline,
    processing_deadline,
)

logger = logging.getLogger(__name__)

SUPPORTED_CONTENT_TYPES: dict[str, str] = {
    "application/pdf": "pdf",
    "image/jpeg": "jpeg",
    "image/jpg": "jpeg",
    "image/png": "png",
    "image/webp": "webp",
    "image/tiff": "tiff",
}

EXTENSION_TO_FILETYPE: dict[str, str] = {
    ".pdf": "pdf",
    ".jpg": "jpeg",
    ".jpeg": "jpeg",
    ".png": "png",
    ".webp": "webp",
    ".tif": "tiff",
    ".tiff": "tiff",
}


def resolve_filetype(content_type: str | None, filename: str | None) -> str:
    normalized_content_type = (content_type or "").split(";")[0].strip().lower()
    if normalized_content_type in SUPPORTED_CONTENT_TYPES:
        return SUPPORTED_CONTENT_TYPES[normalized_content_type]

    if filename:
        extension = PurePath(filename).suffix.lower()
        if extension in EXTENSION_TO_FILETYPE:
            return EXTENSION_TO_FILETYPE[extension]

    raise UnsupportedMediaTypeError("Unsupported file type")


def read_upload_content(
    upload_file: UploadFile,
    *,
    max_size_bytes: int | None = None,
) -> bytes:
    limit = max_size_bytes if max_size_bytes is not None else settings.max_upload_size_bytes
    chunks: list[bytes] = []
    total_size = 0

    while True:
        chunk = upload_file.file.read(READ_CHUNK_SIZE_BYTES)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > limit:
            raise FileTooLargeError(
                f"Uploaded file exceeds maximum size of {limit} bytes",
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _extract_native_text(
    document: fitz.Document,
    *,
    deadline: float,
    reference_id: str | None = None,
    content_type: str | None = None,
    content_length: int | None = None,
) -> list[str]:
    text_parts: list[str] = []
    for page in document:
        check_processing_deadline(
            deadline,
            reference_id=reference_id,
            content_type=content_type,
            content_length=content_length,
        )
        text_parts.append(page.get_text())
    return text_parts


def extract_text(
    content: bytes,
    content_type: str | None,
    filename: str | None,
    *,
    reference_id: str | None = None,
) -> str:
    if not content:
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Document text extraction failed for empty content",
                reference_id=reference_id,
                stage="text_extraction",
                reason_code=REASON_TEXT_EXTRACTION_FAILED,
                content_type=content_type,
                content_length=0,
            )
        raise TextExtractionError("Unable to extract text from document")

    try:
        filetype = resolve_filetype(content_type, filename)
    except UnsupportedMediaTypeError as exc:
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Unsupported document media type",
                reference_id=reference_id,
                stage="text_extraction",
                reason_code=REASON_UNSUPPORTED_MEDIA_TYPE,
                content_type=content_type,
                content_length=len(content),
            )
        raise exc

    try:
        document = fitz.open(stream=content, filetype=filetype)
    except Exception as exc:
        if reference_id is not None:
            log_upload_event(
                logging.ERROR,
                "Failed to open document for text extraction",
                reference_id=reference_id,
                stage="text_extraction",
                reason_code=REASON_TEXT_EXTRACTION_FAILED,
                content_type=content_type,
                content_length=len(content),
                exc_info=exc,
            )
        else:
            logger.exception("Failed to open document for text extraction")
        raise TextExtractionError("Unable to extract text from document") from exc

    deadline = processing_deadline()
    try:
        assert_page_limit(
            document,
            reference_id=reference_id,
            content_type=content_type,
            content_length=len(content),
        )
        try:
            text_parts = _extract_native_text(
                document,
                deadline=deadline,
                reference_id=reference_id,
                content_type=content_type,
                content_length=len(content),
            )
        except (DocumentPageLimitExceededError, DocumentProcessingTimeoutError):
            raise
        except Exception as exc:
            if reference_id is not None:
                log_upload_event(
                    logging.ERROR,
                    "Failed to read document pages for text extraction",
                    reference_id=reference_id,
                    stage="text_extraction",
                    reason_code=REASON_TEXT_EXTRACTION_FAILED,
                    content_type=content_type,
                    content_length=len(content),
                    exc_info=exc,
                )
            raise TextExtractionError("Unable to extract text from document") from exc

        text = "\n".join(part for part in text_parts if part).strip()
        if text:
            return text

        if reference_id is not None:
            log_upload_event(
                logging.INFO,
                "Native text extraction produced no text; attempting OCR fallback",
                reference_id=reference_id,
                stage="text_extraction",
                reason_code=REASON_OCR_FALLBACK,
                content_type=content_type,
                content_length=len(content),
                text_length=0,
            )

        try:
            text = ocr_service.ocr_document(
                document,
                reference_id=reference_id,
                deadline=deadline,
                content_type=content_type,
                content_length=len(content),
            )
        except (DocumentPageLimitExceededError, DocumentProcessingTimeoutError):
            raise
        except TesseractNotFoundError as exc:
            raise TextExtractionError("Unable to extract text from document") from exc
        except Exception as exc:
            raise TextExtractionError("Unable to extract text from document") from exc

        if text:
            if reference_id is not None:
                log_upload_event(
                    logging.INFO,
                    "Document text extracted via OCR fallback",
                    reference_id=reference_id,
                    stage="text_extraction",
                    reason_code=REASON_OCR_TEXT_EXTRACTED,
                    content_type=content_type,
                    content_length=len(content),
                    text_length=len(text),
                )
            return text
    finally:
        document.close()

    if reference_id is not None:
        log_upload_event(
            logging.WARNING,
            "Document text extraction produced no text",
            reference_id=reference_id,
            stage="text_extraction",
            reason_code=REASON_TEXT_EXTRACTION_FAILED,
            content_type=content_type,
            content_length=len(content),
            text_length=0,
        )
    raise TextExtractionError("Unable to extract text from document")
