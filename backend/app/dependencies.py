import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.order import Order
from app.services import order_service


def get_order_or_404(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Order:
    order = order_service.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order
