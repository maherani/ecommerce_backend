# مسیر فایل: app/core/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# وارد کردن تنظیماتی که قبلا در config.py ساختیم
from app.core.config import settings

# ساخت موتور دیتابیس (Engine)
# تنظیمات pool_size و max_overflow برای مدیریت تعداد کاربران همزمان (پرفورمنس) بسیار مهم است
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True, # این گزینه قبل از اجرای کوئری چک می‌کند که ارتباط قطع نشده باشد
    pool_size=10,       # تعداد اتصالات همزمان پایه
    max_overflow=20     # تعداد اتصالات همزمان اضافی در صورت ترافیک بالا
)

# ساخت کلاس Session که در کل برنامه برای کار با دیتابیس استفاده خواهد شد
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# کلاس پایه برای مدل‌های SQLAlchemy (همه جداول دیتابیس از این کلاس ارث‌بری خواهند کرد)
Base = declarative_base()

# یک Generator برای مدیریت هوشمند باز و بسته کردن Session در هر Request (الگوی Dependency Injection)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # پس از پایان پردازش، سشن را می‌بندد تا منابع سرور آزاد شود
