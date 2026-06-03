from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.order import OrderCreate, OrderStatus, OrderUpdate


def test_order_create_rejects_future_dob() -> None:
    future_dob = date.today() + timedelta(days=1)
    with pytest.raises(ValidationError, match="date_of_birth cannot be in the future"):
        OrderCreate(
            patient_first_name="Jane",
            patient_last_name="Doe",
            date_of_birth=future_dob,
        )


def test_order_create_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(
            patient_first_name="Jane",
            patient_last_name="Doe",
            date_of_birth=date(1990, 5, 15),
            status="completed",
        )


def test_order_update_rejects_null_fields() -> None:
    with pytest.raises(ValidationError, match="patient_first_name cannot be set to null"):
        OrderUpdate.model_validate({"patient_first_name": None})


def test_order_update_accepts_partial_payload() -> None:
    update = OrderUpdate.model_validate({"status": "completed"})
    assert update.status == OrderStatus.COMPLETED
    assert update.patient_first_name is None
