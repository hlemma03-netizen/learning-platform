from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.user import User
from app.schemas.lesson_progress import (
    CourseProgressResponse,
    LessonProgressResponse,
)

router = APIRouter(
    prefix="/progress",
    tags=["Progress"],
)


def verify_enrollment(
    course_id: UUID,
    student_id: UUID,
    db: Session,
):
    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.course_id == course_id,
            Enrollment.student_id == student_id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in the course",
        )


@router.post(
    "/lesson/{lesson_id}/complete",
    response_model=LessonProgressResponse,
)
def complete_lesson(
    lesson_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    lesson = (
        db.query(Lesson)
        .join(Course, Lesson.course_id == Course.id)
        .filter(
            Lesson.id == lesson_id,
            Lesson.is_published.is_(True),
            Course.is_published.is_(True),
        )
        .first()
    )

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    verify_enrollment(
        lesson.course_id,
        current_user.id,
        db,
    )

    progress = (
        db.query(LessonProgress)
        .filter(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )

    if progress is None:
        progress = LessonProgress(
            student_id=current_user.id,
            lesson_id=lesson_id,
            is_completed=True,
            completed_at=datetime.utcnow(),
        )
        db.add(progress)
    else:
        progress.is_completed = True
        progress.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)

    return progress


@router.get(
    "/lesson/{lesson_id}",
    response_model=LessonProgressResponse | None,
)
def get_lesson_progress(
    lesson_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    verify_enrollment(
        lesson.course_id,
        current_user.id,
        db,
    )

    return (
        db.query(LessonProgress)
        .filter(
            LessonProgress.student_id == current_user.id,
            LessonProgress.lesson_id == lesson_id,
        )
        .first()
    )


@router.get(
    "/course/{course_id}",
    response_model=CourseProgressResponse,
)
def get_course_progress(
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

    verify_enrollment(
        course_id,
        current_user.id,
        db,
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

    percentage = (
        round((completed_lessons / total_lessons) * 100, 2)
        if total_lessons > 0
        else 0.0
    )

    return CourseProgressResponse(
        course_id=course_id,
        total_lessons=total_lessons,
        completed_lessons=completed_lessons,
        completion_percentage=percentage,
        is_completed=(
            total_lessons > 0
            and completed_lessons == total_lessons
        ),
    )