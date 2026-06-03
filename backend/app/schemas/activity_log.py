from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    method: str
    path: str
    status_code: int
    ip_address: str
    timestamp: datetime
    response_time_ms: float


class ActivityLogListResponse(BaseModel):
    items: list[ActivityLogResponse]
    total: int
    limit: int
