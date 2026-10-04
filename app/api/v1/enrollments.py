from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enrollment import EnrollmentResponse


router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"],
)


@router.post(
    "/course/{course_id}",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def enroll_in_course(
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

    existing_enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )

    if existing_enrollment is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already enrolled in this course",
        )

    enrollment = Enrollment(
        student_id=current_user.id,
        course_id=course_id,
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)

    return enrollment


@router.get(
    "/my-enrollments",
    response_model=list[EnrollmentResponse],
)
def get_my_enrollments(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    enrollments = (
        db.query(Enrollment)
        .filter(Enrollment.student_id == current_user.id)
        .order_by(Enrollment.enrolled_at.desc())
        .all()
    )

    return enrollments


@router.get(
    "/{enrollment_id}",
    response_model=EnrollmentResponse,
)
def get_my_enrollment(
    enrollment_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.id == enrollment_id,
            Enrollment.student_id == current_user.id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found",
        )

    return enrollment