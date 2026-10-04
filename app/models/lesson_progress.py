from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "lesson_id",
            name="uq_student_lesson_progress",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    student_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    lesson_id: Mapped[UUID] = mapped_column(
        ForeignKey("lessons.id"),
        nullable=False,
    )

    is_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    student = relationship("User")
    lesson = relationship("Lesson")