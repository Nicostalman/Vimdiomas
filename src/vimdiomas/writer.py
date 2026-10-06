import os
import shlex
import tempfile
from pathlib import Path

from vimdiomas.languages import LanguageKind
from vimdiomas.models import Deck, Entry

# A tab shifts the columns of a triad row and a newline splits it in two, so
# neither can appear in a field (Sprint 6 M1, #15). Fields reaching the writer
# from the app are already sanitised by `panels.TextField`; this is the
# backstop for any other caller.
_FORBIDDEN_IN_FIELD = ("\t", "\n", "\r")
_FORBIDDEN_IN_NOTE = ("\n", "\r")


def _check_field(entry: Entry, name: str, value: str, forbidden: tuple[str, ...]) -> None:
    for char in forbidden:
        if char in value:
            raise ValueError(
                f"{entry.word!r}: {name} contains {char!r}, "
                "which would corrupt the row it is written on"
            )


def _render_entries(lines: list[str], entries: list[Entry], kind: LanguageKind) -> None:
    for entry in entries:
        if kind.has_reading:
            fields = [entry.word, entry.reading, entry.translation, *entry.extra_fields]
            names = ["word", "reading", "translation"]
        else:
            # Dropping a reading silently would lose it, and nothing in the
            # app can produce one: such a kind's Entry form has no field.
            if entry.reading != "":
                raise ValueError(
                    f"{entry.word!r}: a {kind.name} entry has no reading, "
                    f"but this one has {entry.reading!r}"
                )
            fields = [entry.word, entry.translation, *entry.extra_fields]
            names = ["word", "translation"]
        names += [f"extra_fields[{index}]" for index in range(len(entry.extra_fields))]
        for name, value in zip(names, fields):
            _check_field(entry, name, value, _FORBIDDEN_IN_FIELD)
        lines.append("\t".join(fields))
        if entry.note:
            # A note is written on its own line, so a tab in it shifts
            # nothing — but a newline would still break the file.
            _check_field(entry, "note", entry.note, _FORBIDDEN_IN_NOTE)
            lines.append(f"    *{entry.note}*")


def _render_tag(tag: str) -> str:
    """`tag` in the narrowest form `parser._split_tags_line` reads back.

    That reader is `shlex.split`, so writing has to be shlex-compatible or a
    tag round-trips into something unparseable and the file's whole tag block
    is lost (Sprint 6 M1, #3). The first two branches are what this function
    already emitted, kept byte-for-byte so a correctness fix doesn't reformat
    the tag block of every existing file; only the cases that are broken
    today take the third.
    """
    if not any(ch.isspace() for ch in tag) and not any(ch in tag for ch in "\"'\\"):
        return f"#{tag}"
    if not any(ch in tag for ch in '"\\'):
        return f'#"{tag}"'
    return shlex.quote("#" + tag)


def write(deck: Deck, *, kind: LanguageKind) -> str:
    lines: list[str] = [f"# {deck.title}", ""]

    if deck.uncategorized:
        _render_entries(lines, deck.uncategorized, kind)
        lines.append("")

    for category in deck.categories:
        lines.append(f"## {category.name}")
        lines.append("")
        _render_entries(lines, category.entries, kind)
        lines.append("")
        for subtitle in category.subtitles:
            lines.append(f"### {subtitle.name}")
            lines.append("")
            _render_entries(lines, subtitle.entries, kind)
            lines.append("")

    if deck.tags:
        lines.append("## Tags")
        lines.append("")
        lines.append(" ".join(_render_tag(tag) for tag in deck.tags))

    while lines and lines[-1] == "":
        lines.pop()

    return "\n".join(lines) + "\n"


def save(deck: Deck, path: Path, *, kind: LanguageKind) -> None:
    text = write(deck, kind=kind)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except BaseException:
        os.unlink(tmp_path)
        raise
