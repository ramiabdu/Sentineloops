from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.scanners.contracts import FindingDraft, ScanTarget


def _require_text(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} cannot be blank.")


@dataclass(frozen=True)
class IAMUser:
    user_name: str
    arn: str
    password_enabled: bool
    user_id: str | None = None

    def __post_init__(self) -> None:
        user_name = self.user_name.strip()
        arn = self.arn.strip()
        _require_text("IAM user name", user_name)
        _require_text("IAM user ARN", arn)
        object.__setattr__(self, "user_name", user_name)
        object.__setattr__(self, "arn", arn)
        if self.user_id is not None:
            user_id = self.user_id.strip()
            _require_text("IAM user id", user_id)
            object.__setattr__(self, "user_id", user_id)


@dataclass(frozen=True)
class IAMMFADevice:
    serial_number: str

    def __post_init__(self) -> None:
        serial_number = self.serial_number.strip()
        _require_text("MFA device serial number", serial_number)
        object.__setattr__(self, "serial_number", serial_number)


class IAMUserClient(Protocol):
    def list_users(self) -> Sequence[IAMUser]: ...

    def list_mfa_devices(self, user_name: str) -> Sequence[IAMMFADevice]: ...


class IAMUserWithoutMFAScanner:
    name = "aws-iam-user-without-mfa"
    cloud_provider = CloudProvider.AWS
    description = "Detects IAM users with console passwords and no MFA devices."

    def __init__(self, client: IAMUserClient) -> None:
        self._client = client

    def scan(self, target: ScanTarget) -> list[FindingDraft]:
        if target.cloud_provider != CloudProvider.AWS:
            raise ValueError("IAMUserWithoutMFAScanner only supports AWS scan targets.")

        findings: list[FindingDraft] = []
        for user in self._client.list_users():
            if not user.password_enabled:
                continue

            mfa_devices = tuple(self._client.list_mfa_devices(user.user_name))
            if mfa_devices:
                continue

            findings.append(self._build_missing_mfa_finding(user))
        return findings

    @staticmethod
    def _build_missing_mfa_finding(user: IAMUser) -> FindingDraft:
        return FindingDraft(
            severity=FindingSeverity.HIGH,
            title="IAM user console access has no MFA",
            description=(
                "The IAM user has console password access but no registered MFA "
                "device. Console users should use MFA to reduce account takeover risk."
            ),
            resource_id=user.arn,
            resource_type="iam_user",
            remediation=(
                "Require MFA for the IAM user, rotate credentials if exposure is "
                "suspected, or remove console password access for non-human users."
            ),
            metadata={
                "user_name": user.user_name,
                "user_id": user.user_id,
                "password_enabled": user.password_enabled,
                "mfa_device_count": 0,
            },
        )
