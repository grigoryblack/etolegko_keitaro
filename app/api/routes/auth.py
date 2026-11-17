from fastapi import APIRouter

from app.api.deps import handle_keitaro_error
from app.keitaro.client import (
    KeitaroClient,
    KeitaroError,
    get_keitaro_client,
    set_keitaro_client,
)
from app.schemas.auth import LoginRequest

router = APIRouter(tags=["auth"])


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
