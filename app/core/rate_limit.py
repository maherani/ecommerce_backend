from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# استفاده از Redis برای ذخیره وضعیت درخواست‌های هر IP
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL
)
