from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .keitaro import (
    KeitaroClient,
    KeitaroError,
    KeitaroNotAuthenticated,
    get_keitaro_client,
    set_keitaro_client,
)
from .models import CampaignRecord, Stream, StreamOffer
from .schemas import CampaignCreateRequest, LoginRequest, OfferAddRequest
from .services import (
    active_offers_payload,
    recalc_shares,
    restore_baseline,
    serialize_stream,
    sync_stream_from_keitaro,
)

router = APIRouter(prefix="/api")


def handle_keitaro_error(exc: KeitaroError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


def keitaro_dep() -> KeitaroClient:
    try:
        return get_keitaro_client()
    except KeitaroNotAuthenticated:
        raise HTTPException(status_code=401, detail="Not connected to Keitaro")


# --- auth / connection ----------------------------------------------------


@router.post("/auth/login")
async def login(body: LoginRequest):
    try:
        client = await KeitaroClient.login(body.base_url, body.login, body.password)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)
    set_keitaro_client(client)
    return {"connected": True, "base_url": client.base_url}


@router.post("/auth/logout")
def logout():
    set_keitaro_client(None)
    return {"connected": False}


@router.get("/auth/status")
def auth_status():
    client = get_keitaro_client()
    return {"connected": client is not None, "base_url": client and client.base_url}


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


# --- reference data -----------------------------------------------------


@router.get("/domains")
async def domains(client: KeitaroClient = Depends(keitaro_dep)):
    try:
        return await client.list_domains()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/groups")
async def groups(client: KeitaroClient = Depends(keitaro_dep)):
    try:
        return await client.list_groups("campaigns")
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/sources")
async def sources(client: KeitaroClient = Depends(keitaro_dep)):
    try:
        return await client.list_traffic_sources()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/offers")
async def offers(client: KeitaroClient = Depends(keitaro_dep)):
    try:
        return await client.list_offers()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/offers/search")
async def search_offers(
    query: str = "", client: KeitaroClient = Depends(keitaro_dep)
):
    """Offer autocomplete: filters Keitaro offers by id or name substring."""
    try:
        all_offers = await client.list_offers()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)
    q = query.strip().lower()
    if not q:
        return all_offers
    return [
        o
        for o in all_offers
        if q in str(o.get("id", "")) or q in (o.get("name") or "").lower()
    ]


# --- part 1: campaign creator -------------------------------------------


@router.post("/campaigns", status_code=201)
async def create_campaign(
    body: CampaignCreateRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(keitaro_dep),
):
    campaign_payload = {"name": body.name, "alias": body.alias}
    if body.domain_id is not None:
        campaign_payload["domain_id"] = body.domain_id
    if body.group_id is not None:
        campaign_payload["group_id"] = body.group_id
    if body.source_id is not None:
        campaign_payload["traffic_source_id"] = body.source_id

    try:
        campaign = await client.create_campaign(campaign_payload)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    campaign_id = campaign["id"]

    try:
        geo_stream = await client.create_stream(
            {
                "campaign_id": campaign_id,
                "type": "regular",
                "name": f"{body.geo} -> Google",
                "position": 1,
                "schema": "redirect",
                "action_type": "http",
                "action_payload": settings.google_redirect_url,
                "filters": [
                    {"name": "country", "mode": "accept", "payload": [body.geo]}
                ],
            }
        )
        offer_stream = await client.create_stream(
            {
                "campaign_id": campaign_id,
                "type": "regular",
                "name": "Offer",
                "position": 2,
                "schema": "landings",
                "action_type": "http",
                "offers": [{"offer_id": body.offer_id, "share": 100}],
            }
        )
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    record = CampaignRecord(
        keitaro_id=campaign_id,
        name=body.name,
        alias=body.alias,
        geo=body.geo,
        domain_id=body.domain_id,
        group_id=body.group_id,
        source_id=body.source_id,
        offer_id=body.offer_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "record_id": record.id,
        "campaign": campaign,
        "streams": [geo_stream, offer_stream],
    }


@router.get("/campaigns/local")
def local_campaigns(db: Session = Depends(get_db)):
    return db.query(CampaignRecord).order_by(CampaignRecord.id.desc()).all()


# --- part 2: staged offers editor ----------------------------------------


@router.get("/campaigns")
async def list_campaigns(client: KeitaroClient = Depends(keitaro_dep)):
    try:
        return await client.list_campaigns()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/campaigns/search")
async def search_campaigns(
    query: str = "", client: KeitaroClient = Depends(keitaro_dep)
):
    """Campaign autocomplete: filters Keitaro campaigns by id/name/alias."""
    try:
        all_campaigns = await client.list_campaigns()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)
    q = query.strip().lower()
    if not q:
        return all_campaigns
    return [
        c
        for c in all_campaigns
        if q in str(c.get("id", ""))
        or q in (c.get("name") or "").lower()
        or q in (c.get("alias") or "").lower()
    ]


@router.post("/campaigns/{campaign_id}/fetch_streams")
async def fetch_streams(
    campaign_id: int,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(keitaro_dep),
):
    """Pull streams from Keitaro and merge them into the local DB.

    Streams without offers are stored as plain streams. Offers that were in
    Keitaro before but are gone now are kept locally with status 'removed'.
    """
    try:
        kstreams = await client.list_streams(campaign_id)
        koffers = await client.list_offers()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    offer_names = {o["id"]: o.get("name") for o in koffers or []}

    for ks in kstreams or []:
        stream = (
            db.query(Stream).filter(Stream.keitaro_id == ks["id"]).one_or_none()
        )
        if stream is None:
            stream = Stream(keitaro_id=ks["id"], campaign_id=campaign_id)
            db.add(stream)
        stream.campaign_id = campaign_id
        stream.name = ks.get("name") or f"Stream {ks['id']}"
        stream.type = ks.get("type")
        stream.schema = ks.get("schema")
        stream.state = ks.get("state")
        sync_stream_from_keitaro(db, stream, ks, offer_names)

    db.commit()
    streams = (
        db.query(Stream)
        .filter(Stream.campaign_id == campaign_id)
        .order_by(Stream.id)
        .all()
    )
    return [serialize_stream(s) for s in streams]


@router.get("/campaigns/{campaign_id}/streams")
def list_local_streams(campaign_id: int, db: Session = Depends(get_db)):
    streams = (
        db.query(Stream)
        .filter(Stream.campaign_id == campaign_id)
        .order_by(Stream.id)
        .all()
    )
    return [serialize_stream(s) for s in streams]


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
