
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

# اسکیمای جدید برای ورود کاربر
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# اسکیمای خروجی توکن
class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_superuser: bool

    class Config:
        from_attributes = True
