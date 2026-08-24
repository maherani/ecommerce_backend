"""Reconcile the Alembic schema with the current e-commerce models.

Revision ID: b8c2d1e4f6a7
Revises: aee86fd59c30
Create Date: 2026-08-24

The original database was stamped after several tables already existed.
This migration is intentionally idempotent for those installations while
also creating the complete schema in a fresh environment.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c2d1e4f6a7"
down_revision: Union[str, None] = "aee86fd59c30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    """Return whether a table contains a named column."""
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    """Create missing application tables and reconcile the User model."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "users", "is_superuser"):
        op.add_column(
            "users",
            sa.Column(
                "is_superuser",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        op.alter_column("users", "is_superuser", server_default=None)

    if not inspector.has_table("categories"):
        op.create_table(
            "categories",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.UniqueConstraint("name"),
        )
        op.create_index("ix_categories_id", "categories", ["id"], unique=False)
        op.create_index("ix_categories_name", "categories", ["name"], unique=False)

    if not inspector.has_table("products"):
        op.create_table(
            "products",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("price", sa.Float(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("category_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        )
        op.create_index("ix_products_id", "products", ["id"], unique=False)
        op.create_index("ix_products_title", "products", ["title"], unique=False)

    if not inspector.has_table("cart_items"):
        op.create_table(
            "cart_items",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
        op.create_index("ix_cart_items_id", "cart_items", ["id"], unique=False)

    if not inspector.has_table("orders"):
        op.create_table(
            "orders",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("total_price", sa.Float(), nullable=False),
            sa.Column("status", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        )
        op.create_index("ix_orders_id", "orders", ["id"], unique=False)

    if not inspector.has_table("order_items"):
        op.create_table(
            "order_items",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("product_id", sa.Integer(), nullable=False),
            sa.Column("quantity", sa.Integer(), nullable=False),
            sa.Column("unit_price", sa.Float(), nullable=False),
            sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
            sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
        )
        op.create_index("ix_order_items_id", "order_items", ["id"], unique=False)


def downgrade() -> None:
    """Revert the column addition without removing pre-existing business data."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Historical databases may have contained the business tables before this
    # reconciliation migration, so dropping them here could destroy user data.
    if inspector.has_table("users") and _has_column(inspector, "users", "is_superuser"):
        op.drop_column("users", "is_superuser")
