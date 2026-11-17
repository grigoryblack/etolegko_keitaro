from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .keitaro import KeitaroClient, KeitaroError, get_keitaro_client
from .models import CampaignRecord
from .schemas import CampaignCreateRequest, OfferAddRequest

router = APIRouter(prefix="/api")


def handle_keitaro_error(exc: KeitaroError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


# --- reference data -----------------------------------------------------


@router.get("/domains")
async def domains(client: KeitaroClient = Depends(get_keitaro_client)):
    try:
        return await client.list_domains()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/groups")
async def groups(client: KeitaroClient = Depends(get_keitaro_client)):
    try:
        return await client.list_groups("campaigns")
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/sources")
async def sources(client: KeitaroClient = Depends(get_keitaro_client)):
    try:
        return await client.list_traffic_sources()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/offers")
async def offers(client: KeitaroClient = Depends(get_keitaro_client)):
    try:
        return await client.list_offers()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


# --- part 1: campaign creator -------------------------------------------


@router.post("/campaigns", status_code=201)
async def create_campaign(
    body: CampaignCreateRequest,
    db: Session = Depends(get_db),
    client: KeitaroClient = Depends(get_keitaro_client),
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


# --- part 2: campaign offers editor --------------------------------------


@router.get("/campaigns")
async def list_campaigns(client: KeitaroClient = Depends(get_keitaro_client)):
    try:
        return await client.list_campaigns()
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.get("/campaigns/{campaign_id}/streams")
async def list_streams(
    campaign_id: int, client: KeitaroClient = Depends(get_keitaro_client)
):
    try:
        return await client.list_streams(campaign_id)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


def _current_offers(stream: dict) -> list[dict]:
    return [
        {"offer_id": o["offer_id"], "share": o.get("share", 100)}
        for o in stream.get("offers") or []
    ]


@router.post("/campaigns/{campaign_id}/streams/{stream_id}/offers")
async def add_offer(
    campaign_id: int,
    stream_id: int,
    body: OfferAddRequest,
    client: KeitaroClient = Depends(get_keitaro_client),
):
    try:
        stream = await client.get_stream(stream_id)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    offers = _current_offers(stream)
    if any(o["offer_id"] == body.offer_id for o in offers):
        raise HTTPException(status_code=400, detail="Offer is already in this stream")
    offers.append({"offer_id": body.offer_id, "share": body.share})

    try:
        return await client.update_stream(stream_id, {"offers": offers})
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.delete("/campaigns/{campaign_id}/streams/{stream_id}/offers/{offer_id}")
async def remove_offer(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    client: KeitaroClient = Depends(get_keitaro_client),
):
    try:
        stream = await client.get_stream(stream_id)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    offers = _current_offers(stream)
    remaining = [o for o in offers if o["offer_id"] != offer_id]
    if len(remaining) == len(offers):
        raise HTTPException(status_code=404, detail="Offer not found in this stream")

    try:
        return await client.update_stream(stream_id, {"offers": remaining})
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)


@router.put("/campaigns/{campaign_id}/streams/{stream_id}/offers/{offer_id}")
async def update_offer_share(
    campaign_id: int,
    stream_id: int,
    offer_id: int,
    body: OfferAddRequest,
    client: KeitaroClient = Depends(get_keitaro_client),
):
    try:
        stream = await client.get_stream(stream_id)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)

    offers = _current_offers(stream)
    for o in offers:
        if o["offer_id"] == offer_id:
            o["share"] = body.share
            break
    else:
        raise HTTPException(status_code=404, detail="Offer not found in this stream")

    try:
        return await client.update_stream(stream_id, {"offers": offers})
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)
