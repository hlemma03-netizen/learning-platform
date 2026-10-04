from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.auth import router as auth_router

from app.core.config import settings
from app.core.database import get_db

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

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.cors_origins.split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(courses_router, prefix="/api/v1")
app.include_router(lessons_router, prefix="/api/v1")
app.include_router(enrollments_router, prefix="/api/v1")
app.include_router(assignments_router, prefix="/api/v1")
app.include_router(submissions_router, prefix="/api/v1")
app.include_router(quizzes_router, prefix="/api/v1")
app.include_router(quiz_attempts_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(course_reviews_router, prefix="/api/v1")
app.include_router(progress_router, prefix="/api/v1")
app.include_router(certificates_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "message": "English Learning Platform API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }


@app.get("/db-test")
def database_test(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT current_database()"))

    return {
        "database": result.scalar(),
        "status": "connected",
    }