from __future__ import annotations

import logging
from dataclasses import dataclass

from alembic import command
from alembic.config import Config
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import BACKEND_DIR, settings
from app.db.session import get_engine
from app.models import Base

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DatabaseInitializationResult:
    migrations_checked: bool
    migrations_ran: bool
    missing_tables_checked: bool
    missing_tables_created: bool


def initialize_database(
    *,
    run_migrations: bool | None = None,
    create_missing_tables: bool | None = None,
) -> DatabaseInitializationResult:
    should_run_migrations = (
        settings.should_run_database_migrations
        if run_migrations is None
        else run_migrations
    )
    should_create_missing_tables = (
        settings.should_create_missing_database_tables
        if create_missing_tables is None
        else create_missing_tables
    )

    migrations_ran = False
    missing_tables_created = False

    if should_run_migrations and alembic_migrations_exist():
        try:
            run_database_migrations()
            migrations_ran = True
        except Exception as exc:
            if not should_create_missing_tables:
                raise
            logger.exception(
                "Continuing with missing-table initialization after migration failure: %s: %s",
                exc.__class__.__name__,
                exc,
            )

    if should_create_missing_tables:
        create_missing_database_tables()
        missing_tables_created = True

    return DatabaseInitializationResult(
        migrations_checked=should_run_migrations,
        migrations_ran=migrations_ran,
        missing_tables_checked=should_create_missing_tables,
        missing_tables_created=missing_tables_created,
    )


def alembic_migrations_exist() -> bool:
    versions_dir = BACKEND_DIR / "alembic" / "versions"
    return (BACKEND_DIR / "alembic.ini").exists() and any(versions_dir.glob("*.py"))


def run_database_migrations() -> None:
    logger.info("Running database migrations")
    try:
        alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
        command.upgrade(alembic_config, "head")
    except Exception as exc:
        logger.exception(
            "Database migration failed: %s: %s",
            exc.__class__.__name__,
            exc,
        )
        raise


def create_missing_database_tables() -> None:
    logger.info("Creating missing database tables with SQLAlchemy metadata")
    try:
        Base.metadata.create_all(bind=get_engine())
    except SQLAlchemyError as exc:
        logger.exception(
            "Database table initialization failed: %s: %s",
            exc.__class__.__name__,
            exc,
        )
        raise
