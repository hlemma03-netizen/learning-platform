from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.dependencies import require_student

from app.core.security import verify_password, hash_password
from app.schemas.user import ChangePasswordRequest
from app.schemas.user import UserUpdate

from app.core.dependencies import get_current_user

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == login_data.email)
        .first()
    )

    if not user or not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.get("/student-test")
def student_test(
    current_user: User = Depends(require_student),
):
    return {
        "message": "Student access granted",
        "user": current_user.email,
    }

from app.core.dependencies import require_teacher, require_admin


@router.get("/teacher-test")
def teacher_test(
    current_user: User = Depends(require_teacher),
):
    return {
        "message": "Teacher access granted",
        "user": current_user.email,
    }


@router.get("/admin-test")
def admin_test(
    current_user: User = Depends(require_admin),
):
    return {
        "message": "Admin access granted",
        "user": current_user.email,
    }

@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user_data.first_name is not None:
        current_user.first_name = user_data.first_name

    if user_data.last_name is not None:
        current_user.last_name = user_data.last_name

    db.commit()
    db.refresh(current_user)

    return current_user

@router.patch("/me/password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(
        password_data.current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.password_hash = hash_password(
        password_data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully"
    }

@router.patch("/me/deactivate")
def deactivate_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.is_active = False

    db.commit()

    return {
        "message": "Account deactivated successfully"
    }

@router.get("/users", response_model=list[UserResponse])
def get_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).all()