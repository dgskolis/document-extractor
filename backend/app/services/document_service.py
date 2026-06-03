import logging
from datetime import date
from pathlib import PurePath

import fitz
from fastapi import UploadFile

from app.config import READ_CHUNK_SIZE_BYTES, settings
from app.exceptions import FileTooLargeError, TextExtractionError, UnsupportedMediaTypeError

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


def extract_text(content: bytes, content_type: str | None, filename: str | None) -> str:
    if not content:
        raise TextExtractionError("Unable to extract text from document")

    filetype = resolve_filetype(content_type, filename)

    try:
        document = fitz.open(stream=content, filetype=filetype)
    except Exception as exc:
        logger.exception("Failed to open document for text extraction")
        raise TextExtractionError("Unable to extract text from document") from exc

    try:
        text_parts = [page.get_text() for page in document]
    finally:
        document.close()

    text = "\n".join(part for part in text_parts if part).strip()
    if not text:
        raise TextExtractionError("Unable to extract text from document")

    return text
