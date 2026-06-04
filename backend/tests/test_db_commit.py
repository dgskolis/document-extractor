from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from app.db_commit import commit_with_retry, is_retryable_db_error


def _sqlite_locked_error() -> OperationalError:
    return OperationalError("commit", {}, Exception("database is locked"))


def test_is_retryable_db_error_true_for_sqlite_locked() -> None:
    assert is_retryable_db_error(_sqlite_locked_error())


def test_is_retryable_db_error_true_for_sqlite_busy() -> None:
    error = OperationalError("commit", {}, Exception("database is busy"))
    assert is_retryable_db_error(error)


def test_is_retryable_db_error_true_for_postgres_deadlock() -> None:
    error = OperationalError("commit", {}, Exception("deadlock detected"))
    assert is_retryable_db_error(error)


def test_is_retryable_db_error_false_for_generic_operational_error() -> None:
    error = OperationalError("commit", {}, Exception("no such table: missing"))
    assert not is_retryable_db_error(error)


def test_is_retryable_db_error_false_for_non_operational_error() -> None:
    assert not is_retryable_db_error(ValueError("not a db error"))


def test_commit_with_retry_succeeds_on_second_attempt() -> None:
    db = MagicMock()
    db.commit.side_effect = [_sqlite_locked_error(), None]

    with patch("app.db_commit.settings") as mock_settings:
        mock_settings.db_commit_max_retries = 3
        mock_settings.db_commit_retry_min_seconds = 0.01
        mock_settings.db_commit_retry_max_seconds = 0.02
        commit_with_retry(db)

    assert db.commit.call_count == 2
    db.rollback.assert_called_once()


def test_commit_with_retry_raises_after_exhausted_retries() -> None:
    db = MagicMock()
    db.commit.side_effect = _sqlite_locked_error()

    with patch("app.db_commit.settings") as mock_settings:
        mock_settings.db_commit_max_retries = 1
        mock_settings.db_commit_retry_min_seconds = 0.01
        mock_settings.db_commit_retry_max_seconds = 0.02
        with pytest.raises(OperationalError):
            commit_with_retry(db)

    assert db.commit.call_count == 2
    assert db.rollback.call_count == 2
