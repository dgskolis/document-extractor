import hmac
import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

import app.config
from app.database import get_db
from app.models.order import Order
from app.services import order_service


def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    configured_key = app.config.settings.api_key
    if not configured_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

    provided_key = (x_api_key or "").strip()
    if not hmac.compare_digest(provided_key, configured_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")


def get_order_or_404(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Order:
    order = order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
