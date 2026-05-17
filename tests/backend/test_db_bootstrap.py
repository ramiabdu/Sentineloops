from pathlib import Path

import pytest

from app.db import initialization


def test_alembic_files_exist():
    root = Path(__file__).resolve().parents[2]

    expected_files = [
        root / "backend" / "alembic.ini",
        root / "backend" / "alembic" / "env.py",
        root / "backend" / "alembic" / "script.py.mako",
        root / "backend" / "alembic" / "versions" / "20260424_0001_create_core_tables.py",
        root / "backend" / "alembic" / "versions" / "20260512_0002_add_finding_dedup_constraint.py",
        root / "backend" / "alembic" / "versions" / "20260513_0003_add_finding_dedup_tracking.py",
        root / "backend" / "alembic" / "versions" / "20260517_0004_create_users.py",
        root / "backend" / "app" / "db" / "session.py",
    ]

    for path in expected_files:
        assert path.exists(), f"Missing database bootstrap file: {path}"


def test_database_initialization_falls_back_to_create_all_when_migration_fails(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []

    monkeypatch.setattr(initialization, "alembic_migrations_exist", lambda: True)
    monkeypatch.setattr(
        initialization,
        "run_database_migrations",
        lambda: (_ for _ in ()).throw(RuntimeError("migration failed")),
    )
    monkeypatch.setattr(
        initialization,
        "create_missing_database_tables",
        lambda: calls.append("create_all"),
    )

    result = initialization.initialize_database(
        run_migrations=True,
        create_missing_tables=True,
    )

    assert result.migrations_checked is True
    assert result.migrations_ran is False
    assert result.missing_tables_checked is True
    assert result.missing_tables_created is True
    assert calls == ["create_all"]
