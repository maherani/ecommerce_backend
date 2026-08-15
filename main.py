# مسیر فایل: app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.user.router import router as user_router

# این خط برای این است که تنظیمات اولیه لود شوند
from app.core.config import settings

# ساخت نمونه اصلی برنامه
app = FastAPI(
    title="E-Commerce API",
    description="Professional Headless E-Commerce API using FastAPI",
    version="1.0.0"
)

# تنظیمات CORS (Cross-Origin Resource Sharing)
# این تنظیمات اجازه می‌دهد که فرانت‌اند (مثل React یا Vue) که روی پورت دیگری است به API شما وصل شود
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # در زمان پروداکشن، این را به دامنه سایت خودتان تغییر دهید
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# اضافه کردن روتر کاربران به اپلیکیشن (این خط جا افتاده بود)
app.include_router(user_router)

# یک مسیر ساده برای تست سلامت سرور (Health Check)
@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "Welcome to E-Commerce Backend API!",
        "environment": "Development"
    }
