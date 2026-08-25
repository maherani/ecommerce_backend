from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_price = Column(Float, nullable=False, default=0.0)
    status = Column(String, default="pending") # وضعیت‌های ممکن: pending, paid, shipped, cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
    # رابطه با آیتم‌های سفارش
    shipping = relationship(
        "Shipping",
        back_populates="order",
        uselist=False,
        cascade="all, delete-orphan"
    )
    payment = relationship(
        "Payment",
         back_populates="order",
         uselist=False,
         cascade="all, delete-orphan"
    )

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False) # ذخیره قیمت محصول در لحظه ثبت سفارش

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
