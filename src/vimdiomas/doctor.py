"""Checks the machine has what the app needs: pandoc and xelatex are required
(compiling breaks without them); xeCJK and the CJK font are needed only by the
languages whose kind sets a CJK face (Chinese) — a German-only install has no
use for them (Sprint 6 M7); the input switcher, nvim and pdftoppm are optional
(each only degrades one feature: input switching, Inspect Tree's MD mode,
Inspect Tree's PDF preview).

Which font, which switcher, and the command that installs each dependency
all come from `vimdiomas.platform` (Sprint 5 M7) — nothing here names an
OS-specific tool."""

import shutil
import subprocess
from dataclasses import dataclass

from vimdiomas.languages import LANGUAGES
from vimdiomas.pdf_preview import pdftoppm_available
from vimdiomas.platform import (
    CJK_FONT_NAME,
    CJK_FONT_PATH,
    CJK_FONT_URL,
    cjk_font_installed,
    input_switcher,
    install_hint,
)


@dataclass
class Check:
    """One dependency. `required` means every install needs it; `needed_for`
    names the registry languages that need it when only some do. `install` is
    the platform's command for it, or `""` when there is none to offer."""

    name: str
    required: bool
    ok: bool
    message: str = ""
    url: str = ""
    needed_for: tuple[str, ...] = ()
    install: str = ""


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


def _has_xecjk() -> bool:
    try:
        result = subprocess.run(
            ["kpsewhich", "xeCJK.sty"], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        return False
    return bool(result.stdout.strip())


def _example(dependency: str) -> str:
    """` (e.g. `<command>`)` for the platform's install command, or nothing
    when it has none to offer."""
    command = install_hint(dependency)
    return f" (e.g. `{command}`)" if command else ""


def run() -> list[Check]:
    """Return one Check per dependency; required ones block, optional ones warn,
    and the ones with `needed_for` block only the languages named."""
    checks = []

    has_pandoc = shutil.which("pandoc") is not None
    checks.append(
        Check(
            "pandoc",
            required=True,
            ok=has_pandoc,
            message=f"pandoc not found: install it{_example('pandoc')}",
            url="https://github.com/jgm/pandoc",
        )
    )

    has_xelatex = shutil.which("xelatex") is not None
    checks.append(
        Check(
            "xelatex",
            required=True,
            ok=has_xelatex,
            message="xelatex not found: install a TeX Live distribution"
            f"{_example('xelatex')}",
            url="https://github.com/TeX-Live/texlive-source",
        )
    )

    checks.append(
        Check(
            "xeCJK",
            required=False,
            ok=_has_xecjk(),
            message=install_hint("xecjk") or "xeCJK not found: install the xeCJK LaTeX package",
            url="https://github.com/texjporg/xecjk",
            needed_for=CJK_LANGUAGES,
            install=install_hint("xecjk") or "",
        )
    )

    where = f" at {CJK_FONT_PATH}" if CJK_FONT_PATH else ""
    checks.append(
        Check(
            CJK_FONT_NAME,
            required=False,
            ok=cjk_font_installed(),
            message=f"CJK font not found{where} ({CJK_FONT_NAME}){_example('cjk-font')}",
            url=CJK_FONT_URL,
            needed_for=CJK_LANGUAGES,
            install=install_hint("cjk-font") or "",
        )
    )

    switcher, has_switcher, switcher_url = input_switcher()
    checks.append(
        Check(
            switcher,
            required=False,
            ok=has_switcher,
            message=f"{switcher} not found: input-method switching will be a no-op"
            f"{_example('input-switcher')}",
            url=switcher_url,
        )
    )

    has_nvim = shutil.which("nvim") is not None
    checks.append(
        Check(
            "nvim",
            required=False,
            ok=has_nvim,
            message="nvim not found: Inspect Tree's MD mode won't be able to open files"
            f"{_example('nvim')}",
            url="https://github.com/neovim/neovim",
        )
    )

    has_pdftoppm = pdftoppm_available()
    checks.append(
        Check(
            "pdftoppm",
            required=False,
            ok=has_pdftoppm,
            message="pdftoppm not found: Inspect Tree's PDF preview will be "
            f"degraded{_example('pdftoppm')}",
            url="https://poppler.freedesktop.org/",
        )
    )

    return checks
