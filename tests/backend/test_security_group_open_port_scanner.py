from collections.abc import Sequence
from uuid import uuid4

import pytest

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.scanners import (
    ScanTarget,
    SecurityGroup,
    SecurityGroupIngressRule,
    SecurityGroupOpenPortScanner,
)


class FakeSecurityGroupClient:
    def __init__(self, security_groups: Sequence[SecurityGroup]) -> None:
        self._security_groups = tuple(security_groups)

    def list_security_groups(self) -> Sequence[SecurityGroup]:
        return self._security_groups


def build_target(cloud_provider: CloudProvider = CloudProvider.AWS) -> ScanTarget:
    return ScanTarget(
        account_id=uuid4(),
        cloud_provider=cloud_provider,
        external_id="123456789012",
        account_name="AWS production",
    )


def test_security_group_scanner_reports_public_admin_port_as_critical():
    scanner = SecurityGroupOpenPortScanner(
        FakeSecurityGroupClient(
            [
                SecurityGroup(
                    group_id="sg-123",
                    group_name="bastion",
                    region="us-east-1",
                    vpc_id="vpc-123",
                    ingress_rules=[
                        SecurityGroupIngressRule(
                            protocol="tcp",
                            from_port=22,
                            to_port=22,
                            cidr_ipv4="0.0.0.0/0",
                            description="temporary ssh",
                        )
                    ],
                )
            ]
        )
    )

    findings = scanner.scan(build_target())

    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.CRITICAL
    assert findings[0].resource_id == "sg-123"
    assert findings[0].resource_type == "security_group"
    assert findings[0].region == "us-east-1"
    assert findings[0].metadata["source"] == "0.0.0.0/0"
    assert findings[0].metadata["port_label"] == "22"
    assert findings[0].metadata["exposes_admin_port"] is True


def test_security_group_scanner_reports_public_application_port_as_high():
    scanner = SecurityGroupOpenPortScanner(
        FakeSecurityGroupClient(
            [
                SecurityGroup(
                    group_id="sg-456",
                    group_name="web",
                    region="eu-central-1",
                    ingress_rules=[
                        SecurityGroupIngressRule(
                            protocol="tcp",
                            from_port=443,
                            to_port=443,
                            cidr_ipv6="::/0",
                        )
                    ],
                )
            ]
        )
    )

    findings = scanner.scan(build_target())

    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.HIGH
    assert findings[0].metadata["source"] == "::/0"
    assert findings[0].metadata["port_label"] == "443"
    assert findings[0].metadata["exposes_admin_port"] is False


def test_security_group_scanner_reports_all_traffic_as_critical():
    scanner = SecurityGroupOpenPortScanner(
        FakeSecurityGroupClient(
            [
                SecurityGroup(
                    group_id="sg-all",
                    group_name="open-all",
                    region="us-west-2",
                    ingress_rules=[
                        SecurityGroupIngressRule(
                            protocol=" ALL ",
                            cidr_ipv4=" 0.0.0.0/0 ",
                        )
                    ],
                )
            ]
        )
    )

    findings = scanner.scan(build_target())

    assert len(findings) == 1
    assert findings[0].severity == FindingSeverity.CRITICAL
    assert findings[0].metadata["port_label"] == "all ports"
    assert findings[0].metadata["protocol"] == "all"


def test_security_group_scanner_ignores_private_sources():
    scanner = SecurityGroupOpenPortScanner(
        FakeSecurityGroupClient(
            [
                SecurityGroup(
                    group_id="sg-private",
                    group_name="internal",
                    region="us-east-1",
                    ingress_rules=[
                        SecurityGroupIngressRule(
                            protocol="tcp",
                            from_port=5432,
                            to_port=5432,
                            cidr_ipv4="10.0.0.0/8",
                        )
                    ],
                )
            ]
        )
    )

    assert scanner.scan(build_target()) == []


def test_security_group_scanner_rejects_non_aws_targets():
    scanner = SecurityGroupOpenPortScanner(FakeSecurityGroupClient([]))

    with pytest.raises(ValueError, match="only supports AWS"):
        scanner.scan(build_target(CloudProvider.AZURE))


def test_security_group_domain_objects_reject_invalid_values():
    with pytest.raises(ValueError, match="security group id cannot be blank"):
        SecurityGroup(group_id=" ", group_name="web", region="us-east-1")

    with pytest.raises(ValueError, match="from_port cannot be greater"):
        SecurityGroupIngressRule(
            protocol="tcp",
            from_port=1000,
            to_port=100,
            cidr_ipv4="0.0.0.0/0",
        )
