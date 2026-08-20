# مسیر فایل: app/main.py

from fastapi import FastAPI
from app.core.database import Base, engine
# ۱. ابتدا تمام مدل‌ها باید ایمپورت شوند
from app.modules.user import models as user_models
from app.modules.product import models as product_models
from app.modules.cart import models as cart_models
from app.modules.order import models as order_models
from fastapi.middleware.cors import CORSMiddleware

# ۲. سپس دستور ساخت جداول اجرا شود
Base.metadata.create_all(bind=engine)


# ۳. ایمپورت روترها
from app.modules.product import models as product_models
from app.modules.user.router import router as user_router
from app.modules.product.router import router as product_router  # اضافه شدن این خط
from app.modules.cart.router import router as cart_router
from app.modules.order.router import router as order_router
from app.modules.payment.router import router as payment_router  # اضافه شد
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
app.include_router(product_router)  # اضافه شدن این خط
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(payment_router)  # اضافه شد
# یک مسیر ساده برای تست سلامت سرور (Health Check)
@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "Welcome to E-Commerce Backend API!",
        "environment": "Development"
    }
