def test_create_and_get_order(client):
    r = client.post("/orders", json={"customer": "kim", "items": [{"product_id": 1, "qty": 2}]})
    assert r.status_code == 201
    body = r.json()
    assert body["order_no"] == "A-0001"
    assert body["total"] == 51800

    r = client.get("/orders/A-0001")
    assert r.status_code == 200
    assert r.json()["items"][0]["qty"] == 2


def test_list_orders(client):
    client.post("/orders", json={"customer": "kim", "items": [{"product_id": 1, "qty": 1}]})
    client.post("/orders", json={"customer": "lee", "items": [{"product_id": 2, "qty": 1}]})
    r = client.get("/orders")
    assert r.status_code == 200
    assert [o["customer"] for o in r.json()["items"]] == ["lee", "kim"]


def test_get_order_not_found(client):
    r = client.get("/orders/A-9999")
    assert r.status_code == 404


def test_unknown_product(client):
    r = client.post("/orders", json={"customer": "kim", "items": [{"product_id": 99, "qty": 1}]})
    assert r.status_code == 400
