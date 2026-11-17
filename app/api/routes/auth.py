from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import handle_keitaro_error
from app.core.database import get_db
from app.keitaro.client import (
    KeitaroClient,
    KeitaroError,
    get_keitaro_client,
    set_keitaro_client,
)
from app.schemas.auth import LoginRequest
from app.services.connection import clear_connection, save_connection

router = APIRouter(tags=["auth"])


@router.post("/auth/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    try:
        client = await KeitaroClient.login(body.base_url, body.login, body.password)
    except KeitaroError as exc:
        raise handle_keitaro_error(exc)
    set_keitaro_client(client)
    save_connection(db, client)
    return {"connected": True, "base_url": client.base_url}


@router.post("/auth/logout")
def logout(db: Session = Depends(get_db)):
    set_keitaro_client(None)
    clear_connection(db)
    return {"connected": False}


@router.get("/auth/status")
def auth_status():
    try:
        client = get_keitaro_client()
    except KeitaroError:
        return {"connected": False, "base_url": None}
    return {"connected": True, "base_url": client.base_url}
