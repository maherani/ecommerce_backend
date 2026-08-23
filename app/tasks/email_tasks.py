import time
from app.core.celery_app import celery_app

@celery_app.task(name="send_welcome_email_task")
def send_welcome_email_task(email: str, username: str):
    # اینجا فرض می‌کنیم ۵ ثانیه طول می‌کشد تا به سرور ایمیل وصل شویم و ایمیل را بفرستیم
    print(f"⏳ در حال ارسال ایمیل به {email} ...")
    time.sleep(5)
    
    print("========================================")
    print(f"✅ ایمیل خوش‌آمدگویی به {email} ({username}) با موفقیت ارسال شد!")
    print("========================================")
    
    return {"status": "success", "email": email}
