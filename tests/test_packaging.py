"""Every non-Python file the package needs at runtime is declared as package
data, so the README's non-editable `pip install .` ships it (Sprint 5 M7:
`tui/app.tcss` was missing, and an installed app crashed on launch — an
editable install reads the checkout and hides that)."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "vimdiomas"


def test_every_data_file_is_declared_as_package_data():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = pyproject["tool"]["setuptools"]["package-data"]["vimdiomas"]
    declared = {path for pattern in patterns for path in PACKAGE.glob(pattern)}

    data_files = {
        path
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.suffix not in {".py", ".pyc"} and "__pycache__" not in path.parts
    }

    assert data_files - declared == set()
