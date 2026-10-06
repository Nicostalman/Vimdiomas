"""One place OS-specific calls live, so supporting another platform means
adding a module here rather than touching every call site.

macOS (`macos.py`) and Linux (`linux.py`, Sprint 5 M7) are implemented;
every other platform gets inert no-ops, matching the guarantee
`input_method.py` already made on its own before this module existed."""

import platform as _platform
from pathlib import Path

from vimdiomas.platform.sources import InputSource

if _platform.system() == "Darwin":
    from vimdiomas.platform.macos import (
        CJK_FONT_NAME,
        CJK_FONT_PATH,
        CJK_FONT_URL,
        DEFAULT_SHELL_CONFIG,
        INPUT_SOURCES_SETTINGS,
        cjk_font_installed,
        input_switcher,
        install_hint,
        is_keyboard_layout,
        list_input_sources,
        open_file,
        switch_input_source,
        user_bin_dir,
    )
elif _platform.system() == "Linux":
    from vimdiomas.platform.linux import (
        CJK_FONT_NAME,
        CJK_FONT_PATH,
        CJK_FONT_URL,
        DEFAULT_SHELL_CONFIG,
        INPUT_SOURCES_SETTINGS,
        cjk_font_installed,
        input_switcher,
        install_hint,
        is_keyboard_layout,
        list_input_sources,
        open_file,
        switch_input_source,
        user_bin_dir,
    )
else:
    CJK_FONT_NAME = "Noto Serif CJK SC"
    CJK_FONT_PATH = None
    CJK_FONT_URL = ""
    DEFAULT_SHELL_CONFIG = ".profile"
    INPUT_SOURCES_SETTINGS = "your system's keyboard settings"

    def is_keyboard_layout(source_id: str) -> bool:
        return False

    def open_file(path: Path) -> None:
        pass

    def switch_input_source(source_id: str) -> None:
        pass

    def list_input_sources() -> list[InputSource]:
        """No sources to offer — the wizard treats that the same way it
        treats a Mac with none enabled: warn, and carry on."""
        return []

    def cjk_font_installed() -> bool:
        return False

    def user_bin_dir() -> Path | None:
        """No user-bin convention wired up here, so the wizard skips
        linking rather than guessing at one (Sprint 4 M7)."""
        return None

    def install_hint(dependency: str) -> str | None:
        return None

    def input_switcher() -> tuple[str, bool, str]:
        return "input switcher", False, ""


__all__ = [
    "CJK_FONT_NAME",
    "CJK_FONT_PATH",
    "CJK_FONT_URL",
    "DEFAULT_SHELL_CONFIG",
    "INPUT_SOURCES_SETTINGS",
    "InputSource",
    "cjk_font_installed",
    "input_switcher",
    "install_hint",
    "is_keyboard_layout",
    "list_input_sources",
    "open_file",
    "switch_input_source",
    "user_bin_dir",
]
