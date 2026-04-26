import tomllib
from pathlib import Path


def test_backend_package_discovery_excludes_alembic_scripts():
    root = Path(__file__).resolve().parents[2]
    pyproject = tomllib.loads((root / "backend" / "pyproject.toml").read_text())

    package_find = pyproject["tool"]["setuptools"]["packages"]["find"]

    assert package_find["include"] == ["app*"]
    assert package_find["exclude"] == ["alembic*"]
