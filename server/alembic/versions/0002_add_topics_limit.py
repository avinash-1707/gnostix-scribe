"""add topics_limit to users

Revision ID: 0002_add_topics_limit
Revises: 0001_initial
Create Date: 2026-05-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_add_topics_limit"
down_revision: str | None = "0001_initial"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "topics_limit",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "topics_limit")
