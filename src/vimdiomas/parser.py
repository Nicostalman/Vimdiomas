import shlex

from vimdiomas.languages import LanguageKind
from vimdiomas.models import Category, Deck, Entry, Subtitle, Warning


def _split_tags_line(line: str) -> list[str] | None:
    """The tokens on `line` as `shlex` reads them, or `None` if its quoting
    is unparseable. Each is a `#tag` as written; the caller strips the `#` and
    reports anything that never had one (Sprint 6 M9).

    `shlex.split` raises `ValueError` on an unclosed quote — a file whose
    Tags line was written by an older `writer._render_tag` (Sprint 6 M1, #3)
    can contain exactly that. Returning `None` lets the caller warn on the
    line instead of the exception escaping tree discovery.
    """
    try:
        return shlex.split(line)
    except ValueError:
        return None


def parse(
    text: str, filename_stem: str, *, kind: LanguageKind, grammar: bool = False
) -> tuple[Deck, list[Warning]]:
    """Parse `text` into a `Deck`. `kind` decides what an entry row is
    (Sprint 6 M6): `word<TAB>reading<TAB>translation` for a kind with a
    reading, `word<TAB>translation` for one without. It is required, with no
    default, for the reason the compiler's is: a silent Chinese default is the
    hardcoding Sprint 6 M5 removed. `grammar=True` (Sprint 5 M5) additionally
    recognises a `### ` line, inside a category and outside `## Tags`, as a
    `Subtitle` heading — the third level below a category and above its
    triads. With `grammar=False` (the default, and every vocabulary file's
    behaviour, unchanged), a `### ` line is just another unrecognized line,
    exactly as before this milestone.

    The warnings are the file's deviations from the format `writer.write`
    produces, and they are *reported* only where the deviation is lossy — the
    text does not reach the PDF as itself, or is read back as something other
    than what it says (Sprint 6 M9, `requirements.md` §§1–2). A deviation the
    next in-app write simply tidies away — a blank-line run, a note indented
    by two spaces, `## Tags` before the categories, a tag quoted where the
    writer would not have quoted it — is read back faithfully and says nothing. Warnings never change what this function
    returns: the `Deck` is what it has always been for every input."""
    deck = Deck(title=filename_stem)
    warnings: list[Warning] = []

    current_category: Category | None = None
    current_subtitle: Subtitle | None = None
    in_tags_section = False
    last_entry: Entry | None = None
    header_consumed = False
    tags_heading_seen = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()

        if stripped == "":
            last_entry = None
            continue

        if not header_consumed and stripped.startswith("# ") and not stripped.startswith("## "):
            header_consumed = True
            header_title = stripped[2:].strip()
            if header_title != filename_stem:
                warnings.append(
                    Warning(
                        line_number,
                        f"header '{header_title}' does not match filename '{filename_stem}'",
                        raw_line,
                    )
                )
            continue

        if stripped == "## Tags":
            if tags_heading_seen:
                # The writer emits one tag block, last. A second one means
                # either a category the user meant to call `Tags` — which the
                # app refuses to create (M1, #8) and which this reads as
                # metadata, so it is not a category at all — or entries that
                # are about to be read as tags.
                warnings.append(
                    Warning(line_number, "the tag block appears more than once", raw_line)
                )
            tags_heading_seen = True
            in_tags_section = True
            current_category = None
            current_subtitle = None
            last_entry = None
            continue

        if stripped.startswith("## "):
            name = stripped[3:].strip()
            if any(category.name == name for category in deck.categories):
                # Both headings render, so nothing is lost in the PDF — but
                # the app lists the name twice in its tree and a create writes
                # into the first, leaving the second unreachable from the app.
                # Creating one through Entry selects the existing category
                # instead (M1, #18).
                warnings.append(
                    Warning(line_number, f"category '{name}' appears more than once", raw_line)
                )
            current_category = Category(name=name)
            deck.categories.append(current_category)
            current_subtitle = None
            in_tags_section = False
            last_entry = None
            continue

        if grammar and stripped.startswith("### "):
            if in_tags_section or current_category is None:
                # A subtitle only exists under a category; outside one (or
                # inside ## Tags) it's dropped like any other stray line.
                warnings.append(Warning(line_number, "unrecognized line", raw_line))
            else:
                name = stripped[4:].strip()
                if any(subtitle.name == name for subtitle in current_category.subtitles):
                    # Same as a duplicate category: creating one in Entry
                    # selects the existing subtitle (Sprint 5 M5).
                    warnings.append(
                        Warning(
                            line_number, f"subtitle '{name}' appears more than once", raw_line
                        )
                    )
                current_subtitle = Subtitle(name=name)
                current_category.subtitles.append(current_subtitle)
            last_entry = None
            continue

        if in_tags_section:
            tokens = _split_tags_line(stripped)
            if tokens is None:
                warnings.append(Warning(line_number, "unparseable tag syntax", raw_line))
            else:
                # A token with no `#` is not a tag and is not written by the
                # app: prose under `## Tags`, or an entry row after it, each
                # word of which otherwise becomes a tag of its own and shows
                # up in Browse's filter. Still collected, exactly as before —
                # the warning reports, it does not change the deck.
                not_tags = [token for token in tokens if not token.startswith("#")]
                if not_tags:
                    warnings.append(
                        Warning(line_number, "not a tag: " + ", ".join(not_tags), raw_line)
                    )
                deck.tags.extend(token.lstrip("#") for token in tokens)
            last_entry = None
            continue

        is_indented = raw_line != raw_line.lstrip()
        if is_indented and stripped.startswith("*") and stripped.endswith("*") and last_entry is not None:
            last_entry.note = stripped[1:-1]
            continue

        # A row has one tab fewer than it has columns.
        min_tabs = 2 if kind.has_reading else 1
        if raw_line.count("\t") >= min_tabs:
            # Split the line with only its terminator removed, not `stripped`:
            # `str.strip()` treats a tab as whitespace, so a row with an empty
            # first or last field (`你<TAB>ni3<TAB>`) lost that field's boundary
            # before `split` ever ran, and the guard above — which counts tabs
            # on `raw_line` — disagreed with it (Sprint 6 M1, #2). Each field
            # is then stripped of *spaces* only, which keeps a space-padded row
            # reading as it always has while leaving field boundaries alone.
            fields = [field.strip(" ") for field in raw_line.rstrip("\n\r").split("\t")]
            if len(fields) < min_tabs + 1:
                # Unreachable given the tab-count guard, and deliberately not
                # an exception anyway: both tree screens parse every file to
                # build themselves, so one malformed row must never be able to
                # lock the user out of the whole tree.
                warnings.append(Warning(line_number, "malformed entry row", raw_line))
                last_entry = None
                continue
            if kind.has_reading:
                word, reading, translation, *extra = fields
            else:
                word, translation, *extra = fields
                reading = ""
            # A row has exactly as many fields as the kind has columns. A
            # further field with text in it survives a rewrite (the writer
            # keeps `extra_fields`) but is never rendered, so it sits on disk
            # and is missing from the PDF — `mission.md`'s "never silently
            # discard" case. An *empty* one is a stray tab with no text to
            # lose, and is tidied away by the next write.
            extra_with_text = [value for value in extra if value]
            if extra_with_text:
                warnings.append(
                    Warning(
                        line_number,
                        "extra column(s) never rendered: " + ", ".join(extra_with_text),
                        raw_line,
                    )
                )
            if word == "":
                # Entry's Create is a no-op without a word, so the app cannot
                # write this; it renders as a blank first column.
                warnings.append(Warning(line_number, "an entry with no word", raw_line))
            entry = Entry(word=word, reading=reading, translation=translation, extra_fields=extra)
            last_entry = entry
            if current_subtitle is not None:
                current_subtitle.entries.append(entry)
            elif current_category is not None:
                current_category.entries.append(entry)
            else:
                deck.uncategorized.append(entry)
            continue

        warnings.append(Warning(line_number, "unrecognized line", raw_line))
        last_entry = None

    if not header_consumed:
        # The one structural line the writer always emits. Nothing is lost —
        # pandoc titles the PDF from the filename either way — but a file with
        # no header is not a file the app produced, and the dev's rule is that
        # a missing core element reports like any other deviation. There is no
        # line to blame, so this is a file-level warning: line 0, no raw line.
        warnings.insert(0, Warning(0, f"no '# {filename_stem}' header line", ""))

    return deck, warnings
