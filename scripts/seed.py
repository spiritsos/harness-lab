"""샘플 데이터를 넣는다. 날짜는 실행 시점 기준 최근 30일로 만든다."""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_conn, init_db  # noqa: E402
from app.models import OrderCreate, OrderItemIn  # noqa: E402
from app.services import order_service  # noqa: E402

PRODUCTS = [
    ("무선 마우스", 25900),
    ("기계식 키보드", 89000),
    ("USB-C 허브", 39900),
    ("모니터 받침대", 9990),
    ("노트북 파우치", 19900),
]
CUSTOMERS = ["kim", "lee", "park", "choi", "jung", "kang", "yoon"]


def main() -> None:
    init_db()
    conn = get_conn()
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] > 0:
        print("이미 데이터가 있습니다. 초기화하려면 scripts/reset_db.py")
        return
    conn.executemany("INSERT INTO products (name, price) VALUES (?, ?)", PRODUCTS)
    conn.commit()

    rng = random.Random(42)
    now = datetime.now()
    for _ in range(40):
        created = now - timedelta(days=rng.randint(0, 29), hours=rng.randint(0, 23))
        req = OrderCreate(
            customer=rng.choice(CUSTOMERS),
            items=[OrderItemIn(product_id=rng.randint(1, 5), qty=rng.randint(1, 3))],
        )
        o = order_service.create_order(req, created_at=created.isoformat(timespec="seconds"))
        status = rng.choice(["PENDING", "PAID", "PAID", "SHIPPED", "DELIVERED", "CANCELLED"])
        cancelled_at = None
        if status == "CANCELLED":
            cancelled_at = (created + timedelta(hours=rng.randint(1, 48))).isoformat(timespec="seconds")
        conn.execute(
            "UPDATE orders SET status = ?, cancelled_at = ? WHERE order_no = ?",
            (status, cancelled_at, o["order_no"]),
        )
        conn.commit()
    conn.close()
    print("seed 완료: 상품 5개, 주문 40건")


if __name__ == "__main__":
    main()
