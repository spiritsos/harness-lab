from fastapi import APIRouter

from app.db import get_conn
from app.models import ProductOut

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
def list_products():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, price FROM products ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]
