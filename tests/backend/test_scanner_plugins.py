from uuid import uuid4

import pytest

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.scanners import (
    DuplicateScannerError,
    FindingDraft,
    InvalidScannerError,
    ScannerNotFoundError,
    ScannerProviderMismatchError,
    ScannerRegistry,
    ScanTarget,
    run_scanners,
)


class AwsPublicBucketScanner:
    name = "aws-s3-public-bucket"
    cloud_provider = CloudProvider.AWS
    description = "Detects public S3 buckets."

    def scan(self, target: ScanTarget) -> list[FindingDraft]:
        return [
            FindingDraft(
                severity=FindingSeverity.HIGH,
                title="Public S3 bucket",
                description=f"Account {target.external_id} has a public bucket.",
                resource_id="arn:aws:s3:::public-assets",
                resource_type="s3_bucket",
                region="us-east-1",
                metadata={"bucket_name": "public-assets"},
            )
        ]


class AzureStorageScanner:
    name = "azure-storage-public-container"
    cloud_provider = CloudProvider.AZURE
    description = "Detects public Azure Storage containers."

    def scan(self, _: ScanTarget) -> list[FindingDraft]:
        return []


def build_target(cloud_provider: CloudProvider = CloudProvider.AWS) -> ScanTarget:
    return ScanTarget(
        account_id=uuid4(),
        cloud_provider=cloud_provider,
        external_id="123456789012",
        account_name="Production",
    )


def test_registry_registers_and_filters_scanners_by_provider():
    registry = ScannerRegistry([AzureStorageScanner(), AwsPublicBucketScanner()])

    scanner_names = [scanner.name for scanner in registry.list_scanners()]
    aws_scanner_names = [
        scanner.name for scanner in registry.list_for_provider(CloudProvider.AWS)
    ]

    assert scanner_names == [
        "aws-s3-public-bucket",
        "azure-storage-public-container",
    ]
    assert aws_scanner_names == ["aws-s3-public-bucket"]
    assert registry.get("aws-s3-public-bucket").cloud_provider == CloudProvider.AWS


def test_registry_rejects_duplicate_scanner_names():
    registry = ScannerRegistry([AwsPublicBucketScanner()])

    with pytest.raises(DuplicateScannerError, match="aws-s3-public-bucket"):
        registry.register(AwsPublicBucketScanner())


def test_registry_reports_missing_scanners():
    registry = ScannerRegistry()

    with pytest.raises(ScannerNotFoundError, match="Scanner is not registered"):
        registry.get("missing-scanner")


def test_registry_rejects_invalid_scanner_contracts():
    class MissingNameScanner:
        name = ""
        cloud_provider = CloudProvider.AWS
        description = "Invalid scanner."

        def scan(self, _: ScanTarget) -> list[FindingDraft]:
            return []

    with pytest.raises(InvalidScannerError, match="name cannot be blank"):
        ScannerRegistry([MissingNameScanner()])


def test_runner_executes_registered_scanners_for_target_provider():
    registry = ScannerRegistry([AzureStorageScanner(), AwsPublicBucketScanner()])
    target = build_target()

    results = run_scanners(target, registry=registry)

    assert len(results) == 1
    assert results[0].scanner_name == "aws-s3-public-bucket"
    assert results[0].findings[0].severity == FindingSeverity.HIGH
    assert results[0].findings[0].metadata["bucket_name"] == "public-assets"


def test_runner_rejects_named_scanner_for_wrong_provider():
    registry = ScannerRegistry([AzureStorageScanner()])
    target = build_target(CloudProvider.AWS)

    with pytest.raises(ScannerProviderMismatchError, match="supports azure, not aws"):
        run_scanners(
            target,
            registry=registry,
            scanner_names=["azure-storage-public-container"],
        )


def test_scanner_contracts_reject_blank_required_fields():
    with pytest.raises(ValueError, match="external_id cannot be blank"):
        ScanTarget(
            account_id=uuid4(),
            cloud_provider=CloudProvider.AWS,
            external_id=" ",
            account_name="Production",
        )

    with pytest.raises(ValueError, match="title cannot be blank"):
        FindingDraft(
            severity=FindingSeverity.LOW,
            title=" ",
            description="Description",
            resource_id="resource-1",
            resource_type="s3_bucket",
        )
