from app.models import Stream


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
