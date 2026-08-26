"""add payment events table

Revision ID: e124ed32b079
Revises: aea3438feb25
Create Date: 2026-08-26 04:40:00.690829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e124ed32b079'
down_revision: Union[str, None] = 'aea3438feb25'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["payment_id"],
            ["payments.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_payment_events_id"),
        "payment_events",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_payment_events_id"),
        table_name="payment_events",
    )
    op.drop_table("payment_events")

