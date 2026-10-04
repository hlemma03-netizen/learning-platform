from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.courses import router as courses_router
from app.api.v1.lesson import router as lessons_router
from app.api.v1.enrollments import router as enrollments_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.submission import router as submissions_router
from app.api.v1.quizzes import router as quizzes_router
from app.api.v1.quiz_attempt import router as quiz_attempts_router
from app.api.v1.admin import router as admin_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.course_reviews import router as course_reviews_router
from app.api.v1.progress import router as progress_router
from app.api.v1.certificates import router as certificates_router


api_router = APIRouter()


# Authentication
api_router.include_router(auth_router)

# Learning
api_router.include_router(courses_router)
api_router.include_router(lessons_router)
api_router.include_router(enrollments_router)
api_router.include_router(progress_router)
api_router.include_router(certificates_router)
api_router.include_router(course_reviews_router)

# Assessments
api_router.include_router(assignments_router)
api_router.include_router(submissions_router)
api_router.include_router(quizzes_router)
api_router.include_router(quiz_attempts_router)

# Platform
api_router.include_router(notifications_router)

# Administration
api_router.include_router(admin_router)