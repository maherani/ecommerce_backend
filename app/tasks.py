from app.core.celery_app import celery_app
import time

@celery_app.task(name="send_order_email_task")
def send_order_email_task(email: str, order_id: int):
    """شبیه‌سازی ارسال ایمیل در پس‌زمینه"""
    time.sleep(5)
    print(f"-> Email successfully sent to {email} for Order ID: {order_id}")
    return f"Email sent to {email}"
