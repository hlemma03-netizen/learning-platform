from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student, require_teacher
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.user import User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)

router = APIRouter(
    prefix="/assignments",
    tags=["Assignments"],
)


# ============================================================
# TEACHER ENDPOINTS
# ============================================================

@router.post(
    "/course/{course_id}",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    course_id: UUID,
    assignment_data: AssignmentCreate,
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

    # If a lesson is provided, make sure it belongs to this course.
    if assignment_data.lesson_id is not None:
        lesson = (
            db.query(Lesson)
            .filter(
                Lesson.id == assignment_data.lesson_id,
                Lesson.course_id == course_id,
            )
            .first()
        )

        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson does not belong to this course",
            )

    assignment = Assignment(
        course_id=course_id,
        lesson_id=assignment_data.lesson_id,
        title=assignment_data.title,
        description=assignment_data.description,
        instructions=assignment_data.instructions,
        due_date=assignment_data.due_date,
        max_score=assignment_data.max_score,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


@router.get(
    "/course/{course_id}",
    response_model=list[AssignmentResponse],
)
def get_course_assignments(
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

    assignments = (
        db.query(Assignment)
        .filter(Assignment.course_id == course_id)
        .order_by(Assignment.created_at.desc())
        .all()
    )

    return assignments


@router.get(
    "/teacher/{assignment_id}",
    response_model=AssignmentResponse,
)
def get_teacher_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(Assignment)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Assignment.id == assignment_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return assignment


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentResponse,
)
def update_assignment(
    assignment_id: UUID,
    assignment_data: AssignmentUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(Assignment)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Assignment.id == assignment_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    update_data = assignment_data.model_dump(exclude_unset=True)

    # Validate lesson if it is being changed.
    if "lesson_id" in update_data and update_data["lesson_id"] is not None:
        lesson = (
            db.query(Lesson)
            .filter(
                Lesson.id == update_data["lesson_id"],
                Lesson.course_id == assignment.course_id,
            )
            .first()
        )

        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson does not belong to this course",
            )

    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)

    return assignment


@router.delete(
    "/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(Assignment)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Assignment.id == assignment_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    db.delete(assignment)
    db.commit()

    return None


# ============================================================
# STUDENT ENDPOINTS
# ============================================================

@router.get(
    "/student/course/{course_id}",
    response_model=list[AssignmentResponse],
)
def get_student_course_assignments(
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

    assignments = (
        db.query(Assignment)
        .filter(Assignment.course_id == course_id)
        .order_by(Assignment.due_date.asc().nullslast())
        .all()
    )

    return assignments


@router.get(
    "/student/{assignment_id}",
    response_model=AssignmentResponse,
)
def get_student_assignment(
    assignment_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    assignment = (
        db.query(Assignment)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Assignment.id == assignment_id,
            Course.is_published.is_(True),
        )
        .first()
    )

    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == assignment.course_id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in this course",
        )

    return assignment