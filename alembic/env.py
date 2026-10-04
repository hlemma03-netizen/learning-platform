from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import settings
from app.core.database import Base

# Import models here so Alembic can detect them
from app.models.user import User
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.enrollment import Enrollment
from app.models.assignment import Assignment
from app.models.submission import Submission

from app.models.quiz import Quiz
from app.models.question import Question
from app.models.quiz_option import QuizOption
from app.models.quiz_attempt import QuizAttempt
from app.models.attempt_answer import AttemptAnswer

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the DATABASE_URL from .env
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)

# Tell Alembic about our SQLAlchemy models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = settings.database_url

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()