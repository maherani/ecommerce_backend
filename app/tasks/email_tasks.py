from app.core.celery_app import celery_app
import time

@celery_app.task(name="send_welcome_email_task")
def send_welcome_email_task(email: str, username: str):
    # شبیه‌سازی یک پردازش زمان‌بر (مثلاً ارسال ایمیل)
    time.sleep(5)
    print(f"========================================")
    print(f" ایمیل خوش‌آمدگویی به {email} ({username}) ارسال شد! ")
    print(f"========================================")
    return {"status": "success", "email": email}
