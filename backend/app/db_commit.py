from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings


def _error_message(exc: BaseException) -> str:
    if isinstance(exc, OperationalError):
        origin = exc.orig
        if origin is not None:
            return str(origin).lower()
    return str(exc).lower()


def is_retryable_db_error(exc: BaseException) -> bool:
    if not isinstance(exc, OperationalError):
        return False
    message = _error_message(exc)
    sqlite_locked = "database is locked" in message or "database is busy" in message
    postgres_transient = "deadlock detected" in message or "could not serialize access" in message
    return sqlite_locked or postgres_transient


def commit_with_retry(db: Session) -> None:
    retrying = Retrying(
        retry=retry_if_exception(is_retryable_db_error),
        stop=stop_after_attempt(settings.db_commit_max_retries + 1),
        wait=wait_exponential(
            multiplier=1,
            min=settings.db_commit_retry_min_seconds,
            max=settings.db_commit_retry_max_seconds,
        ),
        reraise=True,
    )
    for attempt in retrying:
        with attempt:
            try:
                db.commit()
            except OperationalError:
                db.rollback()
                raise
