from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreate(BaseModel):
    content: str = Field(..., min_length=1)


class SubmissionGrade(BaseModel):
    score: int = Field(..., ge=0)
    feedback: str | None = None


class SubmissionResponse(BaseModel):
    id: UUID
    assignment_id: UUID
    student_id: UUID
    content: str
    submitted_at: datetime
    score: int | None
    feedback: str | None
    graded_at: datetime | None

    model_config = ConfigDict(from_attributes=True)