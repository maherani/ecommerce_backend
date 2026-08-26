"""add payment webhook event id

Revision ID: e3e6a6bd5e42
Revises: 2a408bf8badb
Create Date: 2026-08-26 08:38:36.173809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3e6a6bd5e42'
down_revision: Union[str, None] = '2a408bf8badb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
def upgrade() -> None:
    op.add_column(
        'payment_events',
        sa.Column('event_id', sa.String(), nullable=True)
    )

    op.create_unique_constraint(
        'uq_payment_events_event_id',
        'payment_events',
        ['event_id']
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_payment_events_event_id',
        'payment_events',
        type_='unique'
    )

    op.drop_column(
        'payment_events',
        'event_id'
    )
