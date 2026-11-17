from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import handle_keitaro_error, keitaro_dep
from app.core.database import get_db
from app.keitaro.client import KeitaroClient, KeitaroError
from app.models import Stream, StreamOffer
from app.schemas.stream import OfferAddRequest
from app.services.streams import (
    active_offers_payload,
    recalc_shares,
    restore_baseline,
    serialize_stream,
)

router = APIRouter(tags=["streams"])


def get_stream_or_404(db: Session, stream_id: int) -> Stream:
    stream = db.get(Stream, stream_id)
    if stream is None:
        raise HTTPException(status_code=404, detail="Stream not found. Fetch streams first.")
    return stream


def get_offer_or_404(stream: Stream, offer_id: int) -> StreamOffer:
    for offer in stream.offers:
        if offer.offer_id == offer_id:
            return offer
    raise HTTPException(status_code=404, detail="Offer not found in this stream")


@router.post("/streams/{stream_id}/offers", status_code=201)
async def add_offer(
    stream_id: int,
    body: OfferAddRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(keitaro_dep),
):
    stream = get_stream_or_404(db, stream_id)
    existing = next(
        (o for o in stream.offers if o.offer_id == body.offer_id), None
    )
    if existing is not None:
        if existing.status == "active":
            raise HTTPException(400, "Offer is already in this stream")
        existing.status = "active"  # re-adding a removed offer restores it
    else:
        try:
            koffer = await client.get_offer(body.offer_id)
            name = koffer.get("name") if koffer else None
        except KeitaroError:
            name = None
        stream.offers.append(
            StreamOffer(offer_id=body.offer_id, offer_name=name, status="active")
        )
    recalc_shares(stream)
    stream.dirty = True
    db.commit()
    return serialize_stream(stream)


@router.post("/streams/{stream_id}/offers/{offer_id}/remove")
def remove_offer(stream_id: int, offer_id: int, db: Session = Depends(get_db)):
    stream = get_stream_or_404(db, stream_id)
    offer = get_offer_or_404(stream, offer_id)
    if offer.status == "removed":
        raise HTTPException(400, "Offer is already removed")
    offer.status = "removed"
    recalc_shares(stream)
    stream.dirty = True
    db.commit()
    return serialize_stream(stream)


@router.post("/streams/{stream_id}/offers/{offer_id}/restore")
def restore_offer(stream_id: int, offer_id: int, db: Session = Depends(get_db)):
    stream = get_stream_or_404(db, stream_id)
    offer = get_offer_or_404(stream, offer_id)
    if offer.status == "active":
        raise HTTPException(400, "Offer is not removed")
    offer.status = "active"
    recalc_shares(stream)
    stream.dirty = True
    db.commit()
    return serialize_stream(stream)


@router.post("/streams/{stream_id}/offers/{offer_id}/pin")
def toggle_pin(stream_id: int, offer_id: int, db: Session = Depends(get_db)):
    stream = get_stream_or_404(db, stream_id)
    offer = get_offer_or_404(stream, offer_id)
    if offer.status != "active":
        raise HTTPException(400, "Cannot pin a removed offer")
    offer.pinned = not offer.pinned
    recalc_shares(stream)
    stream.dirty = True
    db.commit()
    return serialize_stream(stream)


@router.post("/streams/{stream_id}/cancel")
def cancel_changes(stream_id: int, db: Session = Depends(get_db)):
    stream = get_stream_or_404(db, stream_id)
    restore_baseline(db, stream)
    db.commit()
    return serialize_stream(stream)


@router.post("/streams/{stream_id}/push")
async def push_to_keitaro(
    stream_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(keitaro_dep),
):
    stream = get_stream_or_404(db, stream_id)
    try:
        await client.update_stream(
            stream.keitaro_id, {"offers": active_offers_payload(stream)}
        )
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    stream.synced_offers = active_offers_payload(stream)
    for o in stream.offers:
        if o.status == "active":
            o.was_synced = True
    stream.dirty = False
    db.commit()
    return serialize_stream(stream)
