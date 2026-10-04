from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    quiz_id: Mapped[UUID] = mapped_column(
        ForeignKey("quizzes.id"),
        nullable=False,
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    question_type: Mapped[QuestionType] = mapped_column(
        SQLEnum(QuestionType),
        nullable=False,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quiz = relationship(
        "Quiz",
        back_populates="questions",
    )

    options = relationship(
        "QuizOption",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    attempt_answers = relationship(
        "AttemptAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )