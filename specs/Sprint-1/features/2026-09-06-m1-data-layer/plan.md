# M1 · The data layer — Plan

## 1. Models

1.1. Write `src/idiomas/models.py`:
   - `Entry` dataclass: `hanzi: str`, `pinyin: str`, `gloss: str`, `note: str | None = None`, `extra_fields: list[str] = field(default_factory=list)` (for tab-separated fields beyond the third).
   - `Category` dataclass: `name: str`, `entries: list[Entry]`.
   - `Deck` dataclass: `title: str`, `uncategorized: list[Entry]`, `categories: list[Category]`, `tags: list[str]`.
   - `Warning` dataclass: `line_number: int`, `message: str`, `raw_line: str`.

## 2. Parser

2.1. Write `src/idiomas/parser.py` with `parse(text: str, filename_stem: str) -> tuple[Deck, list[Warning]]`.

2.2. Header handling: read the first non-blank `# ...` line if present; if it doesn't match `filename_stem`, emit a warning but use `filename_stem` as `Deck.title` regardless (filename always wins).

2.3. Line classification, in order, per line:
   - blank → skip
   - `## Tags` → enter tags-parsing mode for the following non-blank line(s)
   - `## <Name>` → start new `Category`
   - line with ≥2 tabs → `Entry`, appended to current category or `uncategorized` if no category opened yet
   - indented `*...*` line directly following an entry line → attach as that entry's `note`
   - anything else non-blank → `Warning`, line preserved verbatim

2.4. Tags line parsing: split on whitespace outside quotes; strip leading `#` and surrounding `"..."` from each token; populate `Deck.tags`.

2.5. Return `(Deck, warnings)`.

## 3. Writer

3.1. Write `src/idiomas/writer.py` with `write(deck: Deck) -> str`:
   - Emit `# {deck.title}`, blank line.
   - Emit `deck.uncategorized` entries (tab-joined, notes as indented italic lines).
   - For each `Category` in `deck.categories`, in order: `## {name}`, blank line, its entries.
   - If `deck.tags` is non-empty: `## Tags`, blank line, space-separated tags (quoting any tag containing whitespace).
   - Omit the `## Tags` section entirely when `deck.tags` is empty.

3.2. Write `save(deck: Deck, path: Path) -> None`: serialize with `write()`, write to a temp file in `path.parent` (`tempfile.NamedTemporaryFile` or manual suffix), `os.replace(tmp, path)`.

## 4. Fixtures and round-trip tests

4.1. Create `tests/fixtures/` with hand-written `.md` files covering: a plain deck with categories, a deck with notes, a deck with no tags, a deck with no categories (all uncategorized), a deck with a mismatched header, and a deck with a stray unexpected line.

4.2. Write `tests/test_parser.py` and `tests/test_writer.py`:
   - Round-trip property test: for each fixture, `parse(write(*parse(text, stem))) == parse(text, stem)` (structural `Deck` equality) for every fixture that doesn't intentionally include stray lines.
   - No-op byte-identical test: for at least one clean fixture, `write(parse(text, stem)[0]) == text` exactly.
   - Per-fixture assertions for notes, missing tags, missing categories, uncategorized entries, and warnings on stray lines / mismatched headers.

4.3. Run `pytest` and confirm all tests pass.
