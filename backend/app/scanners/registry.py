from __future__ import annotations

from collections.abc import Iterable

from app.models.account import CloudProvider
from app.scanners.contracts import CloudScanner


class ScannerRegistryError(Exception):
    pass


class DuplicateScannerError(ScannerRegistryError):
    def __init__(self, scanner_name: str) -> None:
        super().__init__(f"Scanner is already registered: {scanner_name}")


class InvalidScannerError(ScannerRegistryError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)


class ScannerNotFoundError(ScannerRegistryError):
    def __init__(self, scanner_name: str) -> None:
        super().__init__(f"Scanner is not registered: {scanner_name}")


class ScannerProviderMismatchError(ScannerRegistryError):
    def __init__(
        self,
        scanner_name: str,
        *,
        expected: CloudProvider,
        actual: CloudProvider,
    ) -> None:
        super().__init__(f"Scanner {scanner_name} supports {actual.value}, not {expected.value}.")


class ScannerRegistry:
    def __init__(self, scanners: Iterable[CloudScanner] | None = None) -> None:
        self._scanners: dict[str, CloudScanner] = {}
        for scanner in scanners or ():
            self.register(scanner)

    def register(self, scanner: CloudScanner) -> CloudScanner:
        self._validate_scanner(scanner)
        if scanner.name in self._scanners:
            raise DuplicateScannerError(scanner.name)
        self._scanners[scanner.name] = scanner
        return scanner

    def get(self, scanner_name: str) -> CloudScanner:
        try:
            return self._scanners[scanner_name]
        except KeyError as exc:
            raise ScannerNotFoundError(scanner_name) from exc

    def list_scanners(self) -> tuple[CloudScanner, ...]:
        return tuple(self._scanners[name] for name in sorted(self._scanners))

    def list_for_provider(self, cloud_provider: CloudProvider) -> tuple[CloudScanner, ...]:
        return tuple(
            scanner for scanner in self.list_scanners() if scanner.cloud_provider == cloud_provider
        )

    @staticmethod
    def _validate_scanner(scanner: CloudScanner) -> None:
        name = getattr(scanner, "name", None)
        if not isinstance(name, str) or not name.strip():
            raise InvalidScannerError("Scanner name cannot be blank.")
        if not isinstance(getattr(scanner, "cloud_provider", None), CloudProvider):
            raise InvalidScannerError("Scanner cloud_provider must be a CloudProvider.")
        description = getattr(scanner, "description", None)
        if not isinstance(description, str) or not description.strip():
            raise InvalidScannerError("Scanner description cannot be blank.")
        if not callable(getattr(scanner, "scan", None)):
            raise InvalidScannerError("Scanner must expose a callable scan method.")


default_registry = ScannerRegistry()
