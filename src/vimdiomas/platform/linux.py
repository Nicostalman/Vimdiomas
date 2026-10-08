"""Linux implementations of the platform layer (Sprint 5 M7): the same
surface as `macos.py`, dispatched to by `vimdiomas.platform` on Linux.

Input switching targets fcitx5 and ibus, whichever is running (D3). It is
best-effort: no framework running makes switching and listing silent no-ops,
the same as macOS without `macism`. The installs are Arch's (pacman): since
Sprint 8 M1 Arch is the only Linux supported, and `vimdiomas.supported_os` is
what refuses every other distro."""

import ast
import configparser
import functools
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from vimdiomas.platform.sources import InputSource

# Noto Serif CJK SC — the Ming/serif counterpart to macOS's Songti SC (D4).
CJK_FONT_NAME = "Noto Serif CJK SC"
# Found through fontconfig, not a fixed file: distros install it in
# different places.
CJK_FONT_PATH = None
CJK_FONT_URL = "https://github.com/notofonts/noto-cjk"

DEFAULT_SHELL_CONFIG = ".bashrc"
"""bash is the default login shell on nearly every distro (D6)."""

FCITX5_PROFILE = Path(".config") / "fcitx5" / "profile"

INPUT_SOURCES_SETTINGS = "fcitx5's or ibus' own settings"
"""Where the user enables input sources, for the wizard's advisory lines."""

# Display names for the engines and layouts most likely to turn up. Cosmetic
# only, as on macOS: anything missing here reads as its raw ID.
DISPLAY_NAMES = {
    "keyboard-us": "English (US)",
    "keyboard-us-intl": "English (US, intl.)",
    "keyboard-gb": "English (UK)",
    "keyboard-es": "Spanish",
    "keyboard-latam": "Spanish (Latin American)",
    "keyboard-de": "German",
    "keyboard-it": "Italian",
    "keyboard-fr": "French",
    "pinyin": "Pinyin",
    "shuangpin": "Shuangpin",
    "wbx": "Wubi",
    "rime": "Rime",
    "xkb:us::eng": "English (US)",
    "xkb:us:intl:eng": "English (US, intl.)",
    "xkb:gb:extd:eng": "English (UK)",
    "xkb:es::spa": "Spanish",
    "xkb:latam::spa": "Spanish (Latin American)",
    "xkb:de::ger": "German",
    "xkb:it::ita": "Italian",
    "xkb:fr::fra": "French",
    "libpinyin": "Pinyin",
}

PACKAGE_MANAGER = "pacman"
"""Named in the line shown when it isn't installed. Taken for granted
otherwise (Sprint 8 backlog)."""

# The pacman packages for each dependency `doctor` can report (Sprint 8 M3), by
# the key `doctor.Check.key` carries. "xelatex" is `texlive-xetex` alone. A
# bare one can't compile the template on Arch (it also needs fontspec, xcolor,
# caption and lmodern's OpenType fonts); `LATEX_PACKAGES` below (Sprint 8 M2)
# covers those, and `install` adds them next to it.
PACMAN_PACKAGES = {
    "pandoc": "pandoc-cli",
    "xelatex": "texlive-xetex",
    "xecjk": "texlive-langchinese",
    "cjk-font": "noto-fonts-cjk",
    "input-switcher": "fcitx5-im fcitx5-chinese-addons",
    "nvim": "neovim",
    "pdftoppm": "poppler",
}

# The LaTeX packages the template loads (Sprint 8 M2), each with the Arch
# package that provides it. Read from `pacman -F` in an `archlinux:latest`
# container, 2026-10-07; `texlive-xetex` pulls in `texlive-latex` only. Names
# are `vimdiomas.doctor`'s, tested against it.
LATEX_PACKAGES = {
    "fontspec": "texlive-latexrecommended",
    "geometry": "texlive-latex",
    "longtable": "texlive-latex",
    "caption": "texlive-latexrecommended",
    "array": "texlive-latex",
    "xcolor": "texlive-latexrecommended",
    "lmodern": "texlive-fontsrecommended",
    "lmodern fonts": "texlive-fontsrecommended",
}


def _succeeds(command: list[str]) -> bool:
    try:
        subprocess.run(command, capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return True


def open_file(path: Path) -> None:
    """A no-op when `xdg-open` is missing, as in a bare container."""
    try:
        subprocess.run(["xdg-open", str(path)], check=False)
    except FileNotFoundError:
        pass


@functools.cache
def _framework() -> str | None:
    """`"fcitx5"`, `"ibus"`, or `None` — whichever input-method framework is
    running, probed once per process: `switch_input_source` runs on every
    focus change and mustn't spawn two probes each time.

    `fcitx5-remote` with no arguments exits 0 only when the daemon answers;
    `ibus engine` likewise fails without a running ibus-daemon."""
    if _succeeds(["fcitx5-remote"]):
        return "fcitx5"
    if _succeeds(["ibus", "engine"]):
        return "ibus"
    return None


def switch_input_source(source_id: str) -> None:
    """A no-op with no framework running, or when the switch fails."""
    framework = _framework()
    if framework == "fcitx5":
        _succeeds(["fcitx5-remote", "-s", source_id])
    elif framework == "ibus":
        _succeeds(["ibus", "engine", source_id])


def is_keyboard_layout(source_id: str) -> bool:
    """fcitx5 names layouts `keyboard-<layout>`; ibus names them
    `xkb:<layout>:<variant>:<lang>`."""
    return source_id.startswith(("keyboard-", "xkb:"))


def display_name(source_id: str) -> str:
    return DISPLAY_NAMES.get(source_id) or source_id


def list_input_sources() -> list[InputSource]:
    """The user's enabled input methods, in their configured order.

    Never raises, the same posture as macOS: no framework, a missing config
    or an unparseable one all give `[]`, which the wizard warns about and
    carries on from.
    """
    framework = _framework()
    if framework == "fcitx5":
        ids = _fcitx5_profile_sources(Path.home() / FCITX5_PROFILE)
    elif framework == "ibus":
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.freedesktop.ibus.general", "preload-engines"],
                capture_output=True,
                text=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return []
        ids = _ibus_preload_engines(result.stdout)
    else:
        return []
    return [InputSource(id=source_id, name=display_name(source_id)) for source_id in ids]


def _fcitx5_profile_sources(path: Path) -> list[str]:
    """The `Name` of every `[Groups/N/Items/M]` section of fcitx5's profile,
    in file order, without duplicates (the same engine can sit in several
    groups). Read as INI rather than over D-Bus, so there's no dependency."""
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    try:
        parser.read_string(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, configparser.Error):
        return []

    names: list[str] = []
    for section in parser.sections():
        parts = section.split("/")
        if len(parts) != 4 or parts[0] != "Groups" or parts[2] != "Items":
            continue
        name = parser[section].get("Name", "").strip()
        if name and name not in names:
            names.append(name)
    return names


def _ibus_preload_engines(text: str) -> list[str]:
    """Parse `gsettings`' GVariant print of a string list —
    `['xkb:us::eng', 'libpinyin']`, or `@as []` when empty. That form is
    also a Python literal once the `@as` type annotation is dropped."""
    text = text.strip().removeprefix("@as").strip()
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return []
    return list(dict.fromkeys(value))


def cjk_font_installed() -> bool:
    try:
        result = subprocess.run(
            ["fc-list", f":family={CJK_FONT_NAME}", "family"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False
    return bool(result.stdout.strip())


def user_bin_dir() -> Path:
    """`~/.local/bin`, the XDG convention — returned whether or not it
    exists yet, as on macOS."""
    return Path.home() / ".local" / "bin"


def package_manager_available() -> bool:
    return shutil.which("pacman") is not None


def installable(key: str) -> bool:
    """Whether `install` can do anything for the dependency `key`."""
    return key in PACMAN_PACKAGES or key == "latex-packages"


def extend_path() -> None:
    """A no-op: pacman installs into `/usr/bin`, already on `PATH`."""


def install(
    keys: list[str],
    run: Callable[[list[str]], bool],
    missing_latex: Callable[[], list[str] | None],
) -> None:
    """Run, through `run`, the one pacman command that installs the
    dependencies `keys` (the keys `doctor.Check.key` carries; any this can't
    install is ignored), each package once, in first-seen order. `--needed`
    skips whatever is already there; `--noconfirm` because the user already
    said yes in the app, and pacman would otherwise ask again, and which
    members of the `fcitx5-im` group to install.

    With a TeX in `keys` (or the LaTeX packages alone), the pacman packages of
    whatever `missing_latex()` reports come too — every one of the template's
    packages when it returns `None`, since a bare machine has no `kpsewhich`
    to ask."""
    packages: dict[str, None] = {}
    for key in keys:
        for package in PACMAN_PACKAGES.get(key, "").split():
            packages[package] = None
    if "xelatex" in keys or "latex-packages" in keys:
        missing = missing_latex()
        for name in LATEX_PACKAGES if missing is None else missing:
            packages[LATEX_PACKAGES[name]] = None
    if packages:
        run(["sudo", "pacman", "-S", "--needed", "--noconfirm", *packages])


def input_switcher() -> tuple[str, bool, str]:
    """`(name, available, url)` — either framework will do (D3)."""
    available = shutil.which("fcitx5-remote") is not None or shutil.which("ibus") is not None
    return "fcitx5 or ibus", available, "https://github.com/fcitx/fcitx5"
