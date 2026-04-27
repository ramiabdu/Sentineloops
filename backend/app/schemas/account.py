from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountStatus, CloudProvider


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    cloud_provider: CloudProvider
    external_id: str = Field(min_length=1, max_length=128)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    cloud_provider: CloudProvider
    external_id: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
