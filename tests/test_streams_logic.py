from app.services.streams import (
    recalc_shares,
    restore_baseline,
    sync_stream_from_keitaro,
)

from .conftest import make_stream


def test_recalc_splits_evenly(db):
    s = make_stream(db, offers=[
        {"offer_id": 1, "share": 100},
        {"offer_id": 2, "share": 0},
        {"offer_id": 3, "share": 0},
    ])
    recalc_shares(s)
    assert [o.share for o in s.offers] == [34, 33, 33]


def test_recalc_respects_pinned(db):
    s = make_stream(db, offers=[
        {"offer_id": 1, "share": 25, "pinned": True},
        {"offer_id": 2, "share": 0},
        {"offer_id": 3, "share": 0},
    ])
    recalc_shares(s)
    assert [o.share for o in s.offers] == [25, 38, 37]
    assert sum(o.share for o in s.offers) == 100


def test_recalc_removed_gets_zero(db):
    s = make_stream(db, offers=[
        {"offer_id": 1, "share": 50},
        {"offer_id": 2, "share": 50, "status": "removed"},
    ])
    recalc_shares(s)
    assert [o.share for o in s.offers] == [100, 0]


def test_sync_marks_missing_offers_removed(db):
    s = make_stream(db, synced_offers=[{"offer_id": 1, "share": 50}, {"offer_id": 2, "share": 50}],
                    offers=[
                        {"offer_id": 1, "share": 50, "was_synced": True},
                        {"offer_id": 2, "share": 50, "was_synced": True},
                    ])
    sync_stream_from_keitaro(db, s, {"offers": [{"offer_id": 1, "share": 100}]}, {})
    assert [(o.offer_id, o.status) for o in s.offers] == [(1, "active"), (2, "removed")]


def test_sync_keeps_removed_offers_across_fetches(db):
    """An offer already marked removed must survive subsequent fetches."""
    s = make_stream(db, synced_offers=[{"offer_id": 1, "share": 100}],
                    offers=[
                        {"offer_id": 1, "share": 100, "was_synced": True},
                        {"offer_id": 2, "share": 0, "status": "removed", "was_synced": True},
                    ])
    sync_stream_from_keitaro(db, s, {"offers": [{"offer_id": 1, "share": 100}]}, {})
    statuses = {o.offer_id: o.status for o in s.offers}
    assert statuses == {1: "active", 2: "removed"}


def test_sync_drops_unsynced_local_additions(db):
    s = make_stream(db, synced_offers=[{"offer_id": 1, "share": 100}],
                    offers=[
                        {"offer_id": 1, "share": 50, "was_synced": True},
                        {"offer_id": 9, "share": 50, "was_synced": False},
                    ])
    sync_stream_from_keitaro(db, s, {"offers": [{"offer_id": 1, "share": 100}]}, {})
    db.commit()
    db.expire(s)
    assert [o.offer_id for o in s.offers] == [1]


def test_restore_baseline_cancels_edits(db):
    s = make_stream(db, synced_offers=[{"offer_id": 1, "share": 100}], dirty=True,
                    offers=[
                        {"offer_id": 1, "share": 50, "was_synced": True},
                        {"offer_id": 5, "share": 50, "was_synced": False},
                        {"offer_id": 2, "share": 0, "status": "removed", "was_synced": True},
                    ])
    restore_baseline(db, s)
    db.commit()
    db.expire(s)
    assert [(o.offer_id, o.share, o.status) for o in s.offers] == [
        (1, 100, "active"),
        (2, 0, "removed"),
    ]
    assert s.dirty is False
