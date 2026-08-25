from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ShippingCreate(BaseModel):
    address: str
    city: str
    postal_code: str


class ShippingUpdate(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None


class ShippingResponse(BaseModel):
    id: int
    order_id: int
    address: str
    city: str
    postal_code: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
