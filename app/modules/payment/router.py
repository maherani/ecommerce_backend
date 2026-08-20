import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.order.models import Order
from app.modules.payment import schemas
from app.modules.user.models import User
from app.modules.user.router import get_current_user

router = APIRouter(prefix="/payment", tags=["Payment"])

@router.post("/process", response_model=schemas.PaymentResponse)
def process_payment(
    payment_data: schemas.PaymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """شبیه‌سازی عملیات پرداخت آنلاین برای سفارش"""
    # ۱. بررسی وجود سفارش برای کاربر جاری
    order = db.query(Order).filter(
        Order.id == payment_data.order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # ۲. بررسی پرداخت‌شده بودن سفارش
    if order.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Order is already paid"
        )

    # ۳. تغییر وضعیت سفارش به paid
    order.status = "paid"
    db.commit()

    # ۴. تولید کد پیگیری ساختگی
    transaction_id = f"TRX-{uuid.uuid4().hex[:8].upper()}"

    return schemas.PaymentResponse(
        order_id=order.id,
        status="paid",
        message="Payment processed successfully",
        transaction_id=transaction_id
    )
