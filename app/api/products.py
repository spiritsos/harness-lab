from fastapi import APIRouter

from app.models import ProductOut
from app.services import order_service

router = APIRouter()


@router.get("/products", response_model=list[ProductOut])
def list_products():
    return order_service.list_products()
