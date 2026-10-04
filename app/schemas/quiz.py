from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.question import QuestionType
from app.models.quiz_attempt import QuizAttemptStatus


# ============================================================
# QUIZ
# ============================================================

class QuizCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    lesson_id: UUID | None = None
    time_limit_minutes: int | None = Field(None, gt=0)
    max_attempts: int = Field(default=1, gt=0)


class QuizUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    lesson_id: UUID | None = None
    time_limit_minutes: int | None = Field(None, gt=0)
    max_attempts: int | None = Field(None, gt=0)
    is_published: bool | None = None


class QuizResponse(BaseModel):
    id: UUID
    course_id: UUID
    lesson_id: UUID | None
    title: str
    description: str | None
    time_limit_minutes: int | None
    max_attempts: int
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# QUESTIONS
# ============================================================

class QuestionCreate(BaseModel):
    question_text: str = Field(..., min_length=1)
    question_type: QuestionType
    points: int = Field(default=1, gt=0)
    order: int = Field(..., ge=1)


class QuestionUpdate(BaseModel):
    question_text: str | None = Field(None, min_length=1)
    points: int | None = Field(None, gt=0)
    order: int | None = Field(None, ge=1)


class QuestionResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    question_text: str
    question_type: QuestionType
    points: int
    order: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# OPTIONS
# ============================================================

class QuizOptionCreate(BaseModel):
    option_text: str = Field(..., min_length=1, max_length=500)
    is_correct: bool = False


class QuizOptionUpdate(BaseModel):
    option_text: str | None = Field(None, min_length=1, max_length=500)
    is_correct: bool | None = None


class QuizOptionResponse(BaseModel):
    id: UUID
    question_id: UUID
    option_text: str
    is_correct: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# QUIZ ATTEMPTS
# ============================================================

class QuizAttemptResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    student_id: UUID
    started_at: datetime
    submitted_at: datetime | None
    score: int | None
    status: QuizAttemptStatus

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# STUDENT ANSWERS
# ============================================================

class AnswerSubmit(BaseModel):
    question_id: UUID
    selected_option_id: UUID | None = None
    answer_text: str | None = None


class QuizSubmit(BaseModel):
    answers: list[AnswerSubmit]


class AttemptAnswerResponse(BaseModel):
    id: UUID
    attempt_id: UUID
    question_id: UUID
    selected_option_id: UUID | None
    answer_text: str | None
    is_correct: bool | None
    points_awarded: int

    model_config = ConfigDict(from_attributes=True)

class ShortAnswerGrade(BaseModel):
    is_correct: bool
    points_awarded: int = Field(..., ge=0)