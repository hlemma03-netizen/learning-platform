from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student, require_teacher
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.models.enrollment import Enrollment

router = APIRouter(
    prefix="/lessons",
    tags=["Lessons"],
)


@router.post(
    "/course/{course_id}",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    course_id: UUID,
    lesson_data: LessonCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    # Check that the course exists and belongs to this teacher
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

    lesson = Lesson(
        course_id=course.id,
        title=lesson_data.title,
        description=lesson_data.description,
        content=lesson_data.content,
        order=lesson_data.order,
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson

@router.get(
    "/course/{course_id}",
    response_model=list[LessonResponse],
)
def get_course_lessons(
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

    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == course_id)
        .order_by(Lesson.order)
        .all()
    )

    return lessons

@router.patch(
    "/{lesson_id}",
    response_model=LessonResponse,
)
def update_lesson(
    lesson_id: UUID,
    lesson_data: LessonUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    lesson = (
        db.query(Lesson)
        .join(Course, Lesson.course_id == Course.id)
        .filter(
            Lesson.id == lesson_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    if lesson_data.title is not None:
        lesson.title = lesson_data.title

    if lesson_data.description is not None:
        lesson.description = lesson_data.description

    if lesson_data.content is not None:
        lesson.content = lesson_data.content

    if lesson_data.order is not None:
        lesson.order = lesson_data.order

    if lesson_data.is_published is not None:
        lesson.is_published = lesson_data.is_published

    db.commit()
    db.refresh(lesson)

    return lesson

@router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lesson(
    lesson_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    lesson = (
        db.query(Lesson)
        .join(Course, Lesson.course_id == Course.id)
        .filter(
            Lesson.id == lesson_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found",
        )

    db.delete(lesson)
    db.commit()

    return None

@router.get(
    "/student/course/{course_id}",
    response_model=list[LessonResponse],
)
def get_student_course_lessons(
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
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == course_id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in this course",
        )

    lessons = (
        db.query(Lesson)
        .filter(
            Lesson.course_id == course_id,
            Lesson.is_published.is_(True),
        )
        .order_by(Lesson.order)
        .all()
    )

    return lessons
    

@router.get(
    "/student/{lesson_id}",
    response_model=LessonResponse,
)
def get_student_lesson(
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

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == lesson.course_id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in this course",
        )

    return lesson