from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_question_answer",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    attempt_id: Mapped[UUID] = mapped_column(
        ForeignKey("quiz_attempts.id"),
        nullable=False,
    )

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )

    selected_option_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("quiz_options.id"),
        nullable=True,
    )

    answer_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    points_awarded: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    attempt = relationship(
        "QuizAttempt",
        back_populates="answers",
    )

    question = relationship(
        "Question",
        back_populates="attempt_answers",
    )

    selected_option = relationship("QuizOption")