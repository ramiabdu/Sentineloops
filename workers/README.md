# Workers

Background execution layer for scans, enrichment, deduplication, and alerting.

## Current scan worker

The worker polls for queued scans, marks one scan as running, executes scanner plugins, persists findings, and marks the scan as completed or failed.

```bash
PYTHONPATH=backend python -m workers.app.main
```
