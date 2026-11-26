from fastapi import FastAPI

from app.api import orders, products
from app.db import init_db

app = FastAPI(title="Order Service")
init_db()

app.include_router(orders.router)
app.include_router(products.router)
