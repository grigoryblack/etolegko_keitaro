from fastapi import APIRouter, Depends

from app.api.deps import handle_keitaro_error, keitaro_dep
from app.keitaro.client import KeitaroClient, KeitaroError

router = APIRouter(tags=["references"])


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
