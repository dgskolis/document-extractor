from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.activity_log import ActivityLog

DEFAULT_LIST_LIMIT = 100


def create_activity_log(
    db: Session,
    *,
    method: str,
    path: str,
    status_code: int,
    ip_address: str,
    response_time_ms: float,
) -> ActivityLog:
    activity_log = ActivityLog(
        method=method,
        path=path,
        status_code=status_code,
        ip_address=ip_address,
        response_time_ms=response_time_ms,
    )
    db.add(activity_log)
    db.commit()
    return activity_log


def list_activity_logs(
    db: Session,
    *,
    limit: int = DEFAULT_LIST_LIMIT,
) -> tuple[list[ActivityLog], int]:
    total = db.scalar(select(func.count()).select_from(ActivityLog)) or 0
    logs = list(
        db.scalars(
            select(ActivityLog)
            .order_by(ActivityLog.timestamp.desc(), ActivityLog.id.desc())
            .limit(limit)
        )
    )
    return logs, total


def prune_activity_logs(db: Session, *, max_entries: int) -> int:
    if max_entries <= 0:
        return 0

    total = db.scalar(select(func.count()).select_from(ActivityLog)) or 0
    excess = total - max_entries
    if excess <= 0:
        return 0

    ids_to_delete = list(
        db.scalars(
            select(ActivityLog.id)
            .order_by(ActivityLog.timestamp.asc(), ActivityLog.id.asc())
            .limit(excess)
        )
    )
    if not ids_to_delete:
        return 0

    db.execute(delete(ActivityLog).where(ActivityLog.id.in_(ids_to_delete)))
    db.commit()
    return len(ids_to_delete)
