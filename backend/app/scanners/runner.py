from __future__ import annotations

from collections.abc import Iterable

from app.scanners.contracts import ScannerRunResult, ScanTarget
from app.scanners.registry import (
    ScannerProviderMismatchError,
    ScannerRegistry,
    default_registry,
)


def run_scanners(
    target: ScanTarget,
    *,
    registry: ScannerRegistry = default_registry,
    scanner_names: Iterable[str] | None = None,
) -> tuple[ScannerRunResult, ...]:
    scanners = (
        tuple(registry.get(scanner_name) for scanner_name in scanner_names)
        if scanner_names is not None
        else registry.list_for_provider(target.cloud_provider)
    )

    results: list[ScannerRunResult] = []
    for scanner in scanners:
        if scanner.cloud_provider != target.cloud_provider:
            raise ScannerProviderMismatchError(
                scanner.name,
                expected=target.cloud_provider,
                actual=scanner.cloud_provider,
            )
        results.append(
            ScannerRunResult(
                scanner_name=scanner.name,
                findings=tuple(scanner.scan(target)),
            )
        )
    return tuple(results)
