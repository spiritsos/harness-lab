import pytest

from app.services import order_service


def _order(client, status):
    r = client.post("/orders", json={"customer": "kim", "items": [{"product_id": 1, "qty": 1}]})
    order_no = r.json()["order_no"]
    order_service.set_status(order_no, status)
    return order_no


def test_cancel_paid_order(client):
    order_no = _order(client, "PAID")
    r = client.post(f"/orders/{order_no}/cancel")
    assert r.status_code == 200
    assert r.json()["status"] == "CANCELLED"
    assert client.get(f"/orders/{order_no}").json()["cancelled_at"] is not None


@pytest.mark.parametrize("status", ["PENDING", "SHIPPED", "DELIVERED", "CANCELLED"])
def test_cannot_cancel_other_status(client, status):
    order_no = _order(client, status)
    r = client.post(f"/orders/{order_no}/cancel")
    assert r.status_code == 409
    assert "PAID" in r.json()["detail"]


def test_cancel_not_found(client):
    r = client.post("/orders/A-9999/cancel")
    assert r.status_code == 404
