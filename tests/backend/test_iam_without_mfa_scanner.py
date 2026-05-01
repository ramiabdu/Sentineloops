from collections.abc import Sequence
from uuid import uuid4

import pytest

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.scanners import (
    IAMMFADevice,
    IAMUser,
    IAMUserWithoutMFAScanner,
    ScanTarget,
)


class FakeIAMUserClient:
    def __init__(
        self,
        users: Sequence[IAMUser],
        mfa_devices_by_user: dict[str, Sequence[IAMMFADevice]] | None = None,
    ) -> None:
        self._users = tuple(users)
        self._mfa_devices_by_user = mfa_devices_by_user or {}

    def list_users(self) -> Sequence[IAMUser]:
        return self._users

    def list_mfa_devices(self, user_name: str) -> Sequence[IAMMFADevice]:
        return self._mfa_devices_by_user.get(user_name, ())


def build_target(cloud_provider: CloudProvider = CloudProvider.AWS) -> ScanTarget:
    return ScanTarget(
        account_id=uuid4(),
        cloud_provider=cloud_provider,
        external_id="123456789012",
        account_name="AWS production",
    )


def test_iam_user_without_mfa_scanner_reports_console_users_without_mfa():
    scanner = IAMUserWithoutMFAScanner(
        FakeIAMUserClient(
            [
                IAMUser(
                    user_name="alice",
                    arn="arn:aws:iam::123456789012:user/alice",
                    password_enabled=True,
                    user_id="AIDAALICE",
                )
            ]
        )
    )

    findings = scanner.scan(build_target())

    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.HIGH
    assert findings[0].title == "IAM user console access has no MFA"
    assert findings[0].resource_id == "arn:aws:iam::123456789012:user/alice"
    assert findings[0].resource_type == "iam_user"
    assert findings[0].metadata["user_name"] == "alice"
    assert findings[0].metadata["mfa_device_count"] == 0
    assert findings[0].metadata["password_enabled"] is True


def test_iam_user_without_mfa_scanner_ignores_users_with_mfa():
    scanner = IAMUserWithoutMFAScanner(
        FakeIAMUserClient(
            [
                IAMUser(
                    user_name="alice",
                    arn="arn:aws:iam::123456789012:user/alice",
                    password_enabled=True,
                )
            ],
            mfa_devices_by_user={
                "alice": [IAMMFADevice(serial_number="arn:aws:iam::123456789012:mfa/alice")]
            },
        )
    )

    assert scanner.scan(build_target()) == []


def test_iam_user_without_mfa_scanner_ignores_non_console_users():
    scanner = IAMUserWithoutMFAScanner(
        FakeIAMUserClient(
            [
                IAMUser(
                    user_name="service-user",
                    arn="arn:aws:iam::123456789012:user/service-user",
                    password_enabled=False,
                )
            ]
        )
    )

    assert scanner.scan(build_target()) == []


def test_iam_user_without_mfa_scanner_rejects_non_aws_targets():
    scanner = IAMUserWithoutMFAScanner(FakeIAMUserClient([]))

    with pytest.raises(ValueError, match="only supports AWS"):
        scanner.scan(build_target(CloudProvider.GCP))


def test_iam_domain_objects_reject_blank_required_values():
    with pytest.raises(ValueError, match="IAM user name cannot be blank"):
        IAMUser(
            user_name=" ",
            arn="arn:aws:iam::123456789012:user/alice",
            password_enabled=True,
        )

    with pytest.raises(ValueError, match="MFA device serial number cannot be blank"):
        IAMMFADevice(serial_number=" ")
