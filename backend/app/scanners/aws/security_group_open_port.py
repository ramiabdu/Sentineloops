from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from app.models.account import CloudProvider
from app.models.finding import FindingSeverity
from app.scanners.contracts import FindingDraft, ScanTarget

ADMIN_PORTS = {22, 3389}
PUBLIC_IPV4_CIDR = "0.0.0.0/0"
PUBLIC_IPV6_CIDR = "::/0"


def _require_text(field_name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} cannot be blank.")


@dataclass(frozen=True)
class SecurityGroupIngressRule:
    protocol: str
    from_port: int | None = None
    to_port: int | None = None
    cidr_ipv4: str | None = None
    cidr_ipv6: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        protocol = self.protocol.strip().lower()
        _require_text("protocol", protocol)
        object.__setattr__(self, "protocol", protocol)
        if self.cidr_ipv4 is not None:
            cidr_ipv4 = self.cidr_ipv4.strip()
            _require_text("cidr_ipv4", cidr_ipv4)
            object.__setattr__(self, "cidr_ipv4", cidr_ipv4)
        if self.cidr_ipv6 is not None:
            cidr_ipv6 = self.cidr_ipv6.strip()
            _require_text("cidr_ipv6", cidr_ipv6)
            object.__setattr__(self, "cidr_ipv6", cidr_ipv6)
        if self.description is not None:
            description = self.description.strip()
            _require_text("description", description)
            object.__setattr__(self, "description", description)
        if self.from_port is None or self.to_port is None:
            return
        if self.from_port < 0 or self.to_port < 0:
            raise ValueError("Ingress rule ports cannot be negative.")
        if self.from_port > self.to_port:
            raise ValueError("Ingress rule from_port cannot be greater than to_port.")

    @property
    def is_public(self) -> bool:
        return self.cidr_ipv4 == PUBLIC_IPV4_CIDR or self.cidr_ipv6 == PUBLIC_IPV6_CIDR

    @property
    def source(self) -> str:
        if self.cidr_ipv4 == PUBLIC_IPV4_CIDR:
            return PUBLIC_IPV4_CIDR
        if self.cidr_ipv6 == PUBLIC_IPV6_CIDR:
            return PUBLIC_IPV6_CIDR
        return self.cidr_ipv4 or self.cidr_ipv6 or "unknown"

    @property
    def port_label(self) -> str:
        if self.allows_all_traffic:
            return "all ports"
        if self.from_port == self.to_port:
            return str(self.from_port)
        return f"{self.from_port}-{self.to_port}"

    @property
    def allows_all_traffic(self) -> bool:
        return self.protocol in {"-1", "all"} or self.from_port is None or self.to_port is None

    @property
    def exposes_admin_port(self) -> bool:
        if self.allows_all_traffic:
            return True
        return any(self.from_port <= port <= self.to_port for port in ADMIN_PORTS)


@dataclass(frozen=True)
class SecurityGroup:
    group_id: str
    group_name: str
    region: str
    ingress_rules: Sequence[SecurityGroupIngressRule] = field(default_factory=tuple)
    vpc_id: str | None = None

    def __post_init__(self) -> None:
        group_id = self.group_id.strip()
        group_name = self.group_name.strip()
        region = self.region.strip()
        _require_text("security group id", group_id)
        _require_text("security group name", group_name)
        _require_text("region", region)
        object.__setattr__(self, "group_id", group_id)
        object.__setattr__(self, "group_name", group_name)
        object.__setattr__(self, "region", region)
        if self.vpc_id is not None:
            vpc_id = self.vpc_id.strip()
            _require_text("vpc_id", vpc_id)
            object.__setattr__(self, "vpc_id", vpc_id)
        object.__setattr__(self, "ingress_rules", tuple(self.ingress_rules))


class SecurityGroupClient(Protocol):
    def list_security_groups(self) -> Sequence[SecurityGroup]: ...


class SecurityGroupOpenPortScanner:
    name = "aws-security-group-open-port"
    cloud_provider = CloudProvider.AWS
    description = "Detects security group ingress rules exposed to the public internet."

    def __init__(self, client: SecurityGroupClient) -> None:
        self._client = client

    def scan(self, target: ScanTarget) -> list[FindingDraft]:
        if target.cloud_provider != CloudProvider.AWS:
            raise ValueError("SecurityGroupOpenPortScanner only supports AWS scan targets.")

        findings: list[FindingDraft] = []
        for security_group in self._client.list_security_groups():
            for ingress_rule in security_group.ingress_rules:
                if not ingress_rule.is_public:
                    continue
                findings.append(
                    self._build_public_ingress_finding(
                        security_group=security_group,
                        ingress_rule=ingress_rule,
                    )
                )
        return findings

    @staticmethod
    def _build_public_ingress_finding(
        *,
        security_group: SecurityGroup,
        ingress_rule: SecurityGroupIngressRule,
    ) -> FindingDraft:
        severity = (
            FindingSeverity.CRITICAL if ingress_rule.exposes_admin_port else FindingSeverity.HIGH
        )
        return FindingDraft(
            severity=severity,
            title="Security group allows public ingress",
            description=(
                "The security group allows public inbound traffic on "
                f"{ingress_rule.protocol}/{ingress_rule.port_label} from "
                f"{ingress_rule.source}."
            ),
            resource_id=security_group.group_id,
            resource_type="security_group",
            region=security_group.region,
            remediation=(
                "Restrict the ingress rule to trusted CIDR ranges, remove public "
                "administrative access, or place access behind a controlled entry point."
            ),
            metadata={
                "group_id": security_group.group_id,
                "group_name": security_group.group_name,
                "vpc_id": security_group.vpc_id,
                "protocol": ingress_rule.protocol,
                "from_port": ingress_rule.from_port,
                "to_port": ingress_rule.to_port,
                "source": ingress_rule.source,
                "rule_description": ingress_rule.description,
                "port_label": ingress_rule.port_label,
                "exposes_admin_port": ingress_rule.exposes_admin_port,
            },
        )
