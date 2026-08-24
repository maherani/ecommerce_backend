# app/modules/user/router.py

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password
from app.modules.user import crud, schemas
from app.tasks.email_tasks import send_welcome_email_task

logger = logging.getLogger(__name__)

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
    Create a new user and queue the welcome-email task.

    The registration response must not depend on the worker being available,
    so a task-delivery failure is logged without rolling back the user.
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

    try:
        # Queue the slow welcome-email work outside the request/response cycle.
        send_welcome_email_task.delay(new_user.email, new_user.email)
    except Exception:
        logger.exception(
            "Welcome email could not be queued for newly registered user",
            extra={"user_id": new_user.id},
        )

    return new_user


@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    (Using standard OAuth2 form data for Swagger compatibility)
    """

    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# Token endpoint for Swagger.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Resolve the authenticated user from a JWT bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    return user


@router.get(
    "/me",
    response_model=schemas.UserResponse,
)
def read_users_me(
    current_user=Depends(get_current_user),
):
    """Return the profile of the authenticated user."""
    return current_user


def get_current_admin_user(
    current_user=Depends(get_current_user),
):
    """Authorize a superuser for admin-only operations."""
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
    current_admin=Depends(get_current_admin_user),
):
    """Return protected admin-only data."""
    return current_admin
