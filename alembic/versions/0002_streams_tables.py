"""create streams and stream_offers tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17

"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "streams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("keitaro_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=True),
        sa.Column("schema", sa.String(length=32), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=True),
        sa.Column("dirty", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("synced_offers", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_streams_keitaro_id", "streams", ["keitaro_id"], unique=True)
    op.create_index("ix_streams_campaign_id", "streams", ["campaign_id"])

    op.create_table(
        "stream_offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "stream_id",
            sa.Integer(),
            sa.ForeignKey("streams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("offer_name", sa.String(length=255), nullable=True),
        sa.Column("share", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pinned", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
    )
    op.create_index("ix_stream_offers_stream_id", "stream_offers", ["stream_id"])


def downgrade() -> None:
    op.drop_table("stream_offers")
    op.drop_table("streams")
