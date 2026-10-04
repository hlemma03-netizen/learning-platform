from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.user import UserRole


class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AdminUserRoleUpdate(BaseModel):
    role: UserRole


class AdminUserStatusUpdate(BaseModel):
    is_active: bool


class AdminCourseResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    teacher_id: UUID
    is_published: bool

    model_config = ConfigDict(from_attributes=True)


class AdminCoursePublishUpdate(BaseModel):
    is_published: bool


class PlatformStatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_teachers: int
    total_admins: int
    active_users: int
    total_courses: int
    published_courses: int
    total_enrollments: int
    total_assignments: int
    total_submissions: int
    total_quizzes: int
    total_quiz_attempts: int