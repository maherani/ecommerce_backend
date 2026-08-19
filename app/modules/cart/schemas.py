from pydantic import BaseModel, Field
from typing import Optional
from app.modules.product.schemas import ProductResponse

class CartItemBase(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, default=1)

class CartItemCreate(CartItemBase):
    pass

class CartItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
