from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator


class OrderStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def validate_date_of_birth(value: date) -> date:
    if value > date.today():
        raise ValueError("date_of_birth cannot be in the future")
    return value


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    patient_first_name: str = Field(min_length=1, max_length=255)
    patient_last_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date

    @field_validator("patient_first_name", "patient_last_name")
    @classmethod
    def names_not_empty(cls, value: str, info: ValidationInfo) -> str:
        if not value:
            field_name = info.field_name or "name"
            raise ValueError(f"{field_name} cannot be empty")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, value: date) -> date:
        return validate_date_of_birth(value)


class OrderUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    patient_first_name: str | None = Field(default=None, min_length=1, max_length=255)
    patient_last_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    status: OrderStatus | None = None

    @field_validator("patient_first_name", "patient_last_name")
    @classmethod
    def names_not_empty(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return value
        if not value:
            field_name = info.field_name or "name"
            raise ValueError(f"{field_name} cannot be empty")
        return value

    @model_validator(mode="before")
    @classmethod
    def reject_null_fields(cls, data: object) -> object:
        if isinstance(data, dict):
            for key, value in data.items():
                if value is None:
                    raise ValueError(f"{key} cannot be set to null")
        return data

    @field_validator("date_of_birth")
    @classmethod
    def dob_not_in_future(cls, value: date | None) -> date | None:
        if value is None:
            return value
        return validate_date_of_birth(value)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_first_name: str
    patient_last_name: str
    date_of_birth: date
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderResponse]
    total: int
    limit: int
    offset: int
