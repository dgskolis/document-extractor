"""add orders created_at index

Revision ID: 002
Revises: 001
Create Date: 2026-06-03

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = "ix_orders_created_at"


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    inspector = inspect(bind)
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    if not _index_exists(bind, "orders", INDEX_NAME):
        op.create_index(INDEX_NAME, "orders", ["created_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if _index_exists(bind, "orders", INDEX_NAME):
        op.drop_index(INDEX_NAME, table_name="orders")
