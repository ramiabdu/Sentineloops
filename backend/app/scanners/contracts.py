from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Protocol
from uuid import UUID

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity

ScannerMetadataValue = str | int | float | bool | None


def _require_text(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} cannot be blank.")


@dataclass(frozen=True)
class ScanTarget:
    account_id: UUID
    cloud_provider: CloudProvider
    external_id: str
    account_name: str

    def __post_init__(self) -> None:
        _require_text("external_id", self.external_id)
        _require_text("account_name", self.account_name)


@dataclass(frozen=True)
class FindingDraft:
    severity: FindingSeverity
    title: str
    description: str
    resource_id: str
    resource_type: str
    region: str | None = None
    remediation: str | None = None
    risk_score: Decimal | None = None
    metadata: Mapping[str, ScannerMetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_text("title", self.title)
        _require_text("description", self.description)
        _require_text("resource_id", self.resource_id)
        _require_text("resource_type", self.resource_type)
        if self.region is not None:
            _require_text("region", self.region)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class ScannerRunResult:
    scanner_name: str
    findings: tuple[FindingDraft, ...]

    def __post_init__(self) -> None:
        _require_text("scanner_name", self.scanner_name)
        object.__setattr__(self, "findings", tuple(self.findings))


class CloudScanner(Protocol):
    name: str
    cloud_provider: CloudProvider
    description: str

    def scan(self, target: ScanTarget) -> Sequence[FindingDraft]:
        """Return normalized finding drafts for the provided account target."""
        ...
