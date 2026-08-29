# مسیر فایل: app/main.py
from app.core.config import settings, validate_security_settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.database import Base, engine
# ۱. ابتدا تمام مدل‌ها باید ایمپورت شوند
from app.modules.user import models as user_models
from app.modules.product import models as product_models
from app.modules.cart import models as cart_models
from app.modules.order import models as order_models
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter
from app.modules.shipping.router import router as shipping_router
# ۲. سپس دستور ساخت جداول اجرا شود
#Base.metadata.create_all(bind=engine)


# ۳. ایمپورت روترها
from app.modules.user.router import router as user_router
from app.modules.product.router import router as product_router  # اضافه شدن این خط
from app.modules.cart.router import router as cart_router
from app.modules.order.router import router as order_router
from app.modules.payment.router import router as payment_router  # اضافه شد
# این خط برای این است که تنظیمات اولیه لود شوند

# ساخت نمونه اصلی برنامه

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
        },
    )

app = FastAPI(
    title="E-Commerce API",
    description="Professional Headless E-Commerce API using FastAPI",
    version="1.0.0"
)


validate_security_settings()


app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)
app.add_middleware(SecurityHeadersMiddleware)

# تنظیمات CORS (Cross-Origin Resource Sharing)
# این تنظیمات اجازه می‌دهد که فرانت‌اند (مثل React یا Vue) که روی پورت دیگری است به API شما وصل شود
cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# اضافه کردن روتر کاربران به اپلیکیشن (این خط جا افتاده بود)
app.include_router(user_router)
app.include_router(product_router)  # اضافه شدن این خط
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(payment_router)  # اضافه شد
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(shipping_router)

# یک مسیر ساده برای تست سلامت سرور (Health Check)
@app.get("/")
def health_check():
    return {
        "status": "success",
        "message": "Welcome to E-Commerce Backend API!",
        "environment": "Development"
    }
