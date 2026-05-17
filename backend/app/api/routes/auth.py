from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser, create_session_token, get_current_user
from app.core.config import settings
from app.core.errors import AuthenticationError, ConflictError
from app.db import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthLoginCreate,
    AuthSessionCreate,
    AuthSessionResponse,
    AuthSignupCreate,
    AuthUserResponse,
)
from app.services.users import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    authenticate_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/session",
    response_model=AuthSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_auth_session(
    payload: AuthSessionCreate | None = None,
) -> AuthSessionResponse:
    session_payload = payload or AuthSessionCreate(
        email=settings.AUTH_DEMO_EMAIL,
        display_name=settings.AUTH_DEMO_DISPLAY_NAME,
        role=settings.AUTH_DEMO_ROLE,
    )
    user = CurrentUser(
        subject=session_payload.email,
        email=session_payload.email,
        display_name=session_payload.display_name,
        role=session_payload.role,
    )

    return AuthSessionResponse(
        access_token=create_session_token(user),
        expires_in=settings.AUTH_TOKEN_TTL_MINUTES * 60,
        user=_serialize_user(user),
    )


@router.post(
    "/signup",
    response_model=AuthUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def signup(payload: AuthSignupCreate, db: Session = Depends(get_db)) -> AuthUserResponse:
    try:
        user = register_user(db, payload)
    except UserAlreadyExistsError as exc:
        raise ConflictError(
            code="user_already_exists",
            message="A user with this email already exists.",
        ) from exc

    return _serialize_registered_user(user)


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: AuthLoginCreate, db: Session = Depends(get_db)) -> AuthSessionResponse:
    try:
        user = authenticate_user(db, payload)
    except InvalidCredentialsError as exc:
        raise AuthenticationError(
            message="Invalid email or password.",
        ) from exc

    current_user = _current_user_from_registered_user(user)
    return AuthSessionResponse(
        access_token=create_session_token(current_user),
        expires_in=settings.AUTH_TOKEN_TTL_MINUTES * 60,
        user=_serialize_user(current_user),
    )


@router.get("/me", response_model=AuthUserResponse)
def get_authenticated_user(
    current_user: CurrentUser = Depends(get_current_user),
) -> AuthUserResponse:
    return _serialize_user(current_user)


def _serialize_user(user: CurrentUser) -> AuthUserResponse:
    return AuthUserResponse(
        subject=user.subject,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )


def _serialize_registered_user(user: User) -> AuthUserResponse:
    return _serialize_user(_current_user_from_registered_user(user))


def _current_user_from_registered_user(user: User) -> CurrentUser:
    return CurrentUser(
        subject=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=user.role,
    )
