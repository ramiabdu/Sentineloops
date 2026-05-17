from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import hash_password, verify_password
from app.models.user import User
from app.repositories.users import create_user, get_user_by_email
from app.schemas.auth import AuthLoginCreate, AuthSignupCreate


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def register_user(db: Session, payload: AuthSignupCreate) -> User:
    if get_user_by_email(db, payload.email) is not None:
        raise UserAlreadyExistsError()

    user = create_user(
        db,
        email=payload.email,
        display_name=payload.display_name,
        role=payload.role,
        password_hash=hash_password(payload.password),
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise UserAlreadyExistsError from exc

    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: AuthLoginCreate) -> User:
    user = get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise InvalidCredentialsError()

    return user
