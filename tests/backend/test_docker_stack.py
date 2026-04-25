from pathlib import Path


def test_docker_assets_exist():
    root = Path(__file__).resolve().parents[2]

    expected_files = [
        root / ".dockerignore",
        root / "backend" / "Dockerfile",
        root / "docker" / "docker-compose.yml",
    ]

    for path in expected_files:
        assert path.exists(), f"Missing Docker stack file: {path}"


def test_compose_defines_day6_services_and_healthchecks():
    root = Path(__file__).resolve().parents[2]
    compose_text = (root / "docker" / "docker-compose.yml").read_text()

    assert "api:" in compose_text
    assert "db:" in compose_text
    assert "redis:" in compose_text
    assert "healthcheck:" in compose_text
    assert "alembic upgrade head" in compose_text


def test_dockerignore_excludes_local_env_files():
    root = Path(__file__).resolve().parents[2]
    dockerignore_text = (root / ".dockerignore").read_text()

    assert ".env" in dockerignore_text
    assert "backend/.env" in dockerignore_text
