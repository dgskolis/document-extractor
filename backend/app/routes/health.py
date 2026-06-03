from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.database import check_connection, check_schema_ready

router = APIRouter(tags=["health"])


@router.get("/health")
def health_liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_readiness() -> dict[str, str]:
    try:
        check_connection()
        check_schema_ready()
    except (ValueError, RuntimeError, SQLAlchemyError) as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}
