from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student, require_teacher
from app.models.assignment import Assignment
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.submission import Submission
from app.models.user import User
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionGrade,
    SubmissionResponse,
)

router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
)


# ============================================================
# STUDENT: SUBMIT ASSIGNMENT
# ============================================================

@router.post(
    "/assignment/{assignment_id}",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_assignment(
    assignment_id: UUID,
    submission_data: SubmissionCreate,
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

    existing_submission = (
        db.query(Submission)
        .filter(
            Submission.assignment_id == assignment_id,
            Submission.student_id == current_user.id,
        )
        .first()
    )

    if existing_submission is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already submitted this assignment",
        )

    submission = Submission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        content=submission_data.content,
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)

    return submission


# ============================================================
# STUDENT: VIEW MY SUBMISSIONS
# ============================================================

@router.get(
    "/my-submissions",
    response_model=list[SubmissionResponse],
)
def get_my_submissions(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    submissions = (
        db.query(Submission)
        .filter(Submission.student_id == current_user.id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    return submissions


# ============================================================
# STUDENT: VIEW ONE OF MY SUBMISSIONS
# ============================================================

@router.get(
    "/my/{submission_id}",
    response_model=SubmissionResponse,
)
def get_my_submission(
    submission_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    submission = (
        db.query(Submission)
        .filter(
            Submission.id == submission_id,
            Submission.student_id == current_user.id,
        )
        .first()
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return submission


# ============================================================
# TEACHER: VIEW ASSIGNMENT SUBMISSIONS
# ============================================================

@router.get(
    "/assignment/{assignment_id}",
    response_model=list[SubmissionResponse],
)
def get_assignment_submissions(
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

    submissions = (
        db.query(Submission)
        .filter(Submission.assignment_id == assignment_id)
        .order_by(Submission.submitted_at.asc())
        .all()
    )

    return submissions


# ============================================================
# TEACHER: VIEW ONE SUBMISSION
# ============================================================

@router.get(
    "/teacher/{submission_id}",
    response_model=SubmissionResponse,
)
def get_teacher_submission(
    submission_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    submission = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Submission.id == submission_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    return submission


# ============================================================
# TEACHER: GRADE SUBMISSION
# ============================================================

@router.patch(
    "/{submission_id}/grade",
    response_model=SubmissionResponse,
)
def grade_submission(
    submission_id: UUID,
    grade_data: SubmissionGrade,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    submission = (
        db.query(Submission)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .join(Course, Assignment.course_id == Course.id)
        .filter(
            Submission.id == submission_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if grade_data.score > submission.assignment.max_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Score cannot exceed {submission.assignment.max_score}",
        )

    submission.score = grade_data.score
    submission.feedback = grade_data.feedback
    submission.graded_at = datetime.utcnow()

    db.commit()
    db.refresh(submission)

    return submission