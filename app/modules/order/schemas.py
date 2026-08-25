from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.modules.product.schemas import ProductResponse
from app.modules.shipping.schemas import ShippingResponse

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []
    shipping: Optional[ShippingResponse] = None

    class Config:
        from_attributes = True

class CheckoutRequest(BaseModel):
    address: str
    city: str
    postal_code: str
