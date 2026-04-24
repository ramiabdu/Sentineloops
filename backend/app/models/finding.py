from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedModel, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.scan import Scan


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, enum.Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    RESOLVED = "resolved"


class Finding(UUIDPrimaryKeyMixin, TimestampedModel, Base):
    __tablename__ = "findings"

    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    scan_id: Mapped[UUID | None] = mapped_column(ForeignKey("scans.id", ondelete="SET NULL"))
    severity: Mapped[FindingSeverity] = mapped_column(Enum(FindingSeverity), nullable=False)
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus),
        nullable=False,
        default=FindingStatus.OPEN,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(64))
    scanner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    risk_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    remediation: Mapped[str | None] = mapped_column(Text)
    resource_metadata: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    account: Mapped["Account"] = relationship(back_populates="findings")
    scan: Mapped["Scan | None"] = relationship(back_populates="findings")
