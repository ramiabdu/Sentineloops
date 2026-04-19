from pathlib import Path


def test_expected_root_directories_exist():
    root = Path(__file__).resolve().parents[2]
    expected = [
        "backend",
        "frontend",
        "workers",
        "docker",
        "terraform",
        "docs",
        "tests",
    ]

    for name in expected:
        assert (root / name).exists(), f"Missing directory: {name}"
