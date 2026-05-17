from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.auth import SUPPORTED_ROLES


class AuthSessionCreate(BaseModel):
    email: str = Field(
        default="analyst@sentinelops.local", min_length=3, max_length=255
    )
    display_name: str = Field(
        default="SentinelOps Analyst", min_length=1, max_length=120
    )
    role: str = Field(default="admin", min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized_value = value.strip().lower()
        if "@" not in normalized_value or " " in normalized_value:
            raise ValueError("email must be a valid address")
        return normalized_value

    @field_validator("display_name")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role = value.strip().lower()
        if role not in SUPPORTED_ROLES:
            raise ValueError("role must be one of admin, analyst, or viewer")
        return role


class AuthSignupCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    display_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="admin", min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("display_name")
    @classmethod
    def strip_display_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("password cannot start or end with whitespace")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        return _normalize_role(value)


class AuthLoginCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)


class AuthUserResponse(BaseModel):
    subject: str
    email: str
    display_name: str
    role: str


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: AuthUserResponse


def _normalize_email(value: str) -> str:
    normalized_value = value.strip().lower()
    if "@" not in normalized_value or " " in normalized_value:
        raise ValueError("email must be a valid address")
    return normalized_value


def _normalize_role(value: str) -> str:
    role = value.strip().lower()
    if role not in SUPPORTED_ROLES:
        raise ValueError("role must be one of admin, analyst, or viewer")
    return role
