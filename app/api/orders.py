from fastapi import APIRouter, HTTPException

from app.models import OrderCreate
from app.services import order_service

router = APIRouter()


@router.get("/orders")
def list_orders():
    return order_service.list_orders()


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


@router.post("/orders/{order_no}/cancel")
def cancel_order(order_no: str):
    try:
        return order_service.cancel_order(order_no)
    except order_service.OrderNotFound:
        raise HTTPException(status_code=404, detail=f"주문 {order_no}을(를) 찾을 수 없습니다") from None
    except order_service.InvalidTransition as e:
        raise HTTPException(
            status_code=409,
            detail=f"현재 상태 {e}에서는 취소할 수 없습니다. 취소는 PAID 상태에서만 가능합니다.",
        ) from None
