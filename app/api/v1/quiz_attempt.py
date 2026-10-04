from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student, require_teacher
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.question import Question, QuestionType
from app.models.quiz import Quiz
from app.models.quiz_attempt import QuizAttempt, QuizAttemptStatus
from app.models.quiz_option import QuizOption
from app.models.attempt_answer import AttemptAnswer
from app.models.user import User
from app.schemas.quiz import (
    AttemptAnswerResponse,
    QuizAttemptResponse,
    QuizSubmit,
    ShortAnswerGrade,
)

router = APIRouter(
    prefix="/quiz-attempts",
    tags=["Quiz Attempts"],
)


# ============================================================
# STUDENT: START QUIZ
# ============================================================

@router.post(
    "/quiz/{quiz_id}/start",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
)
def start_quiz(
    quiz_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(Quiz)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            Quiz.id == quiz_id,
            Quiz.is_published.is_(True),
            Course.is_published.is_(True),
        )
        .first()
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    enrollment = (
        db.query(Enrollment)
        .filter(
            Enrollment.student_id == current_user.id,
            Enrollment.course_id == quiz.course_id,
        )
        .first()
    )

    if enrollment is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be enrolled in this course",
        )

    completed_attempts = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == current_user.id,
            QuizAttempt.status == QuizAttemptStatus.SUBMITTED,
        )
        .count()
    )

    if completed_attempts >= quiz.max_attempts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of attempts reached",
        )

    # Prevent multiple unfinished attempts at the same time.
    active_attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.student_id == current_user.id,
            QuizAttempt.status == QuizAttemptStatus.IN_PROGRESS,
        )
        .first()
    )

    if active_attempt is not None:
        return active_attempt

    attempt = QuizAttempt(
        quiz_id=quiz_id,
        student_id=current_user.id,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


# ============================================================
# STUDENT: SUBMIT QUIZ
# ============================================================

@router.post(
    "/{attempt_id}/submit",
    response_model=QuizAttemptResponse,
)
def submit_quiz(
    attempt_id: UUID,
    submission: QuizSubmit,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.student_id == current_user.id,
        )
        .first()
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    if attempt.status == QuizAttemptStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This quiz attempt has already been submitted",
        )

    quiz = attempt.quiz

    # Check time limit.
    if quiz.time_limit_minutes is not None:
        deadline = attempt.started_at + timedelta(
            minutes=quiz.time_limit_minutes
        )

        if datetime.utcnow() > deadline:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quiz time limit has expired",
            )

    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz.id)
        .all()
    )

    question_map = {question.id: question for question in questions}

    # Prevent duplicate question answers in one submission.
    submitted_question_ids = [
        answer.question_id for answer in submission.answers
    ]

    if len(submitted_question_ids) != len(set(submitted_question_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A question can only be answered once",
        )

    total_score = 0

    for submitted_answer in submission.answers:
        question = question_map.get(submitted_answer.question_id)

        if question is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question does not belong to this quiz",
            )

        # ----------------------------------------------------
        # MULTIPLE CHOICE / TRUE-FALSE
        # ----------------------------------------------------

        if question.question_type in (
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        ):
            if submitted_answer.selected_option_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Question {question.id} requires "
                        "an option selection"
                    ),
                )

            option = (
                db.query(QuizOption)
                .filter(
                    QuizOption.id == submitted_answer.selected_option_id,
                    QuizOption.question_id == question.id,
                )
                .first()
            )

            if option is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Selected option does not belong to this question",
                )

            is_correct = option.is_correct
            points_awarded = question.points if is_correct else 0

        # ----------------------------------------------------
        # SHORT ANSWER
        # ----------------------------------------------------

        else:
            if not submitted_answer.answer_text:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Question {question.id} requires "
                        "an answer"
                    ),
                )

            # Short answers require teacher grading.
            is_correct = None
            points_awarded = 0

        attempt_answer = AttemptAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=submitted_answer.selected_option_id,
            answer_text=submitted_answer.answer_text,
            is_correct=is_correct,
            points_awarded=points_awarded,
        )

        db.add(attempt_answer)

        total_score += points_awarded

    attempt.score = total_score
    attempt.status = QuizAttemptStatus.SUBMITTED
    attempt.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)

    return attempt


# ============================================================
# STUDENT: MY ATTEMPTS
# ============================================================

@router.get(
    "/my-attempts",
    response_model=list[QuizAttemptResponse],
)
def get_my_attempts(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.student_id == current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )


# ============================================================
# STUDENT: GET ONE ATTEMPT
# ============================================================

@router.get(
    "/my/{attempt_id}",
    response_model=QuizAttemptResponse,
)
def get_my_attempt(
    attempt_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.student_id == current_user.id,
        )
        .first()
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    return attempt


# ============================================================
# STUDENT: VIEW ANSWERS FOR ATTEMPT
# ============================================================

@router.get(
    "/my/{attempt_id}/answers",
    response_model=list[AttemptAnswerResponse],
)
def get_my_attempt_answers(
    attempt_id: UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(QuizAttempt)
        .filter(
            QuizAttempt.id == attempt_id,
            QuizAttempt.student_id == current_user.id,
        )
        .first()
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    return (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id)
        .all()
    )


# ============================================================
# TEACHER: VIEW QUIZ ATTEMPTS
# ============================================================

@router.get(
    "/quiz/{quiz_id}",
    response_model=list[QuizAttemptResponse],
)
def get_quiz_attempts(
    quiz_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    quiz = (
        db.query(Quiz)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            Quiz.id == quiz_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if quiz is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz not found",
        )

    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.quiz_id == quiz_id)
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )


# ============================================================
# TEACHER: VIEW ONE ATTEMPT
# ============================================================

@router.get(
    "/teacher/{attempt_id}",
    response_model=QuizAttemptResponse,
)
def get_teacher_attempt(
    attempt_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            QuizAttempt.id == attempt_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    return attempt


# ============================================================
# TEACHER: VIEW ATTEMPT ANSWERS
# ============================================================

@router.get(
    "/teacher/{attempt_id}/answers",
    response_model=list[AttemptAnswerResponse],
)
def get_teacher_attempt_answers(
    attempt_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(QuizAttempt)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            QuizAttempt.id == attempt_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if attempt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quiz attempt not found",
        )

    return (
        db.query(AttemptAnswer)
        .filter(AttemptAnswer.attempt_id == attempt_id)
        .all()
    )

# ============================================================
# TEACHER: GRADE SHORT-ANSWER QUESTION
# ============================================================

@router.patch(
    "/answers/{answer_id}/grade",
    response_model=AttemptAnswerResponse,
)
def grade_short_answer(
    answer_id: UUID,
    grade_data: ShortAnswerGrade,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    answer = (
        db.query(AttemptAnswer)
        .join(QuizAttempt, AttemptAnswer.attempt_id == QuizAttempt.id)
        .join(Quiz, QuizAttempt.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            AttemptAnswer.id == answer_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found",
        )

    if answer.question.question_type != QuestionType.SHORT_ANSWER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only short-answer questions require teacher grading",
        )

    if grade_data.points_awarded > answer.question.points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Points cannot exceed {answer.question.points}",
        )

    answer.is_correct = grade_data.is_correct
    answer.points_awarded = grade_data.points_awarded

    # Recalculate the complete attempt score.
    attempt = answer.attempt

    total_score = sum(
        item.points_awarded
        for item in attempt.answers
    )

    attempt.score = total_score

    db.commit()
    db.refresh(answer)

    return answer