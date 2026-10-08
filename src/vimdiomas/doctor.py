"""Checks the machine has what the app needs: pandoc, xelatex and the LaTeX
packages the template loads are required (compiling breaks without them,
Sprint 8 M2); xeCJK and the CJK font are needed only by the
languages whose kind sets a CJK face (Chinese) — a German-only install has no
use for them (Sprint 6 M7); the input switcher, nvim and pdftoppm are optional
(each only degrades one feature: input switching, Inspect Tree's MD mode,
Inspect Tree's PDF preview).

Which font and which switcher come from `vimdiomas.platform` (Sprint 5 M7) —
nothing here names an OS-specific tool. A check says what is missing and never
how to get it (Sprint 8 M3); each carries the `key` the platform installs it
by."""

import shutil
import subprocess
from dataclasses import dataclass

from vimdiomas.languages import LANGUAGES
from vimdiomas.pdf_preview import pdftoppm_available
from vimdiomas.platform import (
    CJK_FONT_NAME,
    cjk_font_installed,
    input_switcher,
)


@dataclass
class Check:
    """One dependency. `required` means every install needs it; `needed_for`
    names the registry languages that need it when only some do. `key` is the
    name the platform layer knows it by (`pandoc`, `xelatex`,
    `latex-packages`, `xecjk`, `cjk-font`, `input-switcher`, `nvim`,
    `pdftoppm`). `detail` says what is missing, when a check can (the LaTeX
    packages); the wizard shows it under the `missing` line."""

    name: str
    key: str
    required: bool
    ok: bool
    needed_for: tuple[str, ...] = ()
    detail: str = ""


# Derived from the kinds, not hardcoded as "Chinese": a second language of a
# CJK-faced kind would need xeCJK too.
CJK_LANGUAGES = tuple(
    language.name for language in LANGUAGES if language.kind.cjk_font is not None
)


def label(check: Check) -> str:
    """Who needs the check, as printed in brackets: `required`, `optional`, or
    the languages it is needed for."""
    if check.needed_for:
        return ", ".join(check.needed_for)
    return "required" if check.required else "optional"


def missing_for(checks: list[Check], languages: list[str]) -> list[Check]:
    """The checks that are not ok and that this install cannot do without:
    every `required` one, and any needed by one of `languages`. The one rule
    the CLI, the wizard and Settings all use."""
    return [
        check
        for check in checks
        if not check.ok
        and (check.required or any(name in check.needed_for for name in languages))
    ]


# What the template loads unconditionally (Sprint 8 M2): the name shown and the
# file `kpsewhich` looks for. `lmodern` is two rows because the style file and
# the OpenType fonts `fontspec` then uses are separate files; one font stands
# for the directory. A test keeps this and both platforms' tables in step with
# `xecjk.tex`.
LATEX_PACKAGES = (
    ("fontspec", "fontspec.sty"),
    ("geometry", "geometry.sty"),
    ("longtable", "longtable.sty"),
    ("caption", "caption.sty"),
    ("array", "array.sty"),
    ("xcolor", "xcolor.sty"),
    ("lmodern", "lmodern.sty"),
    ("lmodern fonts", "lmroman12-regular.otf"),
)

NO_TEX = "needs a TeX distribution"


def missing_latex_packages() -> list[str] | None:
    """The names of the template's LaTeX packages `kpsewhich` can't find, in
    table order, from a single call; `None` when there is no `kpsewhich`."""
    try:
        result = subprocess.run(
            ["kpsewhich", *(probe for _, probe in LATEX_PACKAGES)],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    found = {line.strip().rsplit("/", 1)[-1] for line in result.stdout.splitlines()}
    return [name for name, probe in LATEX_PACKAGES if probe not in found]


def _has_xecjk() -> bool:
    try:
        result = subprocess.run(
            ["kpsewhich", "xeCJK.sty"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return False
    return bool(result.stdout.strip())


def run() -> list[Check]:
    """Return one Check per dependency; required ones block, optional ones warn,
    and the ones with `needed_for` block only the languages named."""
    checks = []

    checks.append(
        Check("pandoc", "pandoc", required=True, ok=shutil.which("pandoc") is not None)
    )
    checks.append(
        Check("xelatex", "xelatex", required=True, ok=shutil.which("xelatex") is not None)
    )

    missing_packages = missing_latex_packages()
    checks.append(
        Check(
            "LaTeX packages",
            "latex-packages",
            required=True,
            ok=missing_packages == [],
            detail=NO_TEX if missing_packages is None else ", ".join(missing_packages),
        )
    )

    checks.append(
        Check("xeCJK", "xecjk", required=False, ok=_has_xecjk(), needed_for=CJK_LANGUAGES)
    )
    checks.append(
        Check(
            CJK_FONT_NAME,
            "cjk-font",
            required=False,
            ok=cjk_font_installed(),
            needed_for=CJK_LANGUAGES,
        )
    )

    switcher, has_switcher, _ = input_switcher()
    checks.append(Check(switcher, "input-switcher", required=False, ok=has_switcher))
    checks.append(Check("nvim", "nvim", required=False, ok=shutil.which("nvim") is not None))
    checks.append(Check("pdftoppm", "pdftoppm", required=False, ok=pdftoppm_available()))

    return checks
