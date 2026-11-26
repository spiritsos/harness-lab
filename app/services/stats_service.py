from datetime import date, timedelta

from app.db import get_conn


def daily_sales(days: int = 7, today: date | None = None):
    """최근 days일(오늘 포함)의 일별 주문 수·매출. CANCELLED 제외, 주문이 없는 날은 0."""
    today = today or date.today()
    start = today - timedelta(days=days - 1)
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS orders, SUM(total) AS sales
        FROM orders
        WHERE status != 'CANCELLED' AND substr(created_at, 1, 10) BETWEEN ? AND ?
        GROUP BY day
        """,
        (start.isoformat(), today.isoformat()),
    ).fetchall()
    conn.close()
    by_day = {r["day"]: r for r in rows}
    out = []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        r = by_day.get(d)
        out.append({"date": d, "orders": r["orders"] if r else 0, "sales": int(r["sales"]) if r else 0})
    return out
