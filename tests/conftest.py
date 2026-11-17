import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import keitaro_dep
from app.core.database import Base, get_db
from app.main import app
from app.models import Stream, StreamOffer

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture()
def db():
    Base.metadata.create_all(engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


class FakeKeitaro:
    """In-memory stand-in for the Keitaro client (async methods)."""

    def __init__(self):
        self.campaigns = []
        self.streams = {}
        self.offers = []
        self._next_stream_id = 1

    def add_stream(self, campaign_id: int, offers=None, **kwargs) -> dict:
        sid = self._next_stream_id
        self._next_stream_id += 1
        stream = {
            "id": sid,
            "campaign_id": campaign_id,
            "name": kwargs.get("name", f"Stream {sid}"),
            "type": "regular",
            "schema": "landings",
            "state": "active",
            "offers": offers or [],
        }
        self.streams[sid] = stream
        return stream

    def add_offer(self, offer_id: int, name: str = "Offer") -> dict:
        offer = {"id": offer_id, "name": f"{name} {offer_id}"}
        self.offers.append(offer)
        return offer

    async def list_streams(self, campaign_id):
        return [s for s in self.streams.values() if s["campaign_id"] == campaign_id]

    async def list_offers(self):
        return self.offers

    async def get_offer(self, offer_id):
        return next((o for o in self.offers if o["id"] == offer_id), None)

    async def update_stream(self, stream_id, payload):
        self.streams[stream_id].update(payload)
        return self.streams[stream_id]


@pytest.fixture()
def api(db):
    fake = FakeKeitaro()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[keitaro_dep] = lambda: fake
    with TestClient(app) as client:
        yield client, fake
    app.dependency_overrides.clear()


def make_stream(db: Session, **kwargs) -> Stream:  # noqa: F821
    stream = Stream(
        keitaro_id=kwargs.get("keitaro_id", 1),
        campaign_id=kwargs.get("campaign_id", 100),
        name=kwargs.get("name", "S"),
        synced_offers=kwargs.get("synced_offers", []),
    )
    for o in kwargs.get("offers", []):
        stream.offers.append(StreamOffer(**o))
    db.add(stream)
    db.commit()
    db.refresh(stream)
    return stream
