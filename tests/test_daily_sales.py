from datetime import date, timedelta

from app.models import OrderCreate, OrderItemIn
from app.services import order_service


def _order(qty, day, status="PAID"):
    req = OrderCreate(customer="kim", items=[OrderItemIn(product_id=1, qty=qty)])
    o = order_service.create_order(req, created_at=f"{day.isoformat()}T10:00:00")
    order_service.set_status(o["order_no"], status)


def test_daily_sales(client):
    today = date.today()
    _order(1, today)
    _order(2, today)
    _order(1, today - timedelta(days=2))
    _order(5, today - timedelta(days=2), status="CANCELLED")  # 제외
    _order(1, today - timedelta(days=10))  # 범위 밖

    body = client.get("/stats/daily-sales", params={"days": 3}).json()
    assert [d["date"] for d in body] == [(today - timedelta(days=i)).isoformat() for i in (2, 1, 0)]
    assert body[0] == {"date": body[0]["date"], "orders": 1, "sales": 25900}
    assert body[1]["orders"] == 0 and body[1]["sales"] == 0
    assert body[2]["orders"] == 2 and body[2]["sales"] == 25900 * 3
    assert all(isinstance(d["sales"], int) for d in body)


def test_days_bounds(client):
    assert client.get("/stats/daily-sales", params={"days": 0}).status_code == 422
    assert client.get("/stats/daily-sales", params={"days": 91}).status_code == 422
