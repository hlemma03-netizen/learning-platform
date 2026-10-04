from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student, require_teacher
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate


router = APIRouter(
    prefix="/courses",
    tags=["Courses"],
)


# --------------------------------------------------
# TEACHER: Create a course
# --------------------------------------------------

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


# --------------------------------------------------
# TEACHER: Get my courses
# --------------------------------------------------

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


# --------------------------------------------------
# TEACHER: Update my course
# --------------------------------------------------

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


# --------------------------------------------------
# TEACHER: Delete my course
# --------------------------------------------------

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

    return None


# --------------------------------------------------
# STUDENT: Get all published courses
# --------------------------------------------------

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
        .filter(Course.is_published.is_(True))
        .all()
    )

    result = []

    for course in courses:
        enrollment = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == current_user.id,
                Enrollment.course_id == course.id,
            )
            .first()
        )

        result.append(
            CourseResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                teacher_id=course.teacher_id,
                is_published=course.is_published,
                is_enrolled=enrollment is not None,
            )
        )

    return result


# --------------------------------------------------
# STUDENT: Get one published course
# --------------------------------------------------

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
            Enrollment.course_id == course.id,
        )
        .first()
    )

    return CourseResponse(
        id=course.id,
        title=course.title,
        description=course.description,
        teacher_id=course.teacher_id,
        is_published=course.is_published,
        is_enrolled=enrollment is not None,
    )

# --------------------------------------------------
# TEACHER: Get one of my courses
# --------------------------------------------------

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