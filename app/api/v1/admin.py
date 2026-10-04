from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminCoursePublishUpdate,
    AdminCourseResponse,
    AdminUserResponse,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    PlatformStatsResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ---------------------------------------------------------
# USER MANAGEMENT
# ---------------------------------------------------------

@router.get(
    "/users",
    response_model=list[AdminUserResponse],
)
def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch(
    "/users/{user_id}/role",
    response_model=AdminUserResponse,
)
def update_user_role(
    user_id: UUID,
    role_data: AdminUserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id and role_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin role",
        )

    user.role = role_data.role

    db.commit()
    db.refresh(user)

    return user


@router.patch(
    "/users/{user_id}/status",
    response_model=AdminUserResponse,
)
def update_user_status(
    user_id: UUID,
    status_data: AdminUserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account",
        )

    user.is_active = status_data.is_active

    db.commit()
    db.refresh(user)

    return user


# ---------------------------------------------------------
# COURSE MANAGEMENT
# ---------------------------------------------------------

@router.get(
    "/courses",
    response_model=list[AdminCourseResponse],
)
def list_all_courses(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(Course).order_by(Course.created_at.desc()).all()


@router.patch(
    "/courses/{course_id}/publish",
    response_model=AdminCourseResponse,
)
def update_course_publication(
    course_id: UUID,
    publish_data: AdminCoursePublishUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    course.is_published = publish_data.is_published

    db.commit()
    db.refresh(course)

    return course


# ---------------------------------------------------------
# PLATFORM STATISTICS
# ---------------------------------------------------------

@router.get(
    "/stats",
    response_model=PlatformStatsResponse,
)
def platform_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_users = db.query(func.count(User.id)).scalar() or 0

    total_students = (
        db.query(func.count(User.id))
        .filter(User.role == UserRole.STUDENT)
        .scalar()
        or 0
    )

    total_teachers = (
        db.query(func.count(User.id))
        .filter(User.role == UserRole.TEACHER)
        .scalar()
        or 0
    )

    total_admins = (
        db.query(func.count(User.id))
        .filter(User.role == UserRole.ADMIN)
        .scalar()
        or 0
    )

    active_users = (
        db.query(func.count(User.id))
        .filter(User.is_active.is_(True))
        .scalar()
        or 0
    )

    total_courses = db.query(func.count(Course.id)).scalar() or 0

    published_courses = (
        db.query(func.count(Course.id))
        .filter(Course.is_published.is_(True))
        .scalar()
        or 0
    )

    total_enrollments = (
        db.query(func.count(Enrollment.id)).scalar() or 0
    )

    total_assignments = (
        db.query(func.count(Assignment.id)).scalar() or 0
    )

    total_submissions = (
        db.query(func.count(Submission.id)).scalar() or 0
    )

    total_quizzes = (
        db.query(func.count(Quiz.id)).scalar() or 0
    )

    total_quiz_attempts = (
        db.query(func.count(QuizAttempt.id)).scalar() or 0
    )

    return PlatformStatsResponse(
        total_users=total_users,
        total_students=total_students,
        total_teachers=total_teachers,
        total_admins=total_admins,
        active_users=active_users,
        total_courses=total_courses,
        published_courses=published_courses,
        total_enrollments=total_enrollments,
        total_assignments=total_assignments,
        total_submissions=total_submissions,
        total_quizzes=total_quizzes,
        total_quiz_attempts=total_quiz_attempts,
    )