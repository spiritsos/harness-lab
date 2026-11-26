from fastapi import APIRouter, HTTPException

from app.db import get_conn
from app.models import OrderCreate
from app.services import order_service

router = APIRouter()


@router.get("/orders")
def list_orders():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@router.get("/orders/{order_no}")
def get_order(order_no: str):
    order = order_service.get_order(order_no)
    if order is None:
        raise HTTPException(status_code=404, detail="not found")
    return order


@router.post("/orders", status_code=201)
def create_order(req: OrderCreate):
    try:
        return order_service.create_order(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
