from fastapi import APIRouter, Depends, status

from app.core.auth import CurrentUser, create_session_token, get_current_user
from app.core.config import settings
from app.schemas.auth import AuthSessionCreate, AuthSessionResponse, AuthUserResponse

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
