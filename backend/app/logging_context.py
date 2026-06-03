import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


def generate_reference_id() -> str:
    return str(uuid.uuid4())


def log_upload_event(
    level: int,
    event: str,
    *,
    reference_id: str,
    stage: str,
    reason_code: str,
    order_id: str | None = None,
    content_type: str | None = None,
    content_length: int | None = None,
    text_length: int | None = None,
    validation_fields: list[str] | None = None,
    exc_info: Any = None,
) -> None:
    extra: dict[str, Any] = {
        "reference_id": reference_id,
        "stage": stage,
        "reason_code": reason_code,
    }
    if order_id is not None:
        extra["order_id"] = order_id
    if content_type is not None:
        extra["content_type"] = content_type
    if content_length is not None:
        extra["content_length"] = content_length
    if text_length is not None:
        extra["text_length"] = text_length
    if validation_fields is not None:
        extra["validation_fields"] = validation_fields

    message_parts = [
        event,
        f"reference_id={reference_id}",
        f"stage={stage}",
        f"reason_code={reason_code}",
    ]
    if order_id is not None:
        message_parts.append(f"order_id={order_id}")
    if content_type is not None:
        message_parts.append(f"content_type={content_type}")
    if content_length is not None:
        message_parts.append(f"content_length={content_length}")
    if text_length is not None:
        message_parts.append(f"text_length={text_length}")
    if validation_fields is not None:
        message_parts.append(f"validation_fields={','.join(validation_fields)}")

    logger.log(level, " ".join(message_parts), extra=extra, exc_info=exc_info)
