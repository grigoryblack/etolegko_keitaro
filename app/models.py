from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class CampaignRecord(Base):
    """Local record of a campaign created through this app."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    alias: Mapped[str] = mapped_column(String(255))
    geo: Mapped[str] = mapped_column(String(8))
    domain_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    offer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Stream(Base):
    """Keitaro stream mirrored into the local DB for staged editing."""

    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keitaro_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    campaign_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    schema: Mapped[str | None] = mapped_column(String(32), nullable=True)
    state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # True when local edits are not pushed to Keitaro yet ("yellow" stream)
    dirty: Mapped[bool] = mapped_column(Boolean, default=False)
    # Snapshot of offers as last seen in Keitaro: [{"offer_id": int, "share": int}]
    synced_offers: Mapped[list] = mapped_column(JSON, default=list)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    offers: Mapped[list["StreamOffer"]] = relationship(
        back_populates="stream", cascade="all, delete-orphan"
    )


class StreamOffer(Base):
    """An offer attached to a stream, with staged-edit metadata."""

    __tablename__ = "stream_offers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stream_id: Mapped[int] = mapped_column(
        ForeignKey("streams.id", ondelete="CASCADE"), index=True
    )
    offer_id: Mapped[int] = mapped_column(Integer)
    offer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    share: Mapped[int] = mapped_column(Integer, default=0)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|removed
    # True if the offer was ever present in Keitaro (distinguishes archive
    # entries from unsynced local additions)
    was_synced: Mapped[bool] = mapped_column(Boolean, default=False)

    stream: Mapped[Stream] = relationship(back_populates="offers")
