"""add was_synced flag to stream_offers

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "stream_offers",
        sa.Column("was_synced", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("stream_offers", "was_synced")
