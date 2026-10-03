from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db

from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate

from app.core.dependencies import require_student, require_teacher

router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    course = Course(
        title=course_data.title,
        description=course_data.description,
        teacher_id=current_user.id,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course

@router.get(
    "/my-courses",
    response_model=list[CourseResponse],
)
def get_my_courses(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    courses = (
        db.query(Course)
        .filter(Course.teacher_id == current_user.id)
        .all()
    )

    return courses

@router.patch(
    "/{course_id}",
    response_model=CourseResponse,
)
def update_course(
    course_id: UUID,
    course_data: CourseUpdate,
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

    if course_data.title is not None:
        course.title = course_data.title

    if course_data.description is not None:
        course.description = course_data.description

    if course_data.is_published is not None:
        course.is_published = course_data.is_published

    db.commit()
    db.refresh(course)

    return course

@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_course(
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

    db.delete(course)
    db.commit()


@router.get(
    "/",
    response_model=list[CourseResponse],
)
def get_published_courses(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    courses = (
        db.query(Course)
        .filter(Course.is_published == True)
        .all()
    )

    return courses

@router.get(
    "/{course_id}",
    response_model=CourseResponse,
)
def get_course(
    course_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    course = (
        db.query(Course)
        .filter(
            Course.id == course_id,
            Course.is_published == True,
        )
        .first()
    )

    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found",
        )

    return course

@router.get(
    "/teacher/{course_id}",
    response_model=CourseResponse,
)
def get_teacher_course(
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

    return course