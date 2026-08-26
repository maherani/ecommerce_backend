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

    if payment_data.idempotency_key:
        existing_payment = db.query(models.Payment).filter(
            models.Payment.idempotency_key == payment_data.idempotency_key
        ).first()

        if existing_payment:
            if existing_payment.order_id != order.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key already used for another order"
                )

            return schemas.PaymentResponse(
                order_id=existing_payment.order_id,
                status=existing_payment.status,
                message="Payment already processed",
                transaction_id=existing_payment.transaction_id
            )


    transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"

    payment = models.Payment(
        order_id=order.id,
        amount=order.total_price,
        status="paid",
        transaction_id=transaction_id,
        idempotency_key=payment_data.idempotency_key,
        paid_at=datetime.now(timezone.utc)
    )

    order.status = "paid"

    payment_event = models.PaymentEvent(
        payment=payment,
        actor_user_id=current_user.id,
        event_type="payment_created",
        status=payment.status,
        event_metadata={
            "order_id": order.id,
            "amount": order.total_price,
            "transaction_id": payment.transaction_id,
        }
    )
    db.add(payment_event)
    db.commit()
    db.refresh(payment)

    return schemas.PaymentResponse(
        order_id=order.id,
        status=payment.status,
        message="Payment processed successfully",
        transaction_id=payment.transaction_id
    )
@router.post("/{order_id}/refund", response_model=schemas.PaymentResponse)
def refund_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """بازپرداخت سفارش پرداخت‌شده"""

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    payment = db.query(models.Payment).filter(
        models.Payment.order_id == order.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.status == "refunded":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment is already refunded"
        )

    if payment.status != "paid" or order.status != "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only paid payments can be refunded"
        )

    payment.status = "refunded"
    payment.refunded_at = datetime.now(timezone.utc)


    refund_event = models.PaymentEvent(
      payment=payment,
      actor_user_id=current_user.id,
      event_type="payment_refunded",
      status=payment.status,
      event_metadata={
          "order_id": order.id,
          "transaction_id": payment.transaction_id,
          "refunded_at": payment.refunded_at.isoformat()
          if payment.refunded_at else None,
     }
   )
    db.add(refund_event)

    db.commit()
    db.refresh(payment)

    return schemas.PaymentResponse(
        order_id=order.id,
        status=payment.status,
        message="Payment refunded successfully",
        transaction_id=payment.transaction_id
    )
