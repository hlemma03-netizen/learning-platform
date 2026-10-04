from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Certificate(Base):
    __tablename__ = "certificates"

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "course_id",
            name="uq_student_course_certificate",
        ),
        UniqueConstraint(
            "certificate_number",
            name="uq_certificate_number",
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

    course_id: Mapped[UUID] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
    )

    certificate_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    issued_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    student = relationship("User")
    course = relationship("Course")