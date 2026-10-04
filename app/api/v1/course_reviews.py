from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_teacher
from app.models.course import Course
from app.models.course_review import CourseReview
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.course_review import (
    CourseReviewCreate,
    CourseReviewResponse,
    CourseReviewUpdate,
)

router = APIRouter(
    prefix="/course-reviews",
    tags=["Course Reviews"],
)


@router.post(
    "/course/{course_id}",
    response_model=CourseReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    course_id: UUID,
    review_data: CourseReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role.value != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required",
        )

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
            detail="You must be enrolled in the course to review it",
        )

    existing_review = (
        db.query(CourseReview)
        .filter(
            CourseReview.course_id == course_id,
            CourseReview.student_id == current_user.id,
        )
        .first()
    )

    if existing_review is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this course",
        )

    review = CourseReview(
        course_id=course_id,
        student_id=current_user.id,
        rating=review_data.rating,
        comment=review_data.comment,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get(
    "/course/{course_id}",
    response_model=list[CourseReviewResponse],
)
def list_course_reviews(
    course_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter(Course.id == course_id).first()

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return (
        db.query(CourseReview)
        .filter(CourseReview.course_id == course_id)
        .order_by(CourseReview.created_at.desc())
        .all()
    )


@router.patch(
    "/{review_id}",
    response_model=CourseReviewResponse,
)
def update_review(
    review_id: UUID,
    review_data: CourseReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(CourseReview)
        .filter(
            CourseReview.id == review_id,
            CourseReview.student_id == current_user.id,
        )
        .first()
    )

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review_data.rating is not None:
        review.rating = review_data.rating

    if review_data.comment is not None:
        review.comment = review_data.comment

    db.commit()
    db.refresh(review)

    return review


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    review = (
        db.query(CourseReview)
        .filter(
            CourseReview.id == review_id,
            CourseReview.student_id == current_user.id,
        )
        .first()
    )

    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    db.delete(review)
    db.commit()


@router.get(
    "/teacher/{course_id}",
    response_model=list[CourseReviewResponse],
)
def teacher_view_course_reviews(
    course_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return (
        db.query(CourseReview)
        .filter(CourseReview.course_id == course_id)
        .order_by(CourseReview.created_at.desc())
        .all()
    )