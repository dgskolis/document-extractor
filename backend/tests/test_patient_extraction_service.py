from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, AuthenticationError, RateLimitError
from pydantic import ValidationError

from app.exceptions import OpenAIConfigurationError, PatientExtractionError
from app.services.patient_extraction_service import (
    _RawExtractedPatientFields,
    _invoke_structured_llm,
    _is_openai_configuration_error,
    _is_retryable_openai_error,
    extract_patient_fields,
)


def test_is_openai_configuration_error_detects_authentication_error() -> None:
    assert _is_openai_configuration_error(
        AuthenticationError("invalid key", response=MagicMock(), body=None),
    )


def test_is_retryable_openai_error_detects_rate_limit() -> None:
    assert _is_retryable_openai_error(
        RateLimitError("rate limited", response=MagicMock(), body=None),
    )


def test_is_retryable_openai_error_rejects_authentication_error() -> None:
    assert not _is_retryable_openai_error(
        AuthenticationError("invalid key", response=MagicMock(), body=None),
    )


@patch("app.services.patient_extraction_service._build_llm")
@patch("app.services.patient_extraction_service._invoke_structured_llm")
def test_extract_patient_fields_maps_authentication_error_to_configuration_error(
    mock_invoke,
    mock_build_llm,
) -> None:
    mock_build_llm.return_value.with_structured_output.return_value = MagicMock()
    mock_invoke.side_effect = AuthenticationError("invalid key", response=MagicMock(), body=None)

    with pytest.raises(OpenAIConfigurationError, match="not configured or invalid"):
        extract_patient_fields("Patient: Jane Doe", reference_id="ref-auth")


def _connection_error() -> APIConnectionError:
    return APIConnectionError(message="temporary", request=MagicMock())


def test_invoke_structured_llm_retries_then_succeeds() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = [
        _connection_error(),
        _RawExtractedPatientFields(
            first_name="Jane",
            last_name="Doe",
            date_of_birth="1990-05-15",
        ),
    ]

    with patch("app.services.patient_extraction_service.settings") as mock_settings:
        mock_settings.openai_max_retries = 2
        mock_settings.openai_retry_min_seconds = 0.01
        mock_settings.openai_retry_max_seconds = 0.02
        result = _invoke_structured_llm(mock_llm, [])

    assert result.first_name == "Jane"
    assert mock_llm.invoke.call_count == 2


def test_invoke_structured_llm_raises_after_exhausted_retries() -> None:
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = _connection_error()

    with patch("app.services.patient_extraction_service.settings") as mock_settings:
        mock_settings.openai_max_retries = 1
        mock_settings.openai_retry_min_seconds = 0.01
        mock_settings.openai_retry_max_seconds = 0.02
        with pytest.raises(APIConnectionError):
            _invoke_structured_llm(mock_llm, [])

    assert mock_llm.invoke.call_count == 2


@patch("app.services.patient_extraction_service._build_llm")
def test_extract_patient_fields_maps_validation_error_to_patient_extraction_error(
    mock_build_llm,
) -> None:
    mock_llm = mock_build_llm.return_value
    mock_structured = mock_llm.with_structured_output.return_value
    mock_structured.invoke.side_effect = ValidationError.from_exception_data(
        "RawExtractedPatientFields",
        [],
    )

    with pytest.raises(PatientExtractionError, match="Patient field extraction failed"):
        extract_patient_fields("Patient: Jane Doe")


@patch("app.services.patient_extraction_service._build_llm")
def test_extract_patient_fields_returns_normalized_fields(mock_build_llm) -> None:
    mock_llm = mock_build_llm.return_value
    mock_structured = mock_llm.with_structured_output.return_value
    mock_structured.invoke.return_value = _RawExtractedPatientFields(
        first_name="Jane",
        last_name="Doe",
        date_of_birth="1990-05-15",
    )

    result = extract_patient_fields("Patient: Jane Doe, DOB 1990-05-15")

    assert result.first_name == "Jane"
    assert result.last_name == "Doe"
    assert result.date_of_birth == date(1990, 5, 15)
