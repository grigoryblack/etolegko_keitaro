from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import handle_keitaro_error, keitaro_dep
from app.api.routes.references import _matches
from app.core.database import get_db
from app.keitaro.client import KeitaroClient, KeitaroError
from app.models import CampaignRecord, Stream
from app.schemas.campaign import CampaignCreateRequest
from app.services.campaigns import create_keitaro_campaign
from app.services.streams import serialize_stream, sync_stream_from_keitaro

router = APIRouter(tags=["campaigns"])


@router.post("/campaigns", status_code=201)
async def create_campaign(
    body: CampaignCreateRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(keitaro_dep),
):
    try:
        return await create_keitaro_campaign(db, client, body)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/campaigns/local")
def local_campaigns(db: Session = Depends(get_db)):
    return db.query(CampaignRecord).order_by(CampaignRecord.id.desc()).all()


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
    """Campaign autocomplete: every space-separated token must match id/name/alias."""
    try:
        all_campaigns = await client.list_campaigns()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)
    if not query.strip():
        return all_campaigns
    return [
        c
        for c in all_campaigns
        if _matches(query, c.get("id"), c.get("name"), c.get("alias"))
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

    # drop local streams that no longer exist in Keitaro
    keitaro_stream_ids = {ks["id"] for ks in kstreams or []}
    db.query(Stream).filter(
        Stream.campaign_id == campaign_id,
        Stream.keitaro_id.notin_(keitaro_stream_ids),
    ).delete(synchronize_session=False)

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
