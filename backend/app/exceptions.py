class UnsupportedMediaTypeError(Exception):
    """Raised when an uploaded file has an unsupported content type."""


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the configured size limit."""


class TextExtractionError(Exception):
    """Raised when text cannot be extracted from a document."""


class DocumentPageLimitExceededError(TextExtractionError):
    """Raised when a document exceeds the configured page limit."""


class DocumentProcessingTimeoutError(TextExtractionError):
    """Raised when document text/OCR processing exceeds the configured deadline."""


class OpenAIConfigurationError(Exception):
    """Raised when OpenAI is not configured."""


class PatientExtractionError(Exception):
    """Raised when patient field extraction via LLM fails."""
