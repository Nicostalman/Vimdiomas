"""The platform layer's own value type for an input source.

In a module of its own so `macos.py` and `linux.py` can import it without
importing the `vimdiomas.platform` package that imports them back."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InputSource:
    """One switchable input source, as the OS reports it.

    `id` is what the switcher takes verbatim (`macism` on macOS,
    `fcitx5-remote -s` or `ibus engine` on Linux); `name` is
    for display only and is never matched on.
    """

    id: str
    name: str
