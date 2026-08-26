from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False,
        unique=True
    )

    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="pending")
    transaction_id = Column(String, nullable=True, unique=True)

    idempotency_key = Column(String, nullable=True, unique=True)

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    paid_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="payment")

    events = relationship(
        "PaymentEvent",
        back_populates="payment",
        cascade="all, delete-orphan"
    )

class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(
        Integer,
        ForeignKey("payments.id"),
        nullable=False
    )

    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    payment = relationship(
        "Payment",
        back_populates="events"
    )
