from fastapi import APIRouter
from app.tasks.email_tasks import send_welcome_email_task

router = APIRouter()

@router.post("/test-email")
def test_background_email(email: str, username: str):
    
    # فراخوانی تسک در پس‌زمینه - اجرای این خط کمتر از ۱ میلی‌ثانیه زمان می‌برد!
    send_welcome_email_task.delay(email=email, username=username)
    
    return {
        "message": "درخواست دریافت شد. ایمیل در پس‌زمینه ارسال خواهد شد.",
        "email": email
    }
