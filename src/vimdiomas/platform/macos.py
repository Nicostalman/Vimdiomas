"""macOS implementations of the platform layer: opening files, switching
input sources, listing the enabled ones, checking the CJK font is installed,
and installing the dependencies that are missing (Sprint 8 M3) — the
OS-specific calls `vimdiomas.platform` dispatches to on Darwin."""

import os
import plistlib
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from vimdiomas.platform.sources import InputSource

# Songti SC — a traditional Song/Ming face, dev-approved in Sprint 5 M3.
CJK_FONT_NAME = "Songti SC"
CJK_FONT_PATH = "/System/Library/Fonts/Supplemental/Songti.ttc"
# Bundled with macOS, not something installed from a repo — no url.
CJK_FONT_URL = ""

DEFAULT_SHELL_CONFIG = ".zshrc"
"""zsh is macOS's default login shell (Sprint 5 M7's D6)."""

PACKAGE_MANAGER = "Homebrew"
"""Named in the line shown when it isn't installed. Taken for granted
otherwise (Sprint 8 backlog)."""

# The Homebrew formula for each dependency `doctor` can report (Sprint 8 M3),
# by the key `doctor.Check.key` carries. xelatex is not here: it is the
# BasicTeX cask, installed only when there is no TeX at all. The CJK font isn't
# either: it ships with the OS.
BREW_FORMULAS = {
    "pandoc": "pandoc",
    "input-switcher": "laishulu/homebrew/macism",
    "nvim": "neovim",
    "pdftoppm": "poppler",
}

BASICTEX_CASK = "basictex"
"""A fresh BasicTeX has every LaTeX package the template loads except xeCJK
(Sprint 8 notes, Assumptions)."""

XECJK_TLMGR_PACKAGE = "xecjk"

# Where a tool installed by the package manager lands, for the app's own
# `PATH`: Homebrew's prefix on Apple Silicon and on Intel, and the TeX
# distributions' links. A shell only has `/Library/TeX/texbin` through
# `/etc/paths.d/TeX`, read when it starts, so a TeX installed mid-session isn't
# on the app's `PATH` without this.
EXTRA_PATH_DIRS = ("/opt/homebrew/bin", "/usr/local/bin", "/Library/TeX/texbin")

# The LaTeX packages the template loads (Sprint 8 M2), each with the `tlmgr`
# package that provides it. `longtable` and `array` ship in `tools`; both
# lmodern rows are `lm`. Names are `vimdiomas.doctor`'s, tested against it.
LATEX_PACKAGES = {
    "fontspec": "fontspec",
    "geometry": "geometry",
    "longtable": "tools",
    "caption": "caption",
    "array": "tools",
    "xcolor": "xcolor",
    "lmodern": "lm",
    "lmodern fonts": "lm",
}

INPUT_SOURCES_SETTINGS = "System Settings › Keyboard › Input Sources"
"""Where the user enables input sources, for the wizard's advisory lines."""

HITOOLBOX_DOMAIN ="com.apple.HIToolbox"

ENABLED_SOURCES_KEY = "AppleEnabledInputSources"

KEYBOARD_LAYOUT_PREFIX = "com.apple.keylayout."

# Display names for the sources most likely to turn up. Cosmetic only: every
# option is shown with its raw ID alongside, so a source missing from this
# table is still perfectly usable — it just reads as its last dotted segment.
DISPLAY_NAMES = {
    "com.apple.keylayout.US": "U.S.",
    "com.apple.keylayout.USInternational-PC": "U.S. International – PC",
    "com.apple.keylayout.ABC": "ABC",
    "com.apple.keylayout.British": "British",
    "com.apple.keylayout.German": "German",
    "com.apple.keylayout.German-DIN-2137": "German – Standard",
    "com.apple.keylayout.Italian": "Italian",
    "com.apple.keylayout.Italian-Pro": "Italian – Pro",
    "com.apple.keylayout.French": "French",
    "com.apple.keylayout.French-PC": "French – PC",
    "com.apple.keylayout.Spanish": "Spanish",
    "com.apple.keylayout.Spanish-ISO": "Spanish – ISO",
    "com.apple.keylayout.LatinAmerican": "Latin American",
    "com.apple.inputmethod.SCIM.ITABC": "Pinyin – Simplified",
    "com.apple.inputmethod.SCIM.WBX": "Wubi Xing – Simplified",
    "com.apple.inputmethod.SCIM.Shuangpin": "Shuangpin – Simplified",
    "com.apple.inputmethod.TCIM.Pinyin": "Pinyin – Traditional",
    "com.apple.inputmethod.TCIM.Zhuyin": "Zhuyin",
    "com.apple.inputmethod.TCIM.Cangjie": "Cangjie",
}


def open_file(path: Path) -> None:
    subprocess.run(["open", str(path)], check=False)


def switch_input_source(source_id: str) -> None:
    """A no-op whenever `macism` isn't installed or the source isn't
    available — that covers a missing Accessibility permission too, since
    macism fails the same way either way."""
    try:
        subprocess.run(["macism", source_id], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass


def is_keyboard_layout(source_id: str) -> bool:
    """A plain keyboard layout, as opposed to an input method — what the
    wizard prefers for the translation side."""
    return source_id.startswith(KEYBOARD_LAYOUT_PREFIX)


def display_name(source_id: str) -> str:
    return DISPLAY_NAMES.get(source_id) or source_id.rsplit(".", 1)[-1]


def list_input_sources() -> list[InputSource]:
    """The machine's enabled, switchable input sources, in the order macOS
    reports them.

    Read with `defaults export <domain> -`, which writes an XML plist to
    stdout that `plistlib` parses directly. `defaults read` prints the old
    NeXTSTEP format instead, which has no parser in the standard library —
    that difference is the whole reason this uses `export`.

    Never raises: a missing `defaults`, a failing call, or an unparseable
    payload all return `[]`, the same never-crash posture
    `switch_input_source` already has. An empty list is a legitimate answer
    (the wizard warns and carries on), not an error to surface.
    """
    try:
        result = subprocess.run(
            ["defaults", "export", HITOOLBOX_DOMAIN, "-"],
            capture_output=True,
            check=True,
        )
        data = plistlib.loads(result.stdout)
    except Exception:
        # Deliberately broad: a missing `defaults`, a non-zero exit, and a
        # payload `plistlib` chokes on all mean the same thing here — the OS
        # told us nothing, so offer nothing.
        return []

    if not isinstance(data, dict):
        return []

    entries = data.get(ENABLED_SOURCES_KEY) or []
    return _sources_from_entries(entries)


def _sources_from_entries(entries: list) -> list[InputSource]:
    """Map `AppleEnabledInputSources` entries onto the IDs `macism` accepts.

    The three kinds that produce a switchable source are handled per Sprint 4
    M6's `requirements.md`:

    - `Keyboard Layout` is named, not identified: `KeyboardLayout Name` needs
      the `com.apple.keylayout.` prefix macism expects.
    - `Input Mode` already carries a full ID in its `Input Mode` value.
    - `Keyboard Input Method` is the *container* of a multi-mode IME, which
      also appears once per mode. Offering it alongside its own modes would
      be a duplicate that switches to an arbitrary one, so it is kept only
      when no mode of its own is enabled (a mode-less IME still needs
      listing).

    `Non Keyboard Input Method` (character palette, Press-and-Hold, emoji) is
    dropped: macism can't meaningfully switch to any of them.
    """
    modes_by_bundle = {
        entry.get("Bundle ID")
        for entry in entries
        if isinstance(entry, dict) and entry.get("InputSourceKind") == "Input Mode"
    }

    sources: list[InputSource] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("InputSourceKind")
        if kind == "Keyboard Layout":
            name = entry.get("KeyboardLayout Name")
            source_id = f"{KEYBOARD_LAYOUT_PREFIX}{name}" if name else None
        elif kind == "Input Mode":
            source_id = entry.get("Input Mode")
        elif kind == "Keyboard Input Method":
            bundle = entry.get("Bundle ID")
            source_id = bundle if bundle not in modes_by_bundle else None
        else:
            source_id = None

        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        sources.append(InputSource(id=source_id, name=display_name(source_id)))

    return sources


def cjk_font_installed() -> bool:
    return os.path.exists(CJK_FONT_PATH)


def package_manager_available() -> bool:
    return shutil.which("brew") is not None


def installable(key: str) -> bool:
    """Whether `install` can do anything for the dependency `key`."""
    return key in BREW_FORMULAS or key in ("xelatex", "latex-packages", "xecjk")


def extend_path() -> None:
    """Append each of `EXTRA_PATH_DIRS` that exists and isn't already an entry
    to this process's `PATH`. In-process only: no shell file is touched."""
    current = os.environ.get("PATH", "")
    entries = current.split(os.pathsep) if current else []
    for directory in EXTRA_PATH_DIRS:
        if directory not in entries and os.path.isdir(directory):
            entries.append(directory)
    os.environ["PATH"] = os.pathsep.join(entries)


def install(
    keys: list[str],
    run: Callable[[list[str]], bool],
    missing_latex: Callable[[], list[str] | None],
) -> None:
    """Run, through `run`, the commands that install the dependencies `keys`
    (the keys `doctor.Check.key` carries; any this can't install is ignored).
    A command failing doesn't stop the next: the caller's recheck decides what
    is still missing.

    `brew install` takes every formula at once. Then, with no TeX at all, the
    BasicTeX cask. Then `tlmgr` for what the TeX lacks (`missing_latex()`,
    called after the cask so it sees the new TeX) and for xeCJK. `tlmgr` needs
    `update --self` first (a fresh BasicTeX refuses to install anything until
    then) and `sudo` (the `.pkg` installs a root-owned tree), and runs by its
    absolute path because `sudo` may reset `PATH`. With no `tlmgr` the pair is
    skipped: it could only fail."""
    formulas = list(dict.fromkeys(BREW_FORMULAS[key] for key in keys if key in BREW_FORMULAS))
    if formulas:
        run(["brew", "install", *formulas])

    if "xelatex" in keys:
        run(["brew", "install", "--cask", BASICTEX_CASK])
        extend_path()

    packages: dict[str, None] = {}
    if "xelatex" in keys or "latex-packages" in keys:
        for name in missing_latex() or []:
            packages[LATEX_PACKAGES[name]] = None
    if "xecjk" in keys:
        packages[XECJK_TLMGR_PACKAGE] = None
    tlmgr = shutil.which("tlmgr")
    if packages and tlmgr:
        run(["sudo", tlmgr, "update", "--self"])
        run(["sudo", tlmgr, "install", *packages])


def input_switcher() -> tuple[str, bool, str]:
    """`(name, available, url)` of the tool `switch_input_source` drives."""
    return (
        "macism",
        shutil.which("macism") is not None,
        "https://github.com/laishulu/macism",
    )


def user_bin_dir() -> Path:
    """Where a user-installed command belongs on this machine.

    `~/.local/bin` is the convention shells already put on `PATH` by default
    on most setups, and the one the installation wizard links `vimdiomas` into
    (Sprint 4 M7). It is returned whether or not it exists yet — creating it
    is the caller's job, and its absence is the ordinary first-install case,
    not an error.
    """
    return Path.home() / ".local" / "bin"
