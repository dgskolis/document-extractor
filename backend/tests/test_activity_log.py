import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.middleware.activity_log import ActivityLogMiddleware, _resolve_ip_address
from app.models.activity_log import ActivityLog
from app.models.order import utc_now
from app.services import activity_log_service
from starlette.requests import Request


def _wait_for_logs(db_session: Session, minimum_count: int, timeout_seconds: float = 1.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        db_session.rollback()
        count = db_session.scalar(select(func.count()).select_from(ActivityLog)) or 0
        if count >= minimum_count:
            return
        time.sleep(0.01)
    pytest.fail(f"Expected at least {minimum_count} activity logs within {timeout_seconds}s")


def test_middleware_persists_activity_log(client: TestClient, db_session: Session) -> None:
    response = client.get("/health")
    assert response.status_code == 200

    _wait_for_logs(db_session, 1)
    log = db_session.scalar(select(ActivityLog).order_by(ActivityLog.timestamp.desc()))
    assert log is not None
    assert log.method == "GET"
    assert log.path == "/health"
    assert log.status_code == 200
    assert log.ip_address == "testclient"
    assert log.response_time_ms >= 0


def test_middleware_uses_x_forwarded_for_client_ip(client: TestClient, db_session: Session) -> None:
    response = client.get("/health", headers={"X-Forwarded-For": "203.0.113.50, 10.0.0.1"})
    assert response.status_code == 200

    _wait_for_logs(db_session, 1)
    log = db_session.scalar(select(ActivityLog).order_by(ActivityLog.timestamp.desc()))
    assert log is not None
    assert log.ip_address == "203.0.113.50"


def test_resolve_ip_address_prefers_x_forwarded_for() -> None:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "query_string": b"",
        "headers": [(b"x-forwarded-for", b"203.0.113.50, 10.0.0.1")],
        "client": ("127.0.0.1", 5000),
    }
    request = Request(scope)
    assert _resolve_ip_address(request) == "203.0.113.50"


def test_list_activity_logs_endpoint(client: TestClient, db_session: Session) -> None:
    client.get("/health")
    client.get("/health/ready")
    client.get("/api/v1/orders/", params={"limit": 2, "offset": 1})
    _wait_for_logs(db_session, 3)

    response = client.get("/api/v1/logs/")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 100
    assert data["total"] >= 3
    assert len(data["items"]) >= 3
    assert data["items"][0]["timestamp"] >= data["items"][1]["timestamp"]

    first_item = data["items"][0]
    assert uuid.UUID(first_item["id"])
    assert first_item["method"]
    assert first_item["path"]
    assert isinstance(first_item["status_code"], int)
    assert first_item["ip_address"]
    assert isinstance(first_item["response_time_ms"], float)

    query_log = db_session.scalar(
        select(ActivityLog).where(ActivityLog.path == "/api/v1/orders/?limit=2&offset=1")
    )
    assert query_log is not None


def test_list_activity_logs_caps_at_100(db_session: Session) -> None:
    base_time = utc_now()
    for index in range(105):
        db_session.add(
            ActivityLog(
                method="GET",
                path=f"/path-{index}",
                status_code=200,
                ip_address="127.0.0.1",
                timestamp=base_time + timedelta(seconds=index),
                response_time_ms=1.0,
            )
        )
    db_session.commit()

    logs, total = activity_log_service.list_activity_logs(db_session, limit=100)
    assert total == 105
    assert len(logs) == 100
    assert logs[0].path == "/path-104"
    assert logs[-1].path == "/path-5"


def test_list_activity_logs_service_ordering(db_session: Session) -> None:
    older = ActivityLog(
        method="GET",
        path="/older",
        status_code=200,
        ip_address="127.0.0.1",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        response_time_ms=2.5,
    )
    newer = ActivityLog(
        method="POST",
        path="/newer",
        status_code=201,
        ip_address="127.0.0.1",
        timestamp=datetime(2024, 6, 1, tzinfo=timezone.utc),
        response_time_ms=3.5,
    )
    db_session.add_all([older, newer])
    db_session.commit()

    logs, total = activity_log_service.list_activity_logs(db_session, limit=100)
    assert total == 2
    assert [log.path for log in logs] == ["/newer", "/older"]


@patch("app.middleware.activity_log._persist_activity_log_sync")
def test_middleware_failure_does_not_break_response(
    mock_persist_sync,
    client: TestClient,
) -> None:
    mock_persist_sync.side_effect = RuntimeError("database unavailable")

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_middleware_logs_http_error_status(client: TestClient, db_session: Session) -> None:
    missing_order_id = uuid.uuid4()
    response = client.get(f"/api/v1/orders/{missing_order_id}")
    assert response.status_code == 404

    _wait_for_logs(db_session, 1)
    log = db_session.scalar(
        select(ActivityLog)
        .where(ActivityLog.path == f"/api/v1/orders/{missing_order_id}")
        .order_by(ActivityLog.timestamp.desc())
    )
    assert log is not None
    assert log.method == "GET"
    assert log.status_code == 404


def test_list_activity_logs_endpoint_caps_at_100(client: TestClient, db_session: Session) -> None:
    base_time = utc_now()
    for index in range(105):
        db_session.add(
            ActivityLog(
                method="GET",
                path=f"/seed-{index}",
                status_code=200,
                ip_address="127.0.0.1",
                timestamp=base_time + timedelta(seconds=index),
                response_time_ms=1.0,
            )
        )
    db_session.commit()

    response = client.get("/api/v1/logs/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 105
    assert data["limit"] == 100
    assert len(data["items"]) == 100


def test_list_activity_logs_tie_breaks_on_id(db_session: Session) -> None:
    shared_timestamp = datetime(2024, 1, 1, tzinfo=timezone.utc)
    first = ActivityLog(
        method="GET",
        path="/first",
        status_code=200,
        ip_address="127.0.0.1",
        timestamp=shared_timestamp,
        response_time_ms=1.0,
    )
    second = ActivityLog(
        method="GET",
        path="/second",
        status_code=200,
        ip_address="127.0.0.1",
        timestamp=shared_timestamp,
        response_time_ms=1.0,
    )
    db_session.add_all([first, second])
    db_session.commit()
    db_session.refresh(first)
    db_session.refresh(second)

    logs, total = activity_log_service.list_activity_logs(db_session, limit=100)
    assert total == 2
    assert [log.id for log in logs] == sorted([first.id, second.id], reverse=True)


def test_prune_activity_logs(db_session: Session) -> None:
    base_time = utc_now()
    for index in range(5):
        db_session.add(
            ActivityLog(
                method="GET",
                path=f"/path-{index}",
                status_code=200,
                ip_address="127.0.0.1",
                timestamp=base_time + timedelta(seconds=index),
                response_time_ms=1.0,
            )
        )
    db_session.commit()

    deleted = activity_log_service.prune_activity_logs(db_session, max_entries=3)
    assert deleted == 2
    remaining = db_session.scalar(select(func.count()).select_from(ActivityLog)) or 0
    assert remaining == 3

    oldest_remaining = db_session.scalar(
        select(ActivityLog.path).order_by(ActivityLog.timestamp.asc(), ActivityLog.id.asc())
    )
    assert oldest_remaining == "/path-2"


@pytest.mark.anyio
async def test_middleware_logs_when_call_next_raises() -> None:
    middleware = ActivityLogMiddleware(app=AsyncMock())
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/broken",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 5000),
    }
    request = Request(scope)

    with patch("app.middleware.activity_log._schedule_activity_log") as mock_schedule:
        call_next = AsyncMock(side_effect=RuntimeError("handler failed"))
        with pytest.raises(RuntimeError, match="handler failed"):
            await middleware.dispatch(request, call_next)

    mock_schedule.assert_called_once()
    assert mock_schedule.call_args.kwargs["status_code"] == 500
    assert mock_schedule.call_args.kwargs["path"] == "/broken"
    assert mock_schedule.call_args.kwargs["method"] == "GET"
