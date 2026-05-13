from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.finding import FindingSeverity, FindingStatus


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    scan_id: UUID | None
    severity: FindingSeverity
    status: FindingStatus
    title: str
    description: str | None
    resource_id: str
    resource_type: str
    region: str | None
    scanner_name: str
    risk_score: Decimal | None
    remediation: str | None
    resource_metadata: dict[str, Any] | None
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int
    created_at: datetime
    updated_at: datetime
