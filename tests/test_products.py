def test_list_products(client):
    r = client.get("/products")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()]
    assert names == ["무선 마우스", "모니터 받침대"]
