from pydantic import BaseModel

class PaymentRequest(BaseModel):
    order_id: int
    card_number: str = "6037991122334455"

class PaymentResponse(BaseModel):
    order_id: int
    status: str
    message: str
    transaction_id: str
