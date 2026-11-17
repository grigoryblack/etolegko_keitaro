from fastapi import HTTPException

from app.keitaro.client import (
    KeitaroClient,
    KeitaroError,
    KeitaroNotAuthenticated,
    get_keitaro_client,
)


def keitaro_dep() -> KeitaroClient:
    try:
        return get_keitaro_client()
    except KeitaroNotAuthenticated:
        raise HTTPException(status_code=401, detail="Not connected to Keitaro")


def handle_keitaro_error(exc: KeitaroError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)
