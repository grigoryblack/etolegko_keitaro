"""create keitaro_sessions table

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keitaro_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("base_url", sa.String(length=255), nullable=False),
        sa.Column("cookie", sa.String(length=2048), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("keitaro_sessions")
