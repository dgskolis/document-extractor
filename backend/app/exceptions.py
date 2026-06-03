class UnsupportedMediaTypeError(Exception):
    """Raised when an uploaded file has an unsupported content type."""


class TextExtractionError(Exception):
    """Raised when text cannot be extracted from a document."""


class OpenAIConfigurationError(Exception):
    """Raised when OpenAI is not configured."""


class PatientExtractionError(Exception):
    """Raised when patient field extraction via LLM fails."""
