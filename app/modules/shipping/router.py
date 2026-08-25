from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.shipping import models, schemas
from app.modules.user.models import User
from app.modules.user.router import get_current_admin_user

router = APIRouter(prefix="/shipping", tags=["Shipping"])


@router.patch("/{order_id}", response_model=schemas.ShippingResponse)
def update_shipping(
    order_id: int,
    shipping_data: schemas.ShippingUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """به‌روزرسانی اطلاعات حمل سفارش توسط مدیر"""

    shipping = db.query(models.Shipping).filter(
        models.Shipping.order_id == order_id
    ).first()

    if not shipping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipping record not found"
        )

    if shipping_data.carrier is not None:
        shipping.carrier = shipping_data.carrier

    if shipping_data.tracking_number is not None:
        shipping.tracking_number = shipping_data.tracking_number

    db.commit()
    db.refresh(shipping)

    return shipping
