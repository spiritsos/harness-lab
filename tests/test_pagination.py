def _make(client, n):
    for i in range(n):
        client.post("/orders", json={"customer": f"c{i}", "items": [{"product_id": 1, "qty": 1}]})


def test_first_page_default_limit(client):
    _make(client, 25)
    body = client.get("/orders").json()
    assert len(body["items"]) == 20
    assert body["items"][0]["order_no"] == "A-0025"
    assert body["next_cursor"] == "A-0006"


def test_walk_all_pages(client):
    _make(client, 7)
    seen, cursor = [], None
    while True:
        params = {"limit": 3} | ({"cursor": cursor} if cursor else {})
        body = client.get("/orders", params=params).json()
        seen += [o["order_no"] for o in body["items"]]
        cursor = body["next_cursor"]
        if cursor is None:
            break
    assert seen == [f"A-{i:04d}" for i in range(7, 0, -1)]


def test_limit_bounds(client):
    assert client.get("/orders", params={"limit": 0}).status_code == 422
    assert client.get("/orders", params={"limit": 101}).status_code == 422


def test_unknown_cursor(client):
    assert client.get("/orders", params={"cursor": "A-9999"}).status_code == 400
