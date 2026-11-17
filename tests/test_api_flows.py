def _shares(stream):
    return {o["offer_id"]: (o["share"], o["status"]) for o in stream["offers"]}


def test_fetch_add_push_flow(api):
    client, fake = api
    fake.add_offer(1, "A")
    fake.add_offer(2, "B")
    fake.add_stream(100, offers=[{"offer_id": 1, "share": 100}])

    res = client.post("/api/campaigns/100/fetch_streams")
    assert res.status_code == 200
    stream = res.json()[0]
    assert stream["dirty"] is False
    assert _shares(stream) == {1: (100, "active")}

    res = client.post(f"/api/streams/{stream['id']}/offers", json={"offer_id": 2})
    stream = res.json()
    assert stream["dirty"] is True
    assert _shares(stream) == {1: (50, "active"), 2: (50, "active")}
    # Keitaro untouched until push
    assert fake.streams[1]["offers"] == [{"offer_id": 1, "share": 100}]

    res = client.post(f"/api/streams/{stream['id']}/push")
    assert res.json()["dirty"] is False
    assert fake.streams[1]["offers"] == [
        {"offer_id": 1, "share": 50},
        {"offer_id": 2, "share": 50},
    ]


def test_cancel_reverts_unpublished_changes(api):
    client, fake = api
    fake.add_offer(1, "A")
    fake.add_offer(2, "B")
    fake.add_stream(100, offers=[{"offer_id": 1, "share": 100}])

    stream = client.post("/api/campaigns/100/fetch_streams").json()[0]
    client.post(f"/api/streams/{stream['id']}/offers", json={"offer_id": 2})
    stream = client.post(f"/api/streams/{stream['id']}/cancel").json()
    assert stream["dirty"] is False
    assert _shares(stream) == {1: (100, "active")}


def test_remove_and_bring_back(api):
    client, fake = api
    fake.add_offer(1, "A")
    fake.add_offer(2, "B")
    fake.add_stream(
        100, offers=[{"offer_id": 1, "share": 50}, {"offer_id": 2, "share": 50}]
    )

    stream = client.post("/api/campaigns/100/fetch_streams").json()[0]
    stream = client.post(f"/api/streams/{stream['id']}/offers/2/remove").json()
    assert _shares(stream) == {1: (100, "active"), 2: (0, "removed")}

    stream = client.post(f"/api/streams/{stream['id']}/offers/2/restore").json()
    assert _shares(stream) == {1: (50, "active"), 2: (50, "active")}


def test_pin_keeps_weight_on_recalc(api):
    client, fake = api
    for i in (1, 2, 3):
        fake.add_offer(i, "A")
    fake.add_stream(
        100,
        offers=[{"offer_id": 1, "share": 34}, {"offer_id": 2, "share": 33}, {"offer_id": 3, "share": 33}],
    )

    stream = client.post("/api/campaigns/100/fetch_streams").json()[0]
    stream = client.post(f"/api/streams/{stream['id']}/offers/1/pin").json()
    stream = client.post(f"/api/streams/{stream['id']}/offers/3/remove").json()
    assert _shares(stream)[1] == (34, "active")
    assert _shares(stream)[2] == (66, "active")
    assert _shares(stream)[3] == (0, "removed")


def test_external_deletion_syncs_as_removed(api):
    client, fake = api
    fake.add_offer(1, "A")
    fake.add_offer(2, "B")
    fake.add_offer(3, "C")
    fake.add_stream(
        100, offers=[{"offer_id": 1, "share": 50}, {"offer_id": 2, "share": 50}]
    )

    client.post("/api/campaigns/100/fetch_streams")
    fake.streams[1]["offers"] = [{"offer_id": 1, "share": 50}, {"offer_id": 3, "share": 50}]

    stream = client.post("/api/campaigns/100/fetch_streams").json()[0]
    assert _shares(stream) == {
        1: (50, "active"),
        2: (0, "removed"),
        3: (50, "active"),
    }
