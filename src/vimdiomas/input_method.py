"""Input-source switching, driven by the config.

Sprint 2 M4 hardcoded one pair — Pinyin Simplified and English
International — standing in for an installation wizard that didn't exist
yet. Sprint 4 M6 replaced that: the wizard (and Settings) ask which sources
to use, store them per language in `~/.config/vimdiomas/config.toml`, and this
module switches to whatever is stored. Changing them there changes what the
app switches to, with no code edit.

`vimdiomas.platform.switch_input_source` is a no-op on every platform but
macOS and Linux, and a no-op (never a crash) whenever the switcher isn't
installed — `macism` on macOS, a running fcitx5 or ibus on Linux — or the
input source isn't available.
"""

from vimdiomas.platform import switch_input_source


def switch_to(source_id: str) -> None:
    """Switch to `source_id`, or do nothing if it's empty.

    An empty ID means the config has no answer for this language. The only
    way that reaches a running app is a machine with no enabled input
    sources at all — where there is nothing to switch to — or a hand-written
    config. Doing nothing is the right answer in both: the user keeps typing
    with whatever keyboard they have, and no screen is unusable.
    """
    if not source_id:
        return
    switch_input_source(source_id)
