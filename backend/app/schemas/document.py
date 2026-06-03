from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.order import OrderResponse, validate_date_of_birth


class ExtractedPatientFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None

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
    extraction: ExtractedPatientFields


def is_extraction_complete(fields: ExtractedPatientFields) -> bool:
    return bool(fields.first_name and fields.last_name and fields.date_of_birth)


def build_partial_extraction_detail(fields: ExtractedPatientFields) -> dict[str, object]:
    return DocumentExtractionErrorDetail(
        message="Could not extract all required patient fields from document",
        extraction=fields,
    ).model_dump(mode="json")
