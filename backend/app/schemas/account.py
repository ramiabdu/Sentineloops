from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.account import AccountStatus, CloudProvider


class AccountCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    cloud_provider: CloudProvider
    external_id: str = Field(min_length=1, max_length=128)

    @field_validator("external_id")
    @classmethod
    def reject_external_id_whitespace(cls, value: str) -> str:
        if any(character.isspace() for character in value):
            raise ValueError("External ID cannot contain whitespace.")
        return value


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    cloud_provider: CloudProvider
    external_id: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
