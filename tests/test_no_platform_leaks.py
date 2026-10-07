"""Nothing outside `vimdiomas.platform` names an OS-specific tool or path in
executable code (Sprint 5 M7). Comments and docstrings may still mention
them — historical notes are allowed — so only string literals that aren't
docstrings are checked."""

import ast
from pathlib import Path

import pytest

import vimdiomas

PACKAGE = Path(vimdiomas.__file__).parent

FORBIDDEN = [
    "brew ",
    # Sprint 8 M3: the installs live in the platform layer.
    "tlmgr",
    "pacman",
    "sudo ",
    "macism",
    "/System/",
    "/Library/",
    "defaults export",
    "xdg-open",
    # Found in the M7 container pass: the wizard told a Linux user to open
    # System Settings, and preselected by macOS's layout-ID prefix.
    "System Settings",
    "com.apple.",
]


def _modules_outside_the_platform_layer() -> list[Path]:
    platform_dir = PACKAGE / "platform"
    return sorted(
        path for path in PACKAGE.rglob("*.py") if platform_dir not in path.parents
    )


def _docstring_nodes(tree: ast.AST) -> set[int]:
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
        else:
            continue
        # A bare string expression anywhere in a body is documentation, not
        # code (attribute docstrings follow assignments, not only the top).
        for statement in body:
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                ids.add(id(statement.value))
    return ids


def _code_strings(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = _docstring_nodes(tree)
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def test_the_sweep_covers_the_package():
    modules = _modules_outside_the_platform_layer()
    assert PACKAGE / "doctor.py" in modules
    assert PACKAGE / "platform" / "macos.py" not in modules


@pytest.mark.parametrize(
    "path", _modules_outside_the_platform_layer(), ids=lambda p: str(p.relative_to(PACKAGE))
)
def test_no_os_specific_strings_outside_the_platform_layer(path):
    leaks = [
        f"line {line}: {needle!r} in {value!r}"
        for line, value in _code_strings(path)
        for needle in FORBIDDEN
        if needle in value
    ]
    assert not leaks, "\n".join(leaks)
