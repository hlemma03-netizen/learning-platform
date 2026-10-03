from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CourseCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None


class CourseUpdate(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=200)
    description: str | None = None
    is_published: bool | None = None


class CourseResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    teacher_id: UUID
    is_published: bool

    model_config = ConfigDict(from_attributes=True)