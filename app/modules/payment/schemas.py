from datetime import datetime

from pydantic import BaseModel

class PaymentRequest(BaseModel):
    order_id: int
    card_number: str = "6037991122334455"
    idempotency_key: str | None = None

class PaymentResponse(BaseModel):
    order_id: int
    status: str
    message: str
    transaction_id: str
class PaymentWebhookRequest(BaseModel):
    transaction_id: str
    status: str
    event_id: str

class PaymentDetailsResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    status: str
    transaction_id: str | None
    created_at: datetime
    paid_at: datetime | None
    refunded_at: datetime | None