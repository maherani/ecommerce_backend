from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.order import models, schemas
from app.modules.cart.models import CartItem
from app.modules.user.models import User
from app.modules.user.router import get_current_user, get_current_admin_user
from app.modules.product.models import Product
from app.modules.shipping import models as shipping_models

# Allowed order status transitions.
ALLOWED_STATUS_TRANSITIONS = {
    "pending": {"paid", "cancelled"},
    "paid": {"processing"},
    "processing": {"shipped"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/checkout", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    checkout_data: schemas.CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تبدیل محتویات سبد خرید کاربر به سفارش و کم کردن اتمیک موجودی"""
    # ۱. دریافت آیتم‌های سبد خرید کاربر
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty"
        )

    # ۲. بررسی و کاهش اتمیک موجودی + ساخت آیتم‌های سفارش
    total_price = 0.0
    order_items = []

    for item in cart_items:
        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id,
                Product.stock_quantity >= item.quantity
            )
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {item.product_id}"
            )

        product.stock_quantity -= item.quantity

        item_total = product.price * item.quantity
        total_price += item_total

        order_item = models.OrderItem(
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price
        )
        order_items.append(order_item)

    # ۳. ثبت سفارش اصلی
    new_order = models.Order(
        user_id=current_user.id,
        total_price=total_price,
        status="pending",
        items=order_items
    )
    db.add(new_order)

    shipping = shipping_models.Shipping(
        order=new_order,
        address=checkout_data.address,
        city=checkout_data.city,
        postal_code=checkout_data.postal_code
    )
    db.add(shipping)
    # ۴. پاک‌سازی سبد خرید کاربر
    db.query(CartItem).filter(
        CartItem.user_id == current_user.id
    ).delete()

    db.commit()
    db.refresh(new_order)

    return new_order

@router.get("/", response_model=List[schemas.OrderResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """مشاهده تمام سفارش‌های ثبت‌شده توسط کاربر جاری"""
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).all()


@router.patch("/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(
    order_id: int,
    new_status: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """تغییر وضعیت سفارش توسط مدیر"""

    order = db.query(models.Order).filter(
        models.Order.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(order.status, set())

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition: "
                f"{order.status} -> {new_status}"
            )
        )

    order.status = new_status
    shipping = db.query(shipping_models.Shipping).filter(
        shipping_models.Shipping.order_id == order.id
    ).first()

    if new_status == "shipped":
       if shipping:
        shipping.shipped_at = datetime.now(timezone.utc)

    elif new_status == "delivered":
       if shipping:
           shipping.delivered_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)

    return order

@router.post("/{order_id}/cancel", response_model=schemas.OrderResponse)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """لغو سفارش pending و بازگرداندن موجودی محصولات"""

    # پیدا کردن سفارش متعلق به کاربر جاری
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.user_id == current_user.id
    ).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # فقط سفارش‌های pending قابل لغو هستند
    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending orders can be cancelled"
        )

    # بازگرداندن موجودی محصولات با row-level locking
    for item in order.items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .with_for_update()
            .first()
        )

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )

        product.stock_quantity += item.quantity

    # تغییر وضعیت سفارش
    order.status = "cancelled"

    db.commit()
    db.refresh(order)

    return order
