from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_order_or_404
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse, OrderUpdate
from app.services import order_service

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

DEFAULT_LIST_LIMIT = 100
MAX_LIST_LIMIT = 1000


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)) -> OrderResponse:
    return order_service.create_order(db, order_in)


@router.get("/", response_model=OrderListResponse)
def list_orders(
    db: Session = Depends(get_db),
    limit: int = Query(default=DEFAULT_LIST_LIMIT, ge=1, le=MAX_LIST_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> OrderListResponse:
    orders, total = order_service.list_orders(db, limit=limit, offset=offset)
    return OrderListResponse(items=orders, total=total, limit=limit, offset=offset)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order: Order = Depends(get_order_or_404)) -> OrderResponse:
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_in: OrderUpdate,
    order: Order = Depends(get_order_or_404),
    db: Session = Depends(get_db),
) -> OrderResponse:
    return order_service.update_order(db, order, order_in)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(
    order: Order = Depends(get_order_or_404),
    db: Session = Depends(get_db),
) -> None:
    order_service.delete_order(db, order)
