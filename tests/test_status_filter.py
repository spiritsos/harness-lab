from app.services import order_service


def _make(client, statuses):
    for st in statuses:
        r = client.post("/orders", json={"customer": "kim", "items": [{"product_id": 1, "qty": 1}]})
        order_service.set_status(r.json()["order_no"], st)


def test_filter_by_status(client):
    _make(client, ["PAID", "PENDING", "PAID", "SHIPPED"])
    body = client.get("/orders", params={"status": "PAID"}).json()
    assert [o["order_no"] for o in body["items"]] == ["A-0003", "A-0001"]


def test_filter_with_pagination(client):
    _make(client, ["PAID", "PENDING", "PAID", "PAID", "SHIPPED", "PAID"])
    first = client.get("/orders", params={"status": "PAID", "limit": 2}).json()
    assert [o["order_no"] for o in first["items"]] == ["A-0006", "A-0004"]
    second = client.get(
        "/orders", params={"status": "PAID", "limit": 2, "cursor": first["next_cursor"]}
    ).json()
    assert [o["order_no"] for o in second["items"]] == ["A-0003", "A-0001"]
    assert second["next_cursor"] is None


def test_unknown_status(client):
    r = client.get("/orders", params={"status": "LOST"})
    assert r.status_code == 400
    assert "PAID" in r.json()["detail"]
