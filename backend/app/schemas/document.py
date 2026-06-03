from datetime import date

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.schemas.order import OrderCreate, OrderResponse, validate_date_of_birth


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
    order: OrderResponse


class DocumentExtractionErrorDetail(BaseModel):
    message: str
    extraction: ExtractedPatientFields | None = None


def is_extraction_complete(fields: ExtractedPatientFields) -> bool:
    return bool(fields.first_name and fields.last_name and fields.date_of_birth)


def build_error_detail(
    message: str,
    *,
    extraction: ExtractedPatientFields | None = None,
) -> dict[str, object]:
    detail = DocumentExtractionErrorDetail(message=message, extraction=extraction)
    payload = detail.model_dump(mode="json")
    if extraction is None:
        payload.pop("extraction", None)
    return payload


def build_partial_extraction_detail(fields: ExtractedPatientFields) -> dict[str, object]:
    return build_error_detail(
        "Could not extract all required patient fields from document",
        extraction=fields,
    )


def build_text_extraction_error_detail(
    message: str = "Unable to extract text from document",
) -> dict[str, object]:
    return build_error_detail(message)


def build_order_create_from_extraction(fields: ExtractedPatientFields) -> OrderCreate | None:
    if fields.first_name is None or fields.last_name is None or fields.date_of_birth is None:
        return None

    try:
        return OrderCreate(
            patient_first_name=fields.first_name,
            patient_last_name=fields.last_name,
            date_of_birth=fields.date_of_birth,
        )
    except ValidationError:
        return None
