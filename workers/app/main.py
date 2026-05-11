import os
import time

from workers.app.scans import run_once

from app.db import get_session_factory
from app.scanners import run_scanners

DEFAULT_POLL_INTERVAL_SECONDS = 5.0


def run_forever(poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS) -> None:
    session_factory = get_session_factory()
    while True:
        processed_scan = run_once(session_factory, scanner_runner=run_scanners)
        if processed_scan is None:
            time.sleep(poll_interval_seconds)


def _poll_interval_from_env() -> float:
    raw_value = os.getenv("WORKER_POLL_INTERVAL_SECONDS")
    if raw_value is None:
        return DEFAULT_POLL_INTERVAL_SECONDS
    return max(0.1, float(raw_value))


if __name__ == "__main__":
    run_forever(poll_interval_seconds=_poll_interval_from_env())
