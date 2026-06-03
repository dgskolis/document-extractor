import asyncio
import logging
import time

from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database import SessionLocal
from app.services import activity_log_service

logger = logging.getLogger(__name__)

UNKNOWN_IP = "unknown"
MAX_PATH_LENGTH = 2048
INTERNAL_SERVER_ERROR_STATUS = 500


def _resolve_ip_address(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        if client_ip:
            return client_ip[:45]

    if request.client and request.client.host:
        return request.client.host
    return UNKNOWN_IP


def _resolve_request_path(request: Request) -> str:
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"
    return path[:MAX_PATH_LENGTH]


def _log_background_task_error(task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is not None:
        logger.exception("Background activity log task failed", exc_info=exc)


def _schedule_activity_log(
    *,
    method: str,
    path: str,
    status_code: int,
    ip_address: str,
    response_time_ms: float,
) -> None:
    task = asyncio.create_task(
        _persist_activity_log(
            method=method,
            path=path,
            status_code=status_code,
            ip_address=ip_address,
            response_time_ms=response_time_ms,
        )
    )
    task.add_done_callback(_log_background_task_error)


def _persist_activity_log_sync(
    *,
    method: str,
    path: str,
    status_code: int,
    ip_address: str,
    response_time_ms: float,
) -> None:
    db = SessionLocal()
    try:
        activity_log_service.create_activity_log(
            db,
            method=method,
            path=path,
            status_code=status_code,
            ip_address=ip_address,
            response_time_ms=response_time_ms,
        )
    except Exception:
        logger.exception(
            "Failed to persist activity log",
            extra={
                "method": method,
                "path": path,
                "status_code": status_code,
            },
        )
    finally:
        db.close()


async def _persist_activity_log(
    *,
    method: str,
    path: str,
    status_code: int,
    ip_address: str,
    response_time_ms: float,
) -> None:
    await run_in_threadpool(
        _persist_activity_log_sync,
        method=method,
        path=path,
        status_code=status_code,
        ip_address=ip_address,
        response_time_ms=response_time_ms,
    )


class ActivityLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        status_code = INTERNAL_SERVER_ERROR_STATUS
        response: Response | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = INTERNAL_SERVER_ERROR_STATUS
            raise
        finally:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            _schedule_activity_log(
                method=request.method,
                path=_resolve_request_path(request),
                status_code=status_code,
                ip_address=_resolve_ip_address(request),
                response_time_ms=elapsed_ms,
            )
