def test_coupon_discount_is_int_and_floored(client):
    # 모니터 받침대 9,990원 → 10% 할인 999원 → 8,991원 (정수)
    r = client.post(
        "/orders",
        json={"customer": "kim", "items": [{"product_id": 2, "qty": 1}], "coupon": "WELCOME10"},
    )
    total = r.json()["total"]
    assert total == 8991
    assert isinstance(total, int)


def test_product_price_is_int(client):
    prices = [p["price"] for p in client.get("/products").json()]
    assert all(isinstance(p, int) for p in prices)
