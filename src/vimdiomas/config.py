"""User-level config: `~/.config/vimdiomas/config.toml`, independent of where
the package is installed. Written once by the installation wizard (Sprint 4
M5); every other module only reads it."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import vimdiomas
from vimdiomas.languages import LanguageKind

CONFIG_PATH = Path.home() / ".config" / "vimdiomas" / "config.toml"
PACKAGE_ROOT = Path(vimdiomas.__file__).parent


LEGACY_NAME = "idiomas"


def migrate_legacy_paths(home: Path | None = None, bin_dir: Path | None = None) -> None:
    """Carry an install from before the rename to Vimdiomas (Sprint 7 M6)
    over to the new names: the config and cache folders are moved, and the
    old `idiomas` link is removed once its target is gone.

    Each step acts only when its condition holds, so this is a no-op after
    the first run and on a fresh machine. Never raises: a step that fails is
    skipped, and a missing config then simply means the wizard runs."""
    home = home or Path.home()
    for parent in (".config", ".cache"):
        old, new = home / parent / LEGACY_NAME, home / parent / "vimdiomas"
        try:
            if old.is_dir() and not new.exists():
                new.parent.mkdir(parents=True, exist_ok=True)
                os.replace(old, new)
        except OSError:
            pass

    if bin_dir is None:
        from vimdiomas.platform import user_bin_dir

        bin_dir = user_bin_dir()
    if bin_dir is None:
        return
    link = bin_dir / LEGACY_NAME
    try:
        # Only the kind of link the installer made, and only once it dangles.
        if link.is_symlink() and Path(os.readlink(link)).name == LEGACY_NAME and not link.exists():
            link.unlink()
    except OSError:
        pass


class ConfigNotFoundError(Exception):
    """Raised when CONFIG_PATH doesn't exist yet (no wizard has run)."""


@dataclass
class LanguageConfig:
    """One registered language.

    `input_method` is the source used to type the language itself (hanzi for
    Chinese); `translation_input_method` the one used for translations. Both
    default to `""`, meaning "don't switch" — the only case that reaches the
    app is a machine with no enabled input sources at all, where there is
    nothing to switch to anyway (Sprint 4 M6).
    """

    name: str
    input_method: str = ""
    translation_input_method: str = ""


@dataclass
class Config:
    user_name: str
    root: Path
    languages: list[LanguageConfig] = field(default_factory=list)

    def tree_root(self, language: str) -> Path:
        return self.root / f"tree-{language}"

    def language(self, name: str) -> LanguageConfig | None:
        for entry in self.languages:
            if entry.name == name:
                return entry
        return None


@dataclass
class NotebookConfig:
    """A single language's view of the config, as the notebook screens
    (Entry, Browse, Inspect Tree, ...) consume it."""

    tree_root: Path
    language: str
    kind: LanguageKind
    input_method: str = ""
    translation_input_method: str = ""


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        raise ConfigNotFoundError(str(CONFIG_PATH))

    data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))

    languages = [
        LanguageConfig(
            name=entry["name"],
            input_method=entry.get("input_method", ""),
            translation_input_method=entry.get("translation_input_method", ""),
        )
        for entry in data.get("languages", [])
    ]

    return Config(
        user_name=data["user_name"],
        root=_absolute_root(Path(data["root"])),
        languages=languages,
    )


def _absolute_root(root: Path) -> Path:
    """`root` made absolute, anchored to the home directory if it isn't.

    A relative root in a stored config is unusable by definition: it is
    re-interpreted against whatever directory the process was launched from,
    so the same command finds a different tree — or none — depending on where
    it was run (Sprint 6 M1, #7). The wizard has stored a resolved path since
    that fix; a config written before it gets anchored to the one fixed
    directory the app can name, so its meaning at least stops changing per
    launch. Loading is a read: the file itself is left alone, and the next
    `save_config` is what stores the resolved form.
    """
    if root.is_absolute():
        return root
    return (Path.home() / root).resolve()


# TOML's own named escapes for the control characters that have one; every
# other C0 control character, and DEL, is written as \uXXXX.
_TOML_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _needs_basic_string(value: str) -> bool:
    return (
        "'" in value
        or "\\" in value
        or any(ch < " " or ch == "\x7f" for ch in value)
    )


def _toml_string(value: str) -> str:
    """`value` as a TOML string.

    Serialization used to be Python's `!r`, which agrees with TOML on ASCII
    letters and little else: a user named `O'Brien` finished the wizard and
    then could not launch the app again, because `repr` emitted a TOML *basic*
    string whose contents it had escaped by Python's rules, not TOML's
    (Sprint 6 M1, #6).

    A value TOML can hold in a *literal* string is written as one — which is
    byte-for-byte what `repr` produced for it, so no config that works today
    is reformatted. Everything `repr` got wrong (apostrophes, backslashes,
    control characters) takes the basic-string branch and is escaped properly.
    """
    if not _needs_basic_string(value):
        return f"'{value}'"
    out = ['"']
    for ch in value:
        if ch in _TOML_ESCAPES:
            out.append(_TOML_ESCAPES[ch])
        elif ch < " " or ch == "\x7f":
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    out.append('"')
    return "".join(out)


def _toml_lines(config: Config) -> str:
    lines = [
        f"user_name = {_toml_string(config.user_name)}",
        f"root = {_toml_string(str(config.root))}",
    ]
    for language in config.languages:
        lines.append("")
        lines.append("[[languages]]")
        lines.append(f"name = {_toml_string(language.name)}")
        if language.input_method:
            lines.append(f"input_method = {_toml_string(language.input_method)}")
        if language.translation_input_method:
            lines.append(
                f"translation_input_method = "
                f"{_toml_string(language.translation_input_method)}"
            )
    return "\n".join(lines) + "\n"


def _verify_round_trip(text: str, config: Config) -> None:
    """Raise unless `text` parses back to exactly the values `config` holds.

    Catches an encoder bug — including a field added to `Config` without an
    encoder case for it — at save time, loudly, rather than at the next launch
    as a config the app can no longer read (Sprint 6 M1, #6).
    """
    parsed = tomllib.loads(text)
    expected = {
        "user_name": config.user_name,
        "root": str(config.root),
        "languages": [
            {
                "name": language.name,
                **({"input_method": language.input_method} if language.input_method else {}),
                **(
                    {"translation_input_method": language.translation_input_method}
                    if language.translation_input_method
                    else {}
                ),
            }
            for language in config.languages
        ],
    }
    if not config.languages:
        del expected["languages"]
    if parsed != expected:
        raise ValueError(
            f"config did not survive TOML encoding: wrote {expected!r}, read back {parsed!r}"
        )


def save_config(config: Config) -> None:
    """Write `config` to `CONFIG_PATH`, atomically.

    Written to a temp file in the same directory first, then `os.replace`d
    onto `CONFIG_PATH` — the project's standing convention for atomic saves
    — so a crash mid-write never leaves a truncated config behind.
    """
    text = _toml_lines(config)
    # Validated before anything is written, so a config the app could not read
    # back never reaches the disk and never replaces one that works.
    _verify_round_trip(text, config)

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = CONFIG_PATH.with_suffix(".toml.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    os.replace(tmp_path, CONFIG_PATH)


def validate_tree_root(path: Path) -> str | None:
    """Return an error message if `path` isn't fit to be the tree root, or
    `None` if it's acceptable.

    Rejects a path inside the installed `vimdiomas` package (the same class of
    mistake M4 fixed for the config and templates: something user-owned
    breaking because it depended on where the code lives) and a path that
    isn't writable.
    """
    resolved = path.expanduser().resolve()
    if resolved == PACKAGE_ROOT or PACKAGE_ROOT in resolved.parents:
        return f"{path} is inside the vimdiomas package; choose a different folder"

    existing = resolved
    while not existing.exists():
        existing = existing.parent

    if not existing.is_dir():
        return f"{existing} is not a directory"
    if not os.access(existing, os.W_OK):
        return f"{existing} is not writable"

    return None
