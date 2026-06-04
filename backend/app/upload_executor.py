import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import ParamSpec, TypeVar

from app.config import settings

P = ParamSpec("P")
T = TypeVar("T")

_upload_executor: ThreadPoolExecutor | None = None


def get_upload_executor() -> ThreadPoolExecutor:
    global _upload_executor
    if _upload_executor is None:
        _upload_executor = ThreadPoolExecutor(
            max_workers=settings.upload_max_workers,
            thread_name_prefix="upload",
        )
    return _upload_executor


async def run_upload_task(func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(get_upload_executor(), lambda: func(*args, **kwargs))


def shutdown_upload_executor(*, wait: bool = False) -> None:
    global _upload_executor
    if _upload_executor is None:
        return
    _upload_executor.shutdown(wait=wait, cancel_futures=not wait)
    _upload_executor = None
