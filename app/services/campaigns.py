"""Campaign creation orchestration: campaign + two flows in Keitaro."""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.keitaro.client import KeitaroClient
from app.models import CampaignRecord
from app.schemas.campaign import CampaignCreateRequest


async def create_keitaro_campaign(
    db: Session, client: KeitaroClient, body: CampaignCreateRequest
) -> dict:
    campaign_payload = {"name": body.name, "alias": body.alias}
    if body.domain_id is not None:
        campaign_payload["domain_id"] = body.domain_id
    if body.group_id is not None:
        campaign_payload["group_id"] = body.group_id
    if body.source_id is not None:
        campaign_payload["traffic_source_id"] = body.source_id

    campaign = await client.create_campaign(campaign_payload)
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
    except Exception:
        try:
            await client.disable_campaign(campaign_id)
        except Exception:
            pass
        raise

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
