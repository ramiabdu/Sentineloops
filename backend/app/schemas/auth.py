from typing import Literal

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("display_name", "role")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


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
