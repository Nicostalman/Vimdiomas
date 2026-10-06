# M1 · The data layer — Requirements

## Roadmap anchor

**Deliverable.**
- `Entry`, `Category`, `Deck` dataclasses.
- A parser tolerant of hand-editing: filename wins over a mismatched header; `Tags` recognized wherever it sits; any line with ≥2 tabs is an entry; an indented italic line is the note for the entry above; unrecognized lines are preserved verbatim and reported as warnings rather than dropped.
- A deterministic writer that enforces the structural invariants — header first, uncategorized entries before the first `##`, categories in existing order, `## Tags` always last and omitted when empty — and saves atomically via a temp file plus `os.replace`.

**Done when.** `parse(write(deck)) == deck` holds across fixtures covering notes, missing tags, missing categories, uncategorized entries and stray lines; and a file that is parsed and rewritten with no changes is byte-identical.

## Scope

In scope for this phase:

- `src/idiomas/models.py` — `Entry`, `Category`, `Deck` dataclasses, per the concrete file format decided below.
- `src/idiomas/parser.py` — `parse(text: str) -> tuple[Deck, list[Warning]]`, tolerant of hand-editing per the roadmap's rules.
- `src/idiomas/writer.py` — `write(deck: Deck) -> str` (deterministic serialization) and `save(deck: Deck, path: Path) -> None` (atomic write via temp file + `os.replace`).
- Test fixtures and pytest tests establishing the `parse(write(deck)) == deck` round-trip property and byte-identical no-op rewrite.

Explicitly deferred (belongs to later milestones):

- Pinyin conversion or validation (M2) — the parser stores pinyin fields as opaque strings, numbered or not; it does not interpret or convert them.
- Discovery/search over the tree (`store.py`, M3).
- Anything about compiling to PDF (M4) or the TUI (M5).
- Anticipating M5's tree/category-ordering UI needs or M4's compile needs beyond what M1's own round-trip property requires — the model is scoped strictly to parse/write correctness for this phase.

## File format

No example file existed before this phase; the following is fixed here as the concrete shape the parser and writer implement, elaborating the roadmap's deliverable text.

```
# Food

苹果	ping2guo3	apple

## Vegetables

番茄	fan1qie2	tomato
    *sometimes called 西红柿 in the north*
胡萝卜	hu2luo2bo	carrot

## Fruits

香蕉	xiang1jiao1	banana

## Tags

#food #travel #"C1 exam"
```

- **Header.** First non-blank line, `# <Title>`. On parse, the filename (stem) is authoritative for the deck's title; a mismatched header is a warning, not an error, and the writer always emits the filename-derived title.
- **Entry line.** Any line containing **two or more tab characters** is an entry: `hanzi\tpinyin\tgloss`. Extra tab-separated fields beyond the third are preserved as additional trailing fields on `Entry` rather than dropped, so a stray tab from hand-editing doesn't lose data — but M1's own fixtures only exercise the three-field case.
- **Note line.** A line immediately following an entry that is indented and wrapped in `*italic*` markers is that entry's note (`Entry.note: str | None`). Non-indented or non-italic lines never attach as notes.
- **Category heading.** `## <Name>` starts a category; subsequent entries belong to it until the next `##` heading or `## Tags`. Categories preserve file order in the `Deck.categories` list.
- **Uncategorized entries.** Entry lines appearing before the first `## <Name>` heading (and not under `## Tags`) belong to `Deck.uncategorized: list[Entry]`.
- **Tags block.** A `## Tags` heading, recognized case-sensitively wherever it appears in the file (not necessarily last on parse — the roadmap says the *writer* always places it last, not that the parser requires it there). Its body is a line of space-separated tags; a tag is either a bare word (`#travel`) or a quoted multi-word tag (`#"C1 exam"`). Parsed into `Deck.tags: list[str]` without the leading `#` or quotes.
- **Stray lines.** Any non-blank line that is not a header, category heading, tags heading, entry line, or valid note line is preserved verbatim in `Deck.stray_lines` (or attached positionally — see Decisions) and reported as a `Warning`, never dropped.

## Decisions

- **Parser return shape:** `parse(text: str) -> tuple[Deck, list[Warning]]`. `Warning` is a small dataclass (`line_number: int, message: str, raw_line: str`) rather than Python's `warnings` module or exceptions — the parser is a pure function, and callers (TUI, tests) decide how to surface warnings (log, display, assert-empty-in-tests) without catching exceptions or configuring the stdlib warning filter.
- **Stray line placement:** stray lines are preserved with enough positional information (line number, and which section they fell in) that a future writer enhancement *could* re-emit them in place — but for M1, `write()` is only required to be deterministic and round-trip through `parse`, not to guarantee stray-line placement survives a rewrite. A no-op parse-then-write round-trip (no stray lines involved) must still be byte-identical per the roadmap's done-when condition.
- **`Deck.title`:** always derived from the filename at parse time (the roadmap's "filename wins" rule), stored on `Deck`, and used verbatim by the writer to emit `# <Title>`. Since `parse()` takes raw text with no filename argument in isolation, `parse()` accepts an explicit `filename_stem: str` parameter alongside `text`, rather than trying to infer authority from the header line alone.
- **Multi-word tags:** stored without their surrounding quotes in `Deck.tags` (so `#"C1 exam"` parses to `"C1 exam"`); the writer re-quotes any tag containing whitespace when serializing.
- **Equality for the round-trip property:** `Entry`, `Category`, `Deck` are plain `@dataclass` (not frozen, but eq-generating) so `==` is structural and `parse(write(deck)) == deck` is a direct dataclass equality check in tests.
- **Atomic save:** `writer.save()` writes to a temp file in the same directory as the target (so `os.replace` stays on one filesystem) and replaces the target only after the write succeeds.

## Context

- This is the second roadmap phase; `specs/2026-09-06-m0-scaffold/` is the only prior spec folder, and it left `src/idiomas/` with only `__init__.py` and `__main__.py`.
- `stack.md`'s "Storage" section is the authority for *why* tabs and numbered pinyin were chosen; this phase does not revisit that reasoning, only implements it.
- Per the roadmap's own ordering note, this milestone is "the correctness backbone" — every later milestone (compile, TUI) is built on `parse(write(deck)) == deck` holding, so the round-trip property is the non-negotiable bar, not a nice-to-have.
