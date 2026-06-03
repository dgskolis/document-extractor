import logging
from datetime import date

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.logging_context import log_upload_event
from app.schemas.order import OrderCreate, validate_date_of_birth
from app.schemas.upload_errors import (
    GENERIC_UPLOAD_ERROR,
    REASON_EXTRACTED_FIELDS_VALIDATION_FAILED,
    REASON_MISSING_REQUIRED_FIELDS,
)


class ExtractedPatientFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            return None
        stripped = value.strip()
        return stripped or None

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, value: date | None) -> date | None:
        if value is None:
            return value
        return validate_date_of_birth(value)


class DocumentUploadResponse(BaseModel):
    extraction: ExtractedPatientFields


class DocumentExtractionErrorDetail(BaseModel):
    message: str
    reference_id: str | None = None
    extraction: ExtractedPatientFields | None = None


def is_extraction_complete(fields: ExtractedPatientFields) -> bool:
    return bool(fields.first_name and fields.last_name and fields.date_of_birth)


def build_error_detail(
    message: str,
    *,
    reference_id: str | None = None,
    extraction: ExtractedPatientFields | None = None,
) -> dict[str, object]:
    detail = DocumentExtractionErrorDetail(
        message=message,
        reference_id=reference_id,
        extraction=extraction,
    )
    payload = detail.model_dump(mode="json")
    if reference_id is None:
        payload.pop("reference_id", None)
    if extraction is None:
        payload.pop("extraction", None)
    return payload


def build_upload_error_detail(
    *,
    reference_id: str,
    extraction: ExtractedPatientFields | None = None,
) -> dict[str, object]:
    return build_error_detail(
        GENERIC_UPLOAD_ERROR,
        reference_id=reference_id,
        extraction=extraction,
    )


def build_partial_extraction_detail(
    fields: ExtractedPatientFields,
    *,
    reference_id: str,
) -> dict[str, object]:
    return build_upload_error_detail(reference_id=reference_id, extraction=fields)


def build_text_extraction_error_detail(*, reference_id: str) -> dict[str, object]:
    return build_upload_error_detail(reference_id=reference_id)


def _missing_field_names(fields: ExtractedPatientFields) -> list[str]:
    missing: list[str] = []
    if fields.first_name is None:
        missing.append("first_name")
    if fields.last_name is None:
        missing.append("last_name")
    if fields.date_of_birth is None:
        missing.append("date_of_birth")
    return missing


def build_order_create_from_extraction(
    fields: ExtractedPatientFields,
    *,
    reference_id: str | None = None,
) -> OrderCreate | None:
    if fields.first_name is None or fields.last_name is None or fields.date_of_birth is None:
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Upload order creation skipped due to missing extracted fields",
                reference_id=reference_id,
                stage="order_validation",
                reason_code=REASON_MISSING_REQUIRED_FIELDS,
                validation_fields=_missing_field_names(fields),
            )
        return None

    try:
        return OrderCreate(
            patient_first_name=fields.first_name,
            patient_last_name=fields.last_name,
            date_of_birth=fields.date_of_birth,
        )
    except ValidationError as exc:
        validation_fields = [
            ".".join(str(part) for part in error.get("loc", ()))
            for error in exc.errors()
        ]
        if reference_id is not None:
            log_upload_event(
                logging.WARNING,
                "Upload order creation failed extracted field validation",
                reference_id=reference_id,
                stage="order_validation",
                reason_code=REASON_EXTRACTED_FIELDS_VALIDATION_FAILED,
                validation_fields=validation_fields or None,
            )
        return None
