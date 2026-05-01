from collections.abc import Sequence
from uuid import uuid4

import pytest

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.scanners import (
    S3AclGrant,
    S3Bucket,
    S3BucketPolicyStatus,
    S3PublicAccessBlock,
    S3PublicBucketScanner,
    ScanTarget,
)


class FakeS3Client:
    def __init__(
        self,
        *,
        buckets: Sequence[S3Bucket],
        regions: dict[str, str | None] | None = None,
        policy_statuses: dict[str, S3BucketPolicyStatus | None] | None = None,
        public_access_blocks: dict[str, S3PublicAccessBlock | None] | None = None,
        public_acl_grants: dict[str, Sequence[S3AclGrant]] | None = None,
    ) -> None:
        self._buckets = tuple(buckets)
        self._regions = regions or {}
        self._policy_statuses = policy_statuses or {}
        self._public_access_blocks = public_access_blocks or {}
        self._public_acl_grants = public_acl_grants or {}

    def list_buckets(self) -> Sequence[S3Bucket]:
        return self._buckets

    def get_bucket_region(self, bucket_name: str) -> str | None:
        return self._regions.get(bucket_name)

    def get_bucket_policy_status(self, bucket_name: str) -> S3BucketPolicyStatus | None:
        return self._policy_statuses.get(bucket_name)

    def get_public_access_block(self, bucket_name: str) -> S3PublicAccessBlock | None:
        return self._public_access_blocks.get(bucket_name)

    def list_public_acl_grants(self, bucket_name: str) -> Sequence[S3AclGrant]:
        return self._public_acl_grants.get(bucket_name, ())


def build_target(cloud_provider: CloudProvider = CloudProvider.AWS) -> ScanTarget:
    return ScanTarget(
        account_id=uuid4(),
        cloud_provider=cloud_provider,
        external_id="123456789012",
        account_name="AWS production",
    )


def test_s3_public_bucket_scanner_reports_public_policy_and_acl_findings():
    client = FakeS3Client(
        buckets=[S3Bucket(name="public-assets")],
        regions={"public-assets": "us-east-1"},
        policy_statuses={
            "public-assets": S3BucketPolicyStatus(is_public=True),
        },
        public_access_blocks={
            "public-assets": S3PublicAccessBlock(
                block_public_acls=False,
                ignore_public_acls=False,
                block_public_policy=False,
                restrict_public_buckets=False,
            )
        },
        public_acl_grants={
            "public-assets": [
                S3AclGrant(permission="READ", grantee="AllUsers"),
            ]
        },
    )
    scanner = S3PublicBucketScanner(client)

    findings = scanner.scan(build_target())

    assert [finding.title for finding in findings] == [
        "S3 bucket policy is public",
        "S3 bucket ACL grants public access",
    ]
    assert [finding.severity for finding in findings] == [
        FindingSeverity.CRITICAL,
        FindingSeverity.HIGH,
    ]
    assert all(finding.resource_id == "arn:aws:s3:::public-assets" for finding in findings)
    assert all(finding.region == "us-east-1" for finding in findings)
    assert findings[0].metadata["detection_source"] == "bucket_policy_status"
    assert findings[1].metadata["public_acl_grants"] == ("AllUsers:READ",)


def test_s3_public_bucket_scanner_ignores_private_buckets():
    client = FakeS3Client(
        buckets=[S3Bucket(name="private-assets")],
        policy_statuses={
            "private-assets": S3BucketPolicyStatus(is_public=False),
        },
        public_access_blocks={
            "private-assets": S3PublicAccessBlock(
                block_public_acls=True,
                ignore_public_acls=True,
                block_public_policy=True,
                restrict_public_buckets=True,
            )
        },
    )
    scanner = S3PublicBucketScanner(client)

    assert scanner.scan(build_target()) == []


def test_s3_public_bucket_scanner_respects_block_public_access_controls():
    client = FakeS3Client(
        buckets=[S3Bucket(name="guarded-assets")],
        policy_statuses={
            "guarded-assets": S3BucketPolicyStatus(is_public=True),
        },
        public_access_blocks={
            "guarded-assets": S3PublicAccessBlock(
                block_public_acls=True,
                ignore_public_acls=True,
                block_public_policy=True,
                restrict_public_buckets=True,
            )
        },
        public_acl_grants={
            "guarded-assets": [
                S3AclGrant(permission="READ", grantee="AllUsers"),
            ]
        },
    )
    scanner = S3PublicBucketScanner(client)

    assert scanner.scan(build_target()) == []


def test_s3_public_bucket_scanner_rejects_non_aws_targets():
    scanner = S3PublicBucketScanner(FakeS3Client(buckets=[]))

    with pytest.raises(ValueError, match="only supports AWS"):
        scanner.scan(build_target(CloudProvider.GCP))


def test_s3_scanner_domain_objects_reject_blank_required_values():
    with pytest.raises(ValueError, match="bucket name cannot be blank"):
        S3Bucket(name=" ")

    with pytest.raises(ValueError, match="ACL grantee cannot be blank"):
        S3AclGrant(permission="READ", grantee=" ")
