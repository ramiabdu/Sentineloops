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
    assert "worker:" in compose_text
    assert "db:" in compose_text
    assert "redis:" in compose_text
    assert "healthcheck:" in compose_text
    assert "alembic upgrade head" in compose_text
    assert "python -m alembic" not in compose_text


def test_makefile_uses_alembic_console_command():
    root = Path(__file__).resolve().parents[2]
    makefile_text = (root / "Makefile").read_text()

    assert "alembic upgrade head" in makefile_text
    assert "alembic current" in makefile_text
    assert "python -m alembic" not in makefile_text


def test_dockerignore_excludes_local_env_files():
    root = Path(__file__).resolve().parents[2]
    dockerignore_text = (root / ".dockerignore").read_text()

    assert ".env" in dockerignore_text
    assert "backend/.env" in dockerignore_text


def test_render_blueprint_uses_backend_python_commands():
    root = Path(__file__).resolve().parents[2]
    render_text = (root / "render.yaml").read_text()

    assert "runtime: python" in render_text
    assert "buildCommand: cd backend && pip install -r requirements.txt" in render_text
    assert "preDeployCommand: cd backend && alembic upgrade head" in render_text
    assert "DATABASE_AUTO_MIGRATE" in render_text
    assert 'value: "true"' in render_text
    assert (
        "startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
        in render_text
    )
    assert "dockerfilePath" not in render_text


def test_backend_requirements_matches_runtime_dependencies():
    root = Path(__file__).resolve().parents[2]
    root_requirements_text = (root / "requirements.txt").read_text()
    backend_requirements_text = (root / "backend" / "requirements.txt").read_text()

    for dependency in [
        "alembic",
        "fastapi",
        "pydantic-settings",
        "psycopg[binary]",
        "sqlalchemy",
        "uvicorn[standard]",
    ]:
        assert dependency in root_requirements_text
        assert dependency in backend_requirements_text
