from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def create_user(
    db: Session,
    *,
    email: str,
    display_name: str,
    role: str,
    password_hash: str,
) -> User:
    user = User(
        email=email,
        display_name=display_name,
        role=role,
        password_hash=password_hash,
    )
    db.add(user)
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.execute(statement).scalar_one_or_none()
