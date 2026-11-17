"""Persistence for the Keitaro session cookie."""

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.keitaro.client import KeitaroClient, set_keitaro_client
from app.models import KeitaroSession

_SESSION_ROW_ID = 1


def save_connection(db: Session, client: KeitaroClient) -> None:
    row = db.get(KeitaroSession, _SESSION_ROW_ID)
    if row is None:
        row = KeitaroSession(id=_SESSION_ROW_ID)
        db.add(row)
    row.base_url = client.base_url
    row.cookie = client.session_cookie
    db.commit()


def clear_connection(db: Session) -> None:
    row = db.get(KeitaroSession, _SESSION_ROW_ID)
    if row is not None:
        db.delete(row)
        db.commit()


def load_connection() -> None:
    """Restore the Keitaro session from the DB on startup, if present."""
    db = SessionLocal()
    try:
        row = db.get(KeitaroSession, _SESSION_ROW_ID)
        if row is not None:
            set_keitaro_client(KeitaroClient(row.base_url, row.cookie))
    finally:
        db.close()
