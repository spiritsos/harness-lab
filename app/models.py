from pydantic import BaseModel


class ProductOut(BaseModel):
    id: int
    name: str
    price: float


class OrderItemIn(BaseModel):
    product_id: int
    qty: int


class OrderCreate(BaseModel):
    customer: str
    items: list[OrderItemIn]
    coupon: str | None = None
