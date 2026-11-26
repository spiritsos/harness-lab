from datetime import datetime

from app.db import get_conn
from app.models import OrderCreate

COUPONS = {"WELCOME10": 0.1}


def get_order(order_no: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE order_no = ?", (order_no,)).fetchone()
    if row is None:
        conn.close()
        return None
    order = dict(row)
    items = conn.execute(
        "SELECT product_id, qty, unit_price FROM order_items WHERE order_id = ?",
        (row["id"],),
    ).fetchall()
    order["items"] = [dict(i) for i in items]
    conn.close()
    return order


def create_order(req: OrderCreate, created_at: str | None = None):
    conn = get_conn()
    total = 0
    lines = []
    for item in req.items:
        p = conn.execute("SELECT id, price FROM products WHERE id = ?", (item.product_id,)).fetchone()
        if p is None:
            conn.close()
            raise ValueError(f"product {item.product_id} not found")
        total += p["price"] * item.qty
        lines.append((p["id"], item.qty, p["price"]))

    if req.coupon in COUPONS:
        total = total * (1 - COUPONS[req.coupon])

    cur = conn.execute(
        "INSERT INTO orders (customer, total, created_at) VALUES (?, ?, ?)",
        (req.customer, total, created_at or datetime.now().isoformat(timespec="seconds")),
    )
    order_id = cur.lastrowid
    order_no = f"A-{order_id:04d}"
    conn.execute("UPDATE orders SET order_no = ? WHERE id = ?", (order_no, order_id))
    for product_id, qty, unit_price in lines:
        conn.execute(
            "INSERT INTO order_items (order_id, product_id, qty, unit_price) VALUES (?, ?, ?, ?)",
            (order_id, product_id, qty, unit_price),
        )
    conn.commit()
    conn.close()
    return {"order_no": order_no, "customer": req.customer, "total": total, "status": "PENDING"}
