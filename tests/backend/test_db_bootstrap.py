from pathlib import Path


def test_alembic_files_exist():
    root = Path(__file__).resolve().parents[2]

    expected_files = [
        root / "backend" / "alembic.ini",
        root / "backend" / "alembic" / "env.py",
        root / "backend" / "alembic" / "script.py.mako",
        root / "backend" / "alembic" / "versions" / "20260424_0001_create_core_tables.py",
        root / "backend" / "alembic" / "versions" / "20260512_0002_add_finding_dedup_constraint.py",
        root / "backend" / "alembic" / "versions" / "20260513_0003_add_finding_dedup_tracking.py",
        root / "backend" / "app" / "db" / "session.py",
    ]

    for path in expected_files:
        assert path.exists(), f"Missing database bootstrap file: {path}"
