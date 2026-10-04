from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LessonCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    content: str | None = None
    order: int = Field(..., ge=1)


class LessonUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    content: str | None = None
    order: int | None = Field(None, ge=1)
    is_published: bool | None = None


class LessonResponse(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: str | None
    content: str | None
    order: int
    is_published: bool

    model_config = ConfigDict(from_attributes=True)