from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # تنظیمات دیتابیس
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str

    # تنظیمات امنیتی
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    @property
    def DATABASE_URL(self) -> str:
        # ساخت URL اتصال به دیتابیس برای SQLAlchemy به صورت خودکار
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        extra = "ignore"  # این خط اضافه شد تا متغیرهای اضافی در فایل env خطا ایجاد نکنند
# یک نمونه گلوبال از تنظیمات می‌سازیم تا در همه جای برنامه استفاده کنیم
settings = Settings()
