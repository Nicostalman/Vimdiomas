"""Putting `vimdiomas` on the user's `PATH`.

The README's install stops one step short of a usable command: a `git clone`
plus a virtualenv gives you `<clone>/.venv/bin/vimdiomas`, not `vimdiomas`. The
installation wizard's last step closes that gap by symlinking the running
console script into the platform layer's user-bin directory (Sprint 4 M7).

Two rules shape everything here, both from the milestone's spec:

- **The shell config is only ever appended to, never rewritten.** A shell
  that doesn't have the bin directory on `PATH` gets exactly one line added
  by `ensure_on_path()` — checked against the file's own contents first, so
  running the wizard twice never adds it twice. Nothing already in the file
  is touched, reordered, or removed.
- **Nothing is overwritten.** Anything already sitting where the link would
  go — another checkout's script, an unrelated program, a stale link — is
  left exactly as it is and reported back to the caller.

No Textual in here: the wizard's screen renders what `link_status()` returns
and calls `create_link()` on Finish, and the tests exercise both directly.
"""

import os
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from vimdiomas.platform import DEFAULT_SHELL_CONFIG, user_bin_dir

LINK_NAME = "vimdiomas"


class LinkState(Enum):
    """What `<user_bin>/vimdiomas` looks like right now.

    `READY` is the only state `create_link()` acts on; every other state is
    something to report and move past, never a reason to stop the wizard
    finishing.
    """

    READY = "ready"
    """Nothing in the way — the link can be created."""

    ALREADY_LINKED = "already_linked"
    """The link exists and already points at this very script."""

    OCCUPIED = "occupied"
    """Something else is there. Never touched (see the module docstring)."""

    NO_SCRIPT = "no_script"
    """The app wasn't started from a console script, so there is nothing to
    link — `python -m vimdiomas` hits this."""

    UNSUPPORTED = "unsupported"
    """No user-bin convention on this platform (neither macOS nor Linux)."""


@dataclass
class LinkStatus:
    """The answer to "what would linking do right now?", with everything the
    wizard's step needs to explain itself and nothing it would have to
    recompute."""

    state: LinkState
    link_path: Path | None = None
    target: Path | None = None
    occupant: Path | None = None
    """What `link_path` currently resolves to, when `state` is OCCUPIED."""

    @property
    def can_create(self) -> bool:
        return self.state is LinkState.READY


@dataclass
class LinkResult:
    """What actually happened on Finish."""

    created: bool
    link_path: Path | None = None
    error: str | None = None


def console_script_path() -> Path | None:
    """The console script this process was started from, or `None`.

    `sys.argv[0]` is the venv's `bin/vimdiomas` shim when the app was launched
    as a command, and `.../vimdiomas/__main__.py` when it was launched as
    `python -m vimdiomas` — the latter is a module file, not something worth
    linking, so it comes back as `None` and the wizard says so.
    """
    raw = sys.argv[0] if sys.argv else ""
    if not raw:
        return None

    path = Path(raw)
    if not path.is_absolute():
        resolved = _which(path.name)
        if resolved is None:
            return None
        path = resolved

    path = path.resolve()
    if not path.is_file():
        return None
    if path.suffix == ".py":
        return None
    return path


def _which(name: str) -> Path | None:
    import shutil

    found = shutil.which(name)
    return Path(found) if found else None


def link_status(target: Path | None = None) -> LinkStatus:
    """Inspect the link path without touching anything."""
    bin_dir = user_bin_dir()
    if bin_dir is None:
        return LinkStatus(state=LinkState.UNSUPPORTED)

    link_path = bin_dir / LINK_NAME
    target = target or console_script_path()
    if target is None:
        return LinkStatus(state=LinkState.NO_SCRIPT, link_path=link_path)

    # `exists()` follows symlinks, so a link pointing at a deleted target
    # reads as absent; `is_symlink()` catches it and keeps it in OCCUPIED,
    # where it is reported rather than silently replaced.
    if link_path.is_symlink() or link_path.exists():
        current = _resolve_quietly(link_path)
        if current == target:
            return LinkStatus(
                state=LinkState.ALREADY_LINKED, link_path=link_path, target=target
            )
        return LinkStatus(
            state=LinkState.OCCUPIED,
            link_path=link_path,
            target=target,
            occupant=current,
        )

    return LinkStatus(state=LinkState.READY, link_path=link_path, target=target)


def _resolve_quietly(path: Path) -> Path | None:
    """`path.resolve()`, but `None` rather than an exception on a broken or
    circular link — this is display-only information."""
    try:
        return path.resolve(strict=False)
    except OSError:
        return None


def create_link(status: LinkStatus | None = None) -> LinkResult:
    """Create the symlink, if there is one to create.

    Never raises: a failure here must not stop the wizard writing the config
    and the tree folders, which are the part the user actually came for.
    """
    status = status or link_status()

    if status.state is LinkState.ALREADY_LINKED:
        return LinkResult(created=False, link_path=status.link_path)

    if not status.can_create:
        return LinkResult(created=False, link_path=status.link_path)

    assert status.link_path is not None and status.target is not None
    try:
        status.link_path.parent.mkdir(parents=True, exist_ok=True)
        status.link_path.symlink_to(status.target)
    except OSError as error:
        return LinkResult(
            created=False, link_path=status.link_path, error=str(error)
        )

    return LinkResult(created=True, link_path=status.link_path)


def on_path(directory: Path) -> bool:
    """Is `directory` on `PATH`?

    Compared as resolved paths, so `~/.local/bin`, `$HOME/.local/bin` and
    `/Users/you/.local/bin` all count as the same entry rather than three
    different strings.
    """
    target = _resolve_quietly(directory)
    if target is None:
        return False

    for entry in os.environ.get("PATH", "").split(os.pathsep):
        if not entry:
            continue
        resolved = _resolve_quietly(Path(entry).expanduser())
        if resolved == target:
            return True
    return False


def shell_config_path() -> Path:
    """The shell config file to tell the user to edit.

    Named from `$SHELL`, falling back to the platform's default login
    shell's config — `~/.zshrc` on macOS, `~/.bashrc` on Linux (Sprint 5
    M7's D6).
    """
    shell = Path(os.environ.get("SHELL", "")).name
    names = {
        "zsh": ".zshrc",
        "bash": ".bashrc",
        "fish": ".config/fish/config.fish",
    }
    return Path.home() / names.get(shell, DEFAULT_SHELL_CONFIG)


def path_export_line(directory: Path) -> str:
    """The line to add to `shell_config_path()` — shown to the user either
    way, and what `ensure_on_path()` appends when it writes it itself."""
    shown = _home_relative(directory)
    if shell_config_path().name == "config.fish":
        return f"fish_add_path {shown}"
    return f'export PATH="{shown}:$PATH"'


@dataclass
class PathEnsureResult:
    """What `ensure_on_path()` did, or didn't need to."""

    added: bool
    already_present: bool
    config_path: Path
    error: str | None = None


def directory_already_in_shell_config(directory: Path) -> bool:
    """Does `shell_config_path()` already mention `directory`?

    Separate from `on_path()`, which only sees the *running process's*
    `PATH` — a line added by an earlier wizard run wouldn't show up there
    until a new shell is opened, but it's already in the file, and the
    wizard's report should say so rather than claiming it's about to add a
    line that's already there.
    """
    config_path = shell_config_path()
    if not config_path.exists():
        return False
    try:
        return _home_relative(directory) in config_path.read_text(encoding="utf-8")
    except OSError:
        return False


def ensure_on_path(directory: Path) -> PathEnsureResult:
    """Make sure `directory` is on `PATH` for future shells, appending
    `path_export_line()` to `shell_config_path()` if it isn't already there.

    Callers that already know `directory` is on the *running* process's
    `PATH` (via `on_path()`) should skip calling this at all — appending a
    line that only fixes future shells is pointless when nothing is broken
    for any shell. That check happens where this is called from
    (`PathScreen._on_finish`), not in here, so this function is testable
    against the file alone.

    Idempotent: checked against the **file's own contents**, not just the
    running process's `PATH` env var, since a shell config written by an
    earlier wizard run wouldn't show up in this process's environment until
    a new shell is opened. Re-running the wizard (or the Settings screen)
    must never produce a second copy of the line.

    Only ever appends — an existing file's content is never rewritten or
    reordered, and a missing file is created holding just this one line.
    Never raises: a failure here must not stop the wizard finishing, which
    is why every other write in this module follows the same rule.
    """
    config_path = shell_config_path()
    line = path_export_line(directory)

    try:
        existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    except OSError as error:
        return PathEnsureResult(
            added=False, already_present=False, config_path=config_path, error=str(error)
        )

    if _home_relative(directory) in existing:
        return PathEnsureResult(added=False, already_present=True, config_path=config_path)

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(
                "\n# Added by the vimdiomas installer, so the `vimdiomas` command "
                "is found:\n"
            )
            handle.write(f"{line}\n")
    except OSError as error:
        return PathEnsureResult(
            added=False, already_present=False, config_path=config_path, error=str(error)
        )

    return PathEnsureResult(added=True, already_present=False, config_path=config_path)


def _home_relative(path: Path) -> str:
    """`~/.local/bin` rather than `/Users/you/.local/bin`, when it's under
    the home directory — shorter to read, and correct to paste."""
    try:
        return f"$HOME/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)
