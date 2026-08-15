from sqlalchemy.orm import Session
from app.modules.user.models import User
from app.modules.user.schemas import UserCreate
from app.core.security import get_password_hash
from passlib.context import CryptContext

# تنظیمات برای هش کردن امن پسورد
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(db: Session, user: UserCreate):
    # هش کردن پسورد قبل از ذخیره در دیتابیس برای امنیت بالا
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)  # برای دریافت ID تولید شده توسط دیتابیس
    return db_user


def get_password_hash(password: str) -> str:
    # محدود کردن پسورد به حداکثر ۷۲ بایت برای جلوگیری از خطای bcrypt
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def get_user_by_email(db: Session, email: str):
    # جستجوی کاربر بر اساس ایمیل در دیتابیس
    return db.query(User).filter(User.email == email).first()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

