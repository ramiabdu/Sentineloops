from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampedModel, UUIDPrimaryKeyMixin, enum_values

if TYPE_CHECKING:
    from app.models.finding import Finding
    from app.models.scan import Scan


class CloudProvider(str, enum.Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class AccountStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISCONNECTED = "disconnected"


class Account(UUIDPrimaryKeyMixin, TimestampedModel, Base):
    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("cloud_provider", "external_id", name="uq_accounts_provider_external_id"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cloud_provider: Mapped[CloudProvider] = mapped_column(
        Enum(CloudProvider, name="cloud_provider", values_callable=enum_values),
        nullable=False,
        index=True,
    )
    external_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status", values_callable=enum_values),
        nullable=False,
        default=AccountStatus.PENDING,
        index=True,
    )

    scans: Mapped[list["Scan"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
    findings: Mapped[list["Finding"]] = relationship(
        back_populates="account",
        cascade="all, delete-orphan",
    )
