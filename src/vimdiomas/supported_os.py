"""Which systems Vimdiomas runs on (Sprint 8 M1): macOS and Arch Linux.

Stdlib only, and importing nothing from the package: the gate in
`__main__.py` runs this before anything else is imported, so it has to work
on systems where `vimdiomas.platform` is not even meant to load."""

import platform
import sys

MESSAGE = "Vimdiomas runs only on macOS and Arch Linux. This is {name}."


def current() -> str | None:
    """`"macos"`, `"arch"`, or `None` for anything else.

    Arch derivatives (Manjaro, EndeavourOS, Arch ARM) count as Arch when
    `ID_LIKE` lists `arch`. A Linux with a missing or unreadable os-release is
    unsupported, and WSL is judged by its distro like any other Linux."""
    system = platform.system()
    if system == "Darwin":
        return "macos"
    if system != "Linux":
        return None
    try:
        release = platform.freedesktop_os_release()
    except OSError:
        return None
    if "arch" in (release.get("ID", ""), *release.get("ID_LIKE", "").split()):
        return "arch"
    return None


def _name() -> str:
    """What to call the unsupported system: `PRETTY_NAME`, else `ID`, else
    `platform.system()`."""
    if platform.system() == "Linux":
        try:
            release = platform.freedesktop_os_release()
        except OSError:
            release = {}
        name = release.get("PRETTY_NAME") or release.get("ID")
        if name:
            return name
    return platform.system() or "an unknown system"


def refuse_unless_supported() -> None:
    """Does nothing on a supported system. On any other it prints one line
    to stderr and exits with status 1."""
    if current() is None:
        print(MESSAGE.format(name=_name()), file=sys.stderr)
        raise SystemExit(1)
