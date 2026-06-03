import logging

import fitz
import pytesseract
from PIL import Image
from pytesseract import TesseractNotFoundError

from app.config import settings
from app.logging_context import log_upload_event
from app.schemas.upload_errors import REASON_OCR_FAILED, REASON_OCR_UNAVAILABLE

logger = logging.getLogger(__name__)


def _configure_tesseract() -> None:
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def ocr_page(page: fitz.Page, *, dpi: int | None = None) -> str:
    render_dpi = dpi if dpi is not None else settings.ocr_dpi
    pixmap = page.get_pixmap(dpi=render_dpi)
    image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
    return pytesseract.image_to_string(image, lang=settings.tesseract_lang)


def ocr_document(
    document: fitz.Document,
    *,
    reference_id: str | None = None,
    dpi: int | None = None,
) -> str:
    _configure_tesseract()
    text_parts: list[str] = []

    try:
        for page in document:
            page_text = ocr_page(page, dpi=dpi).strip()
            if page_text:
                text_parts.append(page_text)
    except TesseractNotFoundError as exc:
        if reference_id is not None:
            log_upload_event(
                logging.ERROR,
                "Tesseract is not installed or not configured",
                reference_id=reference_id,
                stage="text_extraction",
                reason_code=REASON_OCR_UNAVAILABLE,
            )
        else:
            logger.error("Tesseract is not installed or not configured")
        raise exc
    except Exception as exc:
        if reference_id is not None:
            log_upload_event(
                logging.ERROR,
                "OCR failed while processing document pages",
                reference_id=reference_id,
                stage="text_extraction",
                reason_code=REASON_OCR_FAILED,
                exc_info=exc,
            )
        else:
            logger.exception("OCR failed while processing document pages")
        raise exc

    return "\n".join(text_parts).strip()
