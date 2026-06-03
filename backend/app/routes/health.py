import sqlite3

from fastapi import APIRouter, HTTPException

from app.database import check_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
def health_readiness() -> dict[str, str]:
    try:
        check_connection()
    except (ValueError, sqlite3.Error) as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {"status": "ok"}
