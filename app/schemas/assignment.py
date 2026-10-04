from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    instructions: str | None = None
    lesson_id: UUID | None = None
    due_date: datetime | None = None
    max_score: int = Field(default=100, gt=0)


class AssignmentUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    instructions: str | None = None
    lesson_id: UUID | None = None
    due_date: datetime | None = None
    max_score: int | None = Field(None, gt=0)


class AssignmentResponse(BaseModel):
    id: UUID
    course_id: UUID
    lesson_id: UUID | None
    title: str
    description: str | None
    instructions: str | None
    due_date: datetime | None
    max_score: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)