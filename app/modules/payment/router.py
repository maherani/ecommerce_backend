import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.order.models import Order
from app.modules.payment import models, schemas
from app.modules.user.models import User
from app.modules.user.router import get_current_user

router = APIRouter(prefix="/payment", tags=["Payment"])

@router.post("/process", response_model=schemas.PaymentResponse)
def process_payment(
   payment_data: schemas.PaymentRequest,
   db: Session = Depends(get_db),
   current_user: User = Depends(get_current_user)
):
    """پرداخت سفارش pending و ایجاد رکورد Payment"""

    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be paid"
        )

    if order.payment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order already has a payment"
        )

    transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"

    payment = models.Payment(
        order_id=order.id,
        amount=order.total_price,
        status="paid",
        transaction_id=transaction_id,
        paid_at=datetime.now(timezone.utc)
    )

    order.status = "paid"

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return schemas.PaymentResponse(
        order_id=order.id,
        status=payment.status,
        message="Payment processed successfully",
        transaction_id=payment.transaction_id
    )
