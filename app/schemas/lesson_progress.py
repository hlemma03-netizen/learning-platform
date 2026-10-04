from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LessonProgressResponse(BaseModel):
    id: UUID
    student_id: UUID
    lesson_id: UUID
    is_completed: bool
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CourseProgressResponse(BaseModel):
    course_id: UUID
    total_lessons: int
    completed_lessons: int
    completion_percentage: float
    is_completed: bool