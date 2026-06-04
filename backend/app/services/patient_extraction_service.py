import logging
from collections.abc import Iterator
from datetime import date

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, PermissionDeniedError, RateLimitError
from pydantic import BaseModel, ConfigDict, ValidationError
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings
from app.exceptions import OpenAIConfigurationError, PatientExtractionError
from app.logging_context import log_upload_event
from app.schemas.document import ExtractedPatientFields
from app.schemas.order import validate_date_of_birth
from app.schemas.upload_errors import (
    REASON_LLM_EXTRACTION_FAILED,
    REASON_OPENAI_NOT_CONFIGURED,
)

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = (
    "Extract the patient's first name, last name, and date of birth from this document text. "
    "Return ONLY a JSON object with keys: first_name, last_name, date_of_birth (YYYY-MM-DD format). "
    "If a field cannot be found, return null for that field."
)

EXTRACTION_SYSTEM_PROMPT_TEMPLATE = """You are an information extraction system.

Task:
Extract the patient's identity information from OCR text obtained from a scanned medical document.

Fields to extract:
- first_name
- last_name
- date_of_birth

Extraction Rules:

1. Identify the PATIENT only.
   - Ignore physician names, provider names, facility names, insurance contacts, emergency contacts, parents, guardians, guarantors, witnesses, and signatories.
   - If multiple people are mentioned, prioritize the person explicitly labeled as:
     - Patient
     - Patient Name
     - Member
     - Subscriber (only if clearly the patient)
     - Client
     - Resident

2. Name extraction:
   - Extract only the patient's legal first and last names.
   - Remove titles, suffixes, and credentials such as:
     - Mr, Mrs, Ms, Miss, Dr
     - MD, DO, RN, NP, PA
     - Jr, Sr, II, III, IV
   - If a middle name or middle initial exists, ignore it.
   - If the full patient name is present but cannot be reliably split into first and last name, return null for the uncertain field.

3. Date of birth extraction:
   - Look for labels such as:
     - DOB
     - Date of Birth
     - Birth Date
     - D.O.B.
   - Convert the result to ISO format: YYYY-MM-DD.
   - Accept common date formats such as:
     - MM/DD/YYYY
     - MM-DD-YYYY
     - YYYY-MM-DD
     - Month DD, YYYY
   - If the date is ambiguous or cannot be confidently determined, return null.

4. OCR handling:
   - Be tolerant of OCR errors, extra whitespace, line breaks, punctuation issues, and character recognition mistakes.
   - Use nearby labels and context to determine the correct values.

5. Confidence:
   - Only extract values when reasonably confident they belong to the patient.
   - If a field cannot be confidently determined, return null.

Output Requirements:
- Return ONLY valid JSON.
- Do not include markdown.
- Do not include explanations.
- Do not include additional keys.

Required JSON schema:

{
  "first_name": string | null,
  "last_name": string | null,
  "date_of_birth": string | null
}
"""


class _RawExtractedPatientFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None


def _parse_date_of_birth(
    value: str | None,
    *,
    reference_id: str | None = None,
) -> date | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        parsed = date.fromisoformat(stripped)
        return validate_date_of_birth(parsed)
    except ValueError:
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Extracted date of birth failed validation",
                reference_id=reference_id,
                stage="patient_extraction",
                reason_code="invalid_dob",
            )
        return None


def _truncate_document_text(document_text: str, *, reference_id: str | None = None) -> str:
    max_chars = settings.max_document_text_chars
    if len(document_text) <= max_chars:
        return document_text
    log_upload_event(
        logging.INFO,
        "Truncating document text for LLM extraction",
        reference_id=reference_id or "unknown",
        stage="patient_extraction",
        reason_code="text_truncated",
        text_length=len(document_text),
    )
    return document_text[:max_chars]


def _normalize_extracted_fields(
    raw: _RawExtractedPatientFields,
    *,
    reference_id: str | None = None,
) -> ExtractedPatientFields:
    try:
        return ExtractedPatientFields(
            first_name=raw.first_name,
            last_name=raw.last_name,
            date_of_birth=_parse_date_of_birth(raw.date_of_birth, reference_id=reference_id),
        )
    except ValidationError as exc:
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Extracted patient fields failed validation",
                reference_id=reference_id,
                stage="patient_extraction",
                reason_code=REASON_LLM_EXTRACTION_FAILED,
                exc_info=exc,
            )
        else:
            logger.warning("Extracted patient fields failed validation", exc_info=exc)
        raise PatientExtractionError("Patient field extraction failed") from exc


def _build_llm(*, reference_id: str | None = None) -> ChatOpenAI:
    api_key = (settings.openai_api_key or "").strip()
    if not api_key:
        if reference_id is not None:
            log_upload_event(
                logging.ERROR,
                "OpenAI API key is not configured",
                reference_id=reference_id,
                stage="patient_extraction",
                reason_code=REASON_OPENAI_NOT_CONFIGURED,
            )
        raise OpenAIConfigurationError("OpenAI API key not configured")

    return ChatOpenAI(
        api_key=api_key,
        model=settings.openai_model,
        temperature=0,
        timeout=settings.openai_timeout_seconds,
        max_retries=0,
    )


def _iter_exception_chain(exc: BaseException) -> Iterator[BaseException]:
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        yield current
        current = current.__cause__ or current.__context__


def _is_openai_configuration_error(exc: BaseException) -> bool:
    for err in _iter_exception_chain(exc):
        if isinstance(err, (AuthenticationError, PermissionDeniedError)):
            return True
        if isinstance(err, APIStatusError) and err.status_code in {401, 403}:
            return True
    return False


def _is_retryable_openai_error(exc: BaseException) -> bool:
    if _is_openai_configuration_error(exc):
        return False
    for err in _iter_exception_chain(exc):
        if isinstance(err, (APITimeoutError, APIConnectionError, RateLimitError)):
            return True
        if isinstance(err, APIStatusError) and (err.status_code == 429 or err.status_code >= 500):
            return True
    return False


def _invoke_structured_llm(llm, messages: list) -> _RawExtractedPatientFields:
    retrying = Retrying(
        retry=retry_if_exception(_is_retryable_openai_error),
        stop=stop_after_attempt(settings.openai_max_retries + 1),
        wait=wait_exponential(
            multiplier=1,
            min=settings.openai_retry_min_seconds,
            max=settings.openai_retry_max_seconds,
        ),
        reraise=True,
    )
    for attempt in retrying:
        with attempt:
            return llm.invoke(messages)
    raise PatientExtractionError("Patient field extraction failed")


def extract_patient_fields(
    document_text: str,
    *,
    reference_id: str | None = None,
) -> ExtractedPatientFields:
    llm = _build_llm(reference_id=reference_id).with_structured_output(_RawExtractedPatientFields)
    truncated_text = _truncate_document_text(document_text, reference_id=reference_id)
    messages = [
        SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
        HumanMessage(content=truncated_text),
    ]

    try:
        result = _invoke_structured_llm(llm, messages)
    except ValidationError as exc:
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Structured extraction returned invalid patient fields",
                reference_id=reference_id,
                stage="patient_extraction",
                reason_code=REASON_LLM_EXTRACTION_FAILED,
                exc_info=exc,
            )
        else:
            logger.warning("Structured extraction returned invalid patient fields", exc_info=exc)
        raise PatientExtractionError("Patient field extraction failed") from exc
    except Exception as exc:
        if _is_openai_configuration_error(exc):
            if reference_id is not None:
                log_upload_event(
                    logging.ERROR,
                    "OpenAI authentication failed",
                    reference_id=reference_id,
                    stage="patient_extraction",
                    reason_code=REASON_OPENAI_NOT_CONFIGURED,
                    text_length=len(truncated_text),
                    exc_info=exc,
                )
            raise OpenAIConfigurationError("OpenAI API key not configured or invalid") from exc
        if reference_id is not None:
            log_upload_event(
                logging.ERROR,
                "Patient field extraction failed",
                reference_id=reference_id,
                stage="patient_extraction",
                reason_code=REASON_LLM_EXTRACTION_FAILED,
                text_length=len(truncated_text),
                exc_info=exc,
            )
        else:
            logger.exception("Patient field extraction failed")
        raise PatientExtractionError("Patient field extraction failed") from exc

    if not isinstance(result, _RawExtractedPatientFields):
        if reference_id is not None:
            log_upload_event(
                logging.ERROR,
                "Structured extraction returned unexpected result type",
                reference_id=reference_id,
                stage="patient_extraction",
                reason_code=REASON_LLM_EXTRACTION_FAILED,
            )
        raise PatientExtractionError("Patient field extraction failed")

    return _normalize_extracted_fields(result, reference_id=reference_id)
