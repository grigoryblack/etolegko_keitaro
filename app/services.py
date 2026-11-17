"""Staged-editing logic for streams and their offers."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import Stream, StreamOffer


def recalc_shares(stream: Stream) -> None:
    """Redistribute shares among active offers, keeping pinned ones fixed.

    Active pinned offers keep their share; the remaining percentage is split
    evenly between active unpinned offers. Removed offers get 0.
    """
    active = [o for o in stream.offers if o.status == "active"]
    pinned_sum = sum(o.share for o in active if o.pinned)
    free = [o for o in active if not o.pinned]
    for o in stream.offers:
        if o.status == "removed":
            o.share = 0
    if free:
        total = max(0, 100 - pinned_sum)
        base = total // len(free)
        remainder = total - base * len(free)
        for i, o in enumerate(free):
            o.share = base + (1 if i < remainder else 0)


def serialize_stream(stream: Stream) -> dict:
    return {
        "id": stream.id,
        "keitaro_id": stream.keitaro_id,
        "campaign_id": stream.campaign_id,
        "name": stream.name,
        "type": stream.type,
        "schema": stream.schema,
        "state": stream.state,
        "dirty": stream.dirty,
        "offers": [
            {
                "id": o.id,
                "offer_id": o.offer_id,
                "offer_name": o.offer_name,
                "share": o.share,
                "pinned": o.pinned,
                "status": o.status,
            }
            for o in sorted(stream.offers, key=lambda x: x.id)
        ],
    }


def _baseline_ids(stream: Stream) -> set[int]:
    return {entry["offer_id"] for entry in stream.synced_offers or []}


def sync_stream_from_keitaro(
    db: Session, stream: Stream, kstream: dict, offer_names: dict[int, str]
) -> None:
    """Merge Keitaro stream state into the local row.

    - Streams without offers are stored as plain streams (no offers rows).
    - Offers present in Keitaro -> active, share synced.
    - Offers that were in Keitaro at last sync but are gone now -> 'removed'.
    - Offers added locally but never synced -> dropped on fetch.
    - Local edits (dirty flag) are reset: Keitaro is the source of truth.
    """
    k_offers = kstream.get("offers") or []
    baseline = [
        {"offer_id": o["offer_id"], "share": o.get("share", 0)} for o in k_offers
    ]
    keitaro_ids = {o["offer_id"] for o in k_offers}
    previous_baseline = _baseline_ids(stream)

    for offer in list(stream.offers):
        if offer.offer_id in keitaro_ids:
            offer.status = "active"
            offer.was_synced = True
            offer.share = next(
                o["share"] for o in baseline if o["offer_id"] == offer.offer_id
            )
        elif offer.offer_id in previous_baseline or (
            offer.status == "removed" and offer.was_synced
        ):
            # gone from Keitaro (or already archived earlier): keep as removed
            offer.status = "removed"
            offer.was_synced = True
            offer.share = 0
        else:
            db.delete(offer)

    existing_ids = {o.offer_id for o in stream.offers}
    for o in k_offers:
        if o["offer_id"] not in existing_ids:
            stream.offers.append(
                StreamOffer(
                    offer_id=o["offer_id"],
                    offer_name=offer_names.get(o["offer_id"]),
                    share=o.get("share", 0),
                    status="active",
                    was_synced=True,
                )
            )

    stream.synced_offers = baseline
    stream.dirty = False
    stream.fetched_at = datetime.now(timezone.utc)


def restore_baseline(db: Session, stream: Stream) -> None:
    """Cancel unpublished changes: revert offers to the last synced snapshot."""
    baseline = {e["offer_id"]: e["share"] for e in stream.synced_offers or []}
    for offer in list(stream.offers):
        if offer.offer_id in baseline:
            offer.status = "active"
            offer.share = baseline[offer.offer_id]
        elif offer.was_synced:
            # externally removed in Keitaro: keep the archive entry
            offer.status = "removed"
            offer.share = 0
        else:
            # locally added but never pushed: drop it
            db.delete(offer)
    stream.dirty = False


def active_offers_payload(stream: Stream) -> list[dict]:
    return [
        {"offer_id": o.offer_id, "share": o.share}
        for o in stream.offers
        if o.status == "active"
    ]
