from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import verify_api_key
from app.schemas.activity_log import ActivityLogListResponse
from app.services import activity_log_service

# Intended for admin use only; protected by the shared API key.
router = APIRouter(
    prefix="/api/v1/logs",
    tags=["logs"],
    dependencies=[Depends(verify_api_key)],
)

LOG_LIST_LIMIT = 100


@router.get("/", response_model=ActivityLogListResponse)
def list_logs(db: Session = Depends(get_db)) -> ActivityLogListResponse:
    logs, total = activity_log_service.list_activity_logs(db, limit=LOG_LIST_LIMIT)
    return ActivityLogListResponse(items=logs, total=total, limit=LOG_LIST_LIMIT)
