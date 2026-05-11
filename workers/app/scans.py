from sqlalchemy.orm import Session, sessionmaker

from app.models.scan import Scan
from app.scanners import run_scanners
from app.services.scan_execution import ScannerRunner, execute_next_queued_scan


def run_once(
    session_factory: sessionmaker[Session],
    *,
    scanner_runner: ScannerRunner = run_scanners,
) -> Scan | None:
    with session_factory() as db:
        return execute_next_queued_scan(db, scanner_runner=scanner_runner)
