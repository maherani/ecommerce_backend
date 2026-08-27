from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.database import SessionLocal

from app.modules.user import models as user_models
from app.modules.product import models as product_models
from app.modules.cart import models as cart_models
from app.modules.order import models as order_models
from app.modules.shipping import models as shipping_models
from app.modules.payment import models as payment_models


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=1,
)
def process_payment_webhook(self, webhook_event_id: str) -> str:
    db = SessionLocal()

    try:
        webhook_event = (
            db.query(payment_models.PaymentEvent)
            .filter(
                payment_models.PaymentEvent.event_id == webhook_event_id
            )
            .first()
        )

        if not webhook_event:
            return f"Webhook event {webhook_event_id} not found"

        metadata = webhook_event.event_metadata or {}
        metadata["processing_status"] = "processing"
        webhook_event.event_metadata = metadata
        db.commit()

        transaction_id = metadata.get("transaction_id")
        webhook_status = metadata.get("webhook_status")

        if not transaction_id:
            raise ValueError("Webhook transaction_id is missing")

        if webhook_status not in {"paid", "refunded"}:
            raise ValueError(
                f"Unsupported webhook status: {webhook_status}"
            )

        payment = (
            db.query(payment_models.Payment)
            .filter(
                payment_models.Payment.transaction_id == transaction_id
            )
            .first()
        )

        if not payment:
            raise ValueError(
                f"Payment not found for transaction {transaction_id}"
            )

        order = (
            db.query(order_models.Order)
            .filter(
                order_models.Order.id == payment.order_id
            )
            .first()
        )

        if webhook_status == "paid":
            payment.status = "paid"

            if not payment.paid_at:
                payment.paid_at = datetime.now(timezone.utc)

            if order:
                order.status = "paid"

            webhook_event.event_type = "webhook_paid"

        elif webhook_status == "refunded":
            payment.status = "refunded"

            if not payment.refunded_at:
                payment.refunded_at = datetime.now(timezone.utc)

            if order:
                order.status = "cancelled"

            webhook_event.event_type = "webhook_refunded"

        metadata["processing_status"] = "processed"
        webhook_event.event_metadata = metadata
        webhook_event.status = payment.status

        db.commit()

        return f"Webhook {webhook_event_id} processed successfully"

    except ConnectionError as exc:
        db.rollback()

        if self.request.retries >= self.max_retries:
            webhook_event = (
                db.query(payment_models.PaymentEvent)
                .filter(
                    payment_models.PaymentEvent.event_id == webhook_event_id
                )
                .first()
            )

            if webhook_event:
                metadata = webhook_event.event_metadata or {}
                metadata["processing_status"] = "failed_after_retries"
                webhook_event.event_metadata = metadata
                db.commit()

            raise

        raise self.retry(exc=exc)

    finally:
        db.close()