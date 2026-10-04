import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.user import User
from app.schemas.certificate import CertificateResponse

router = APIRouter(
    prefix="/certificates",
    tags=["Certificates"],
)


def generate_certificate_number() -> str:
    return f"ELP-{secrets.token_hex(6).upper()}"


@router.post(
    "/course/{course_id}",
    response_model=CertificateResponse,
    status_code=status.HTTP_201_CREATED,
)
def issue_certificate(
    course_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.is_published.is_(True),
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.student_id == current_user.id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in the course",
        )

    total_lessons = (
        db.query(func.count(Lesson.id))
        .filter(
            Lesson.course_id == course_id,
            Lesson.is_published.is_(True),
        )
        .scalar()
        or 0
    )

    completed_lessons = (
        db.query(func.count(LessonProgress.id))
        .join(Lesson, LessonProgress.lesson_id == Lesson.id)
        .filter(
            LessonProgress.student_id == current_user.id,
            LessonProgress.is_completed.is_(True),
            Lesson.course_id == course_id,
            Lesson.is_published.is_(True),
        )
        .scalar()
        or 0
    )

    if total_lessons == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course has no published lessons",
        )

    if completed_lessons != total_lessons:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complete all published lessons before requesting a certificate",
        )

    existing_certificate = (
        db.query(Certificate)
        .filter(
            Certificate.course_id == course_id,
            Certificate.student_id == current_user.id,
        )
        .first()
    )

    if existing_certificate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Certificate already issued",
        )

    certificate = Certificate(
        student_id=current_user.id,
        course_id=course_id,
        certificate_number=generate_certificate_number(),
    )

    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    return certificate


@router.get(
    "/my",
    response_model=list[CertificateResponse],
)
def get_my_certificates(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return (
        db.query(Certificate)
        .filter(Certificate.student_id == current_user.id)
        .order_by(Certificate.issued_at.desc())
        .all()
    )


@router.get(
    "/{certificate_id}",
    response_model=CertificateResponse,
)
def get_certificate(
    certificate_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.id == certificate_id,
            Certificate.student_id == current_user.id,
        )
        .first()
    )

    if certificate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found",
        )

    return certificate