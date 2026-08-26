"""add payment idempotency key

Revision ID: aea3438feb25
Revises: cff58edd10a9
Create Date: 2026-08-26 04:06:54.399436

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aea3438feb25'
down_revision: Union[str, None] = 'cff58edd10a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'payments',
        sa.Column('idempotency_key', sa.String(), nullable=True)
    )

    op.create_unique_constraint(
        'uq_payments_idempotency_key',
        'payments',
        ['idempotency_key']
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_payments_idempotency_key',
        'payments',
        type_='unique'
    )

    op.drop_column(
        'payments',
        'idempotency_key'
    )
