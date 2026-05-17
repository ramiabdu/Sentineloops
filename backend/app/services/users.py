import logging

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.auth import hash_password, verify_password
from app.models.user import User
from app.repositories.users import create_user, get_user_by_email
from app.schemas.auth import AuthLoginCreate, AuthSignupCreate

logger = logging.getLogger(__name__)


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def register_user(db: Session, payload: AuthSignupCreate) -> User:
    try:
        existing_user = get_user_by_email(db, payload.email)
        if existing_user is not None:
            db.rollback()
            raise UserAlreadyExistsError()

        user = create_user(
            db,
            email=payload.email,
            display_name=payload.display_name or payload.email.split("@", 1)[0],
            role=payload.role,
            password_hash=hash_password(payload.password),
        )
        db.commit()
        db.refresh(user)
        return user
    except UserAlreadyExistsError:
        raise
    except IntegrityError as exc:
        logger.exception(
            "User signup integrity error: %s: %s",
            exc.__class__.__name__,
            exc,
        )
        db.rollback()
        raise UserAlreadyExistsError from exc
    except SQLAlchemyError as exc:
        logger.exception(
            "User signup database error: %s: %s",
            exc.__class__.__name__,
            exc,
        )
        db.rollback()
        raise
    except Exception as exc:
        logger.exception(
            "User signup unexpected error: %s: %s",
            exc.__class__.__name__,
            exc,
        )
        db.rollback()
        raise


def authenticate_user(db: Session, payload: AuthLoginCreate) -> User:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError()

    return user
