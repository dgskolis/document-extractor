import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order import Order, utc_now
from app.schemas.order import OrderCreate, OrderStatus, OrderUpdate


def get_order(db: Session, order_id: uuid.UUID) -> Order | None:
    return db.get(Order, order_id)


def list_orders(db: Session, *, limit: int, offset: int) -> tuple[list[Order], int]:
    listed_orders_filter = Order.status != OrderStatus.PENDING.value
    total = db.scalar(select(func.count()).select_from(Order).where(listed_orders_filter)) or 0
    orders = list(
        db.scalars(
            select(Order)
            .where(listed_orders_filter)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return orders, total


def create_order(db: Session, order_in: OrderCreate) -> Order:
    order = Order(**order_in.model_dump(), status=OrderStatus.IN_PROGRESS.value)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_order(db: Session, order: Order, order_in: OrderUpdate) -> Order:
    update_data = order_in.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in update_data.items():
        if field == "status":
            setattr(order, field, value.value if isinstance(value, OrderStatus) else value)
        else:
            setattr(order, field, value)
    order.updated_at = utc_now()
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: Order) -> None:
    db.delete(order)
    db.commit()
