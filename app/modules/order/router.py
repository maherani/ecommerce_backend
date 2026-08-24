from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.modules.order import models, schemas
from app.modules.cart.models import CartItem
from app.modules.user.models import User
from app.modules.user.router import get_current_user
from app.modules.product.models import Product

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post("/checkout", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def checkout(
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
