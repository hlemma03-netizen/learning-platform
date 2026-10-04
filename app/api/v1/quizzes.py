from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_student, require_teacher
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.question import Question, QuestionType
from app.models.quiz import Quiz
from app.models.quiz_option import QuizOption
from app.models.user import User
from app.schemas.quiz import (
    QuestionCreate,
    QuestionResponse,
    QuestionUpdate,
    QuizCreate,
    QuizOptionCreate,
    QuizOptionResponse,
    QuizOptionUpdate,
    QuizResponse,
    QuizUpdate,
)

router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
)


# ============================================================
# TEACHER: CREATE QUIZ
# ============================================================

@router.post(
    "/course/{course_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    course_id: UUID,
    quiz_data: QuizCreate,
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

    if quiz_data.lesson_id is not None:
        lesson = (
            db.query(Lesson)
            .filter(
                Lesson.id == quiz_data.lesson_id,
                Lesson.course_id == course_id,
            )
            .first()
        )

        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson does not belong to this course",
            )

    quiz = Quiz(
        course_id=course_id,
        lesson_id=quiz_data.lesson_id,
        title=quiz_data.title,
        description=quiz_data.description,
        time_limit_minutes=quiz_data.time_limit_minutes,
        max_attempts=quiz_data.max_attempts,
    )

    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    return quiz


# ============================================================
# TEACHER: LIST OWN COURSE QUIZZES
# ============================================================

@router.get(
    "/course/{course_id}",
    response_model=list[QuizResponse],
)
def get_course_quizzes(
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
        db.query(Quiz)
        .filter(Quiz.course_id == course_id)
        .order_by(Quiz.created_at.desc())
        .all()
    )


# ============================================================
# TEACHER: GET ONE QUIZ
# ============================================================

@router.get(
    "/teacher/{quiz_id}",
    response_model=QuizResponse,
)
def get_teacher_quiz(
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

    return quiz


# ============================================================
# TEACHER: UPDATE QUIZ
# ============================================================

@router.patch(
    "/{quiz_id}",
    response_model=QuizResponse,
)
def update_quiz(
    quiz_id: UUID,
    quiz_data: QuizUpdate,
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

    update_data = quiz_data.model_dump(exclude_unset=True)

    if "lesson_id" in update_data and update_data["lesson_id"] is not None:
        lesson = (
            db.query(Lesson)
            .filter(
                Lesson.id == update_data["lesson_id"],
                Lesson.course_id == quiz.course_id,
            )
            .first()
        )

        if lesson is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lesson does not belong to this course",
            )

    for field, value in update_data.items():
        setattr(quiz, field, value)

    db.commit()
    db.refresh(quiz)

    return quiz


# ============================================================
# TEACHER: DELETE QUIZ
# ============================================================

@router.delete(
    "/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_quiz(
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

    db.delete(quiz)
    db.commit()

    return None


# ============================================================
# TEACHER: CREATE QUESTION
# ============================================================

@router.post(
    "/{quiz_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    quiz_id: UUID,
    question_data: QuestionCreate,
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

    question = Question(
        quiz_id=quiz_id,
        question_text=question_data.question_text,
        question_type=question_data.question_type,
        points=question_data.points,
        order=question_data.order,
    )

    db.add(question)
    db.commit()
    db.refresh(question)

    return question


# ============================================================
# TEACHER: LIST QUESTIONS
# ============================================================

@router.get(
    "/{quiz_id}/questions",
    response_model=list[QuestionResponse],
)
def get_quiz_questions(
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
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order.asc())
        .all()
    )


# ============================================================
# TEACHER: UPDATE QUESTION
# ============================================================

@router.patch(
    "/questions/{question_id}",
    response_model=QuestionResponse,
)
def update_question(
    question_id: UUID,
    question_data: QuestionUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    question = (
        db.query(Question)
        .join(Quiz, Question.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            Question.id == question_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    update_data = question_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return question


# ============================================================
# TEACHER: DELETE QUESTION
# ============================================================

@router.delete(
    "/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_question(
    question_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    question = (
        db.query(Question)
        .join(Quiz, Question.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            Question.id == question_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    db.delete(question)
    db.commit()

    return None


# ============================================================
# TEACHER: CREATE OPTION
# ============================================================

@router.post(
    "/questions/{question_id}/options",
    response_model=QuizOptionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_option(
    question_id: UUID,
    option_data: QuizOptionCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    question = (
        db.query(Question)
        .join(Quiz, Question.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            Question.id == question_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    if question.question_type == QuestionType.SHORT_ANSWER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Short-answer questions cannot have options",
        )

    option = QuizOption(
        question_id=question_id,
        option_text=option_data.option_text,
        is_correct=option_data.is_correct,
    )

    db.add(option)
    db.commit()
    db.refresh(option)

    return option


# ============================================================
# TEACHER: LIST OPTIONS
# ============================================================

@router.get(
    "/questions/{question_id}/options",
    response_model=list[QuizOptionResponse],
)
def get_question_options(
    question_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    question = (
        db.query(Question)
        .join(Quiz, Question.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            Question.id == question_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    return (
        db.query(QuizOption)
        .filter(QuizOption.question_id == question_id)
        .all()
    )


# ============================================================
# TEACHER: UPDATE OPTION
# ============================================================

@router.patch(
    "/options/{option_id}",
    response_model=QuizOptionResponse,
)
def update_option(
    option_id: UUID,
    option_data: QuizOptionUpdate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    option = (
        db.query(QuizOption)
        .join(Question, QuizOption.question_id == Question.id)
        .join(Quiz, Question.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            QuizOption.id == option_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if option is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Option not found",
        )

    update_data = option_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(option, field, value)

    db.commit()
    db.refresh(option)

    return option


# ============================================================
# TEACHER: DELETE OPTION
# ============================================================

@router.delete(
    "/options/{option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_option(
    option_id: UUID,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    option = (
        db.query(QuizOption)
        .join(Question, QuizOption.question_id == Question.id)
        .join(Quiz, Question.quiz_id == Quiz.id)
        .join(Course, Quiz.course_id == Course.id)
        .filter(
            QuizOption.id == option_id,
            Course.teacher_id == current_user.id,
        )
        .first()
    )

    if option is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Option not found",
        )

    db.delete(option)
    db.commit()

    return None


# ============================================================
# STUDENT: LIST PUBLISHED QUIZZES
# ============================================================

@router.get(
    "/student/course/{course_id}",
    response_model=list[QuizResponse],
)
def get_student_course_quizzes(
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

    return (
        db.query(Quiz)
        .filter(
            Quiz.course_id == course_id,
            Quiz.is_published.is_(True),
        )
        .order_by(Quiz.created_at.asc())
        .all()
    )