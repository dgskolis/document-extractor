import logging
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict, ValidationError

from app.config import settings
from app.exceptions import OpenAIConfigurationError, PatientExtractionError
from app.schemas.document import ExtractedPatientFields
from app.schemas.order import validate_date_of_birth

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = (
    "Extract the patient's first name, last name, and date of birth from this document text. "
    "Return ONLY a JSON object with keys: first_name, last_name, date_of_birth (YYYY-MM-DD format). "
    "If a field cannot be found, return null for that field."
)


class _RawExtractedPatientFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None


def _parse_date_of_birth(value: str | None) -> date | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        parsed = date.fromisoformat(stripped)
        return validate_date_of_birth(parsed)
    except ValueError:
        return None


def _truncate_document_text(document_text: str) -> str:
    max_chars = settings.max_document_text_chars
    if len(document_text) <= max_chars:
        return document_text
    logger.info(
        "Truncating document text for LLM extraction",
        extra={"original_length": len(document_text), "max_chars": max_chars},
    )
    return document_text[:max_chars]


def _normalize_extracted_fields(raw: _RawExtractedPatientFields) -> ExtractedPatientFields:
    try:
        return ExtractedPatientFields(
            first_name=raw.first_name,
            last_name=raw.last_name,
            date_of_birth=_parse_date_of_birth(raw.date_of_birth),
        )
    except ValidationError as exc:
        logger.warning("Extracted patient fields failed validation", exc_info=exc)
        raise PatientExtractionError("Patient field extraction failed") from exc


def _build_llm() -> ChatOpenAI:
    api_key = (settings.openai_api_key or "").strip()
    if not api_key:
        raise OpenAIConfigurationError("OpenAI API key not configured")

    return ChatOpenAI(
        api_key=api_key,
        model=settings.openai_model,
        temperature=0,
        timeout=settings.openai_timeout_seconds,
    )


def extract_patient_fields(document_text: str) -> ExtractedPatientFields:
    llm = _build_llm().with_structured_output(_RawExtractedPatientFields)
    truncated_text = _truncate_document_text(document_text)
    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=truncated_text),
    ]

    try:
        result = llm.invoke(messages)
    except ValidationError as exc:
        logger.warning("Structured extraction returned invalid patient fields", exc_info=exc)
        raise PatientExtractionError("Patient field extraction failed") from exc
    except Exception as exc:
        logger.exception("Patient field extraction failed")
        raise PatientExtractionError("Patient field extraction failed") from exc

    if not isinstance(result, _RawExtractedPatientFields):
        raise PatientExtractionError("Patient field extraction failed")

    return _normalize_extracted_fields(result)
