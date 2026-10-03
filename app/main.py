from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.auth import router as auth_router

from app.core.config import settings
from app.core.database import get_db


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api/v1")

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