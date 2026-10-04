from uuid import UUID, uuid4

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class QuizOption(Base):
    __tablename__ = "quiz_options"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False,
    )

    option_text: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    question = relationship(
        "Question",
        back_populates="options",
    )