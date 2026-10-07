"""One place OS-specific calls live, so supporting another platform means
adding a module here rather than touching every call site.

macOS (`macos.py`) and Linux (`linux.py`, Sprint 5 M7) are implemented, and
only macOS and Arch Linux are supported (Sprint 8 M1). Any other system raises
`ImportError` here, a backstop: `vimdiomas.supported_os` refuses it first, in
`__main__`, before this module is imported."""

import platform as _platform

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
    raise ImportError(
        "vimdiomas.platform supports only macOS and Arch Linux "
        f"(this is {_platform.system()})."
    )


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
