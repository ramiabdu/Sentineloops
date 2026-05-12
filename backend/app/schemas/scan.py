from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.scan import ScanStatus


class ScanCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    account_id: UUID
    triggered_by: str | None = Field(default=None, min_length=1, max_length=255)


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    status: ScanStatus
    triggered_by: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class ScanStatusResponse(ScanResponse):
    duration_seconds: int | None
    findings_total: int
    findings_by_severity: dict[str, int]
    findings_by_status: dict[str, int]
