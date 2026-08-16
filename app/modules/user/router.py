# app/modules/user/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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
    user_credentials: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """
    Authenticate a user and return a JWT access token.
    """

    # Find the user by email.
    user = crud.get_user_by_email(
        db,
        email=user_credentials.email,
    )

    # Reject the request if the user does not exist or the password is wrong.
    if not user or not crud.verify_password(
        user_credentials.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a JWT containing the user's email as the subject.
    access_token = create_access_token(
        data={"sub": user.email},
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
