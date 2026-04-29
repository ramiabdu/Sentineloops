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
class S3Bucket:
    name: str

    def __post_init__(self) -> None:
        _require_text("bucket name", self.name)

    @property
    def arn(self) -> str:
        return f"arn:aws:s3:::{self.name}"


@dataclass(frozen=True)
class S3BucketPolicyStatus:
    is_public: bool


@dataclass(frozen=True)
class S3AclGrant:
    permission: str
    grantee: str

    def __post_init__(self) -> None:
        _require_text("ACL permission", self.permission)
        _require_text("ACL grantee", self.grantee)


@dataclass(frozen=True)
class S3PublicAccessBlock:
    block_public_acls: bool
    ignore_public_acls: bool
    block_public_policy: bool
    restrict_public_buckets: bool

    @property
    def blocks_all_public_access(self) -> bool:
        return all(
            (
                self.block_public_acls,
                self.ignore_public_acls,
                self.block_public_policy,
                self.restrict_public_buckets,
            )
        )


class S3BucketClient(Protocol):
    def list_buckets(self) -> Sequence[S3Bucket]: ...

    def get_bucket_region(self, bucket_name: str) -> str | None: ...

    def get_bucket_policy_status(self, bucket_name: str) -> S3BucketPolicyStatus | None: ...

    def get_public_access_block(self, bucket_name: str) -> S3PublicAccessBlock | None: ...

    def list_public_acl_grants(self, bucket_name: str) -> Sequence[S3AclGrant]: ...


class S3PublicBucketScanner:
    name = "aws-s3-public-bucket"
    cloud_provider = CloudProvider.AWS
    description = "Detects S3 buckets exposed by public policies or public ACL grants."

    def __init__(self, client: S3BucketClient) -> None:
        self._client = client

    def scan(self, target: ScanTarget) -> list[FindingDraft]:
        if target.cloud_provider != CloudProvider.AWS:
            raise ValueError("S3PublicBucketScanner only supports AWS scan targets.")

        findings: list[FindingDraft] = []
        for bucket in self._client.list_buckets():
            region = self._client.get_bucket_region(bucket.name)
            policy_status = self._client.get_bucket_policy_status(bucket.name)
            public_acl_grants = tuple(self._client.list_public_acl_grants(bucket.name))
            public_access_block = self._client.get_public_access_block(bucket.name)

            if (
                policy_status is not None
                and policy_status.is_public
                and _public_policy_is_effective(public_access_block)
            ):
                findings.append(
                    self._build_public_policy_finding(
                        bucket=bucket,
                        region=region,
                        public_access_block=public_access_block,
                    )
                )
            if public_acl_grants and _public_acl_grants_are_effective(public_access_block):
                findings.append(
                    self._build_public_acl_finding(
                        bucket=bucket,
                        region=region,
                        public_acl_grants=public_acl_grants,
                        public_access_block=public_access_block,
                    )
                )
        return findings

    @staticmethod
    def _build_public_policy_finding(
        *,
        bucket: S3Bucket,
        region: str | None,
        public_access_block: S3PublicAccessBlock | None,
    ) -> FindingDraft:
        return FindingDraft(
            severity=FindingSeverity.CRITICAL,
            title="S3 bucket policy is public",
            description=(
                "The bucket policy allows public access. Review the policy and "
                "restrict access to trusted principals."
            ),
            resource_id=bucket.arn,
            resource_type="s3_bucket",
            region=region,
            remediation=(
                "Remove public principals from the bucket policy and enable S3 Block "
                "Public Access controls."
            ),
            metadata={
                "bucket_name": bucket.name,
                "detection_source": "bucket_policy_status",
                "blocks_all_public_access": _blocks_all_public_access(public_access_block),
            },
        )

    @staticmethod
    def _build_public_acl_finding(
        *,
        bucket: S3Bucket,
        region: str | None,
        public_acl_grants: Sequence[S3AclGrant],
        public_access_block: S3PublicAccessBlock | None,
    ) -> FindingDraft:
        return FindingDraft(
            severity=FindingSeverity.HIGH,
            title="S3 bucket ACL grants public access",
            description=(
                "The bucket ACL includes public grants. Remove public ACL grants and "
                "prefer bucket policies with least-privilege principals."
            ),
            resource_id=bucket.arn,
            resource_type="s3_bucket",
            region=region,
            remediation=(
                "Remove AllUsers or AuthenticatedUsers ACL grants and enable S3 Block "
                "Public Access controls."
            ),
            metadata={
                "bucket_name": bucket.name,
                "detection_source": "bucket_acl",
                "public_acl_grants": tuple(
                    f"{grant.grantee}:{grant.permission}" for grant in public_acl_grants
                ),
                "blocks_all_public_access": _blocks_all_public_access(public_access_block),
            },
        )


def _blocks_all_public_access(
    public_access_block: S3PublicAccessBlock | None,
) -> bool:
    return (
        public_access_block.blocks_all_public_access if public_access_block is not None else False
    )


def _public_policy_is_effective(
    public_access_block: S3PublicAccessBlock | None,
) -> bool:
    return public_access_block is None or not public_access_block.restrict_public_buckets


def _public_acl_grants_are_effective(
    public_access_block: S3PublicAccessBlock | None,
) -> bool:
    return public_access_block is None or not public_access_block.ignore_public_acls
