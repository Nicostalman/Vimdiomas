# M1 · The data layer — Validation

Acceptance bar for merging this branch, grounded in the roadmap's own "Done when": `parse(write(deck)) == deck` holds across fixtures covering notes, missing tags, missing categories, uncategorized entries and stray lines; and a file that is parsed and rewritten with no changes is byte-identical.

## Checks

1. **Round-trip property holds across fixtures.**
   ```sh
   pytest tests/test_parser.py tests/test_writer.py -v
   ```
   Passes if every fixture-driven test asserting `parse(write(deck)) == deck` (structural dataclass equality) succeeds, for fixtures covering:
   - an entry with a note
   - a deck with no `## Tags` section (tags omitted, not empty-emitted)
   - a deck with no categories (all entries uncategorized)
   - a deck with uncategorized entries preceding its first category
   - a deck containing a stray/unexpected line (asserted to produce a `Warning`, not to be dropped)

2. **No-op rewrite is byte-identical.**
   - For a clean fixture with no stray lines and no mismatched header, `write(parse(text, stem)[0]) == text` holds exactly (not just structurally equal after re-parsing).

3. **Filename wins over a mismatched header.**
   - A fixture whose `# Title` line does not match its filename stem parses with `Deck.title == filename_stem` and produces exactly one `Warning` referencing the mismatch.

4. **Unrecognized lines are never silently dropped.**
   - A fixture with a stray line produces a `Warning` carrying that line's original text (`raw_line`), and no exception is raised.

5. **Atomic save behaves correctly.**
   ```sh
   python -c "
   from pathlib import Path
   from idiomas.parser import parse
   from idiomas.writer import save
   deck, _ = parse(Path('tests/fixtures/<a-clean-fixture>.md').read_text(), '<stem>')
   save(deck, Path('/tmp/idiomas-save-test.md'))
   "
   ```
   Passes if the target file is created/replaced with no partial-write artifacts left behind (no stray temp file in the directory afterward).

6. **Full suite is green.**
   ```sh
   pytest
   ```
   Passes with zero failures and zero unexpected warnings from pytest itself (not to be confused with the parser's own `Warning` objects).

## Out of scope for this validation

- Pinyin conversion correctness (M2) — entries with numbered pinyin strings are treated as opaque text in this milestone's fixtures.
- Any TUI-driven entry creation or category creation flow (M5) — this validation only exercises `parse`/`write`/`save` as pure functions and file I/O.
- Compile-time rendering of pinyin or hanzi (M4).

## Merge bar

All six checks pass on a clean clone of this branch. No open questions from `requirements.md` remain unresolved.
