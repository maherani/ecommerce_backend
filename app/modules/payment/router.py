import uuid
import hashlib
import hmac

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.order.models import Order
from app.modules.payment import models, schemas
from app.modules.user.models import User
from app.modules.user.router import get_current_user
from app.core.config import settings
from app.tasks.payment_tasks import process_payment_webhook

router = APIRouter(prefix="/payment", tags=["Payment"])

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    expected_signature = hmac.new(
        settings.PAYMENT_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)

@router.post("/webhook", response_model=schemas.PaymentResponse)
async def payment_webhook(
    payment_data: schemas.PaymentWebhookRequest,
    signature: str,
    db: Session = Depends(get_db),
):
    payload = payment_data.model_dump_json().encode()

    if not verify_webhook_signature(payload, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )

    existing_event = db.query(models.PaymentEvent).filter(
        models.PaymentEvent.event_id == payment_data.event_id
    ).first()

    if existing_event:
        return schemas.PaymentResponse(
            order_id=existing_event.payment.order_id,
            status=existing_event.status,
            message="Webhook already processed",
            transaction_id=existing_event.payment.transaction_id
        )

    payment = db.query(models.Payment).filter(
        models.Payment.transaction_id == payment_data.transaction_id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment_data.status not in {"paid", "refunded"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported payment status"
        )

    payment_event = models.PaymentEvent(
        payment=payment,
        actor_user_id=None,
        event_id=payment_data.event_id,
        event_type="webhook_received",
        status=payment.status,
        event_metadata={
            "event_id": payment_data.event_id,
            "transaction_id": payment_data.transaction_id,
            "webhook_status": payment_data.status,
            "source": "payment_webhook",
        }
    )

    db.add(payment_event)
    db.commit()

    process_payment_webhook.delay(payment_data.event_id)

    return schemas.PaymentResponse(
        order_id=payment.order_id,
        status=payment.status,
        message="Payment webhook queued for processing",
        transaction_id=payment.transaction_id
    )

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

@router.get(
    "/orders/{order_id}",
    response_model=schemas.PaymentDetailsResponse,
)
def get_order_payment(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """مشاهده اطلاعات پرداخت یک سفارش متعلق به کاربر جاری"""

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )

    payment = db.query(models.Payment).filter(
        models.Payment.order_id == order.id
    ).first()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    return payment




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
    order.status = "cancelled"


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
