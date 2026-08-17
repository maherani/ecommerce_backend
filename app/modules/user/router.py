# app/modules/user/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer , OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.modules.user import crud, schemas


# Router for all user-related endpoints.
router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "/",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user.

    The email must be unique. The password is hashed inside the CRUD layer
    before the user is stored in PostgreSQL.
    """

    # Check whether a user with this email already exists.
    db_user = crud.get_user_by_email(
        db,
        email=user.email,
    )

    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create and persist the new user.
    new_user = crud.create_user(
        db=db,
        user=user,
    )

    return new_user

@router.post(
    "/login",
    response_model=schemas.Token,
)
def login_user(
    # تغییر از UserLogin به فرم استاندارد OAuth2
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    (Using standard OAuth2 form data for Swagger compatibility)
    """

    # فرم استاندارد از فیلد username استفاده می‌کند، ما ایمیل را درون آن قرار می‌دهیم
    user = crud.get_user_by_email(
        db,
        email=form_data.username,
    )

    if not user or not crud.verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.email},
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# مسیر دریافت توکن برای Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    تزریق وابستگی برای دریافت کاربر فعلی از طریق توکن
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # رمزگشایی توکن
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # جستجوی کاربر در دیتابیس
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
        
    return user

@router.get(
    "/me",
    response_model=schemas.UserResponse,
)

def read_users_me(
    current_user = Depends(get_current_user)
):
    """
    دریافت اطلاعات پروفایل کاربر لاگین شده (مسیر محافظت‌شده)
    """
    return current_user


def get_current_admin_user(
    current_user = Depends(get_current_user)
):
    """
    تزریق وابستگی برای بررسی سطح دسترسی مدیر (Superuser)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


@router.get(
    "/admin-only",
    response_model=schemas.UserResponse,
)
def read_admin_data(
    current_admin = Depends(get_current_admin_user)
):
    """
    مسیر محافظت‌شده اختصاصی فقط برای کاربران مدیر
    """
    return current_admin
