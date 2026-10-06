# M5 · The grammar folder — format and entry — plan

Task groups, ordered so later groups depend only on earlier ones.

## 1. Model and grammar detection

- `models.py`: new `Subtitle(name: str, entries: list[Entry])`; `Category`
  gains `subtitles: list[Subtitle] = field(default_factory=list)`.
- `store.py`: `is_grammar(path: Path, tree_root: Path) -> bool` — `True` iff
  `path` is under `tree_root`, and the first part of the relative path is a
  directory named `grammar` (case-insensitive) with more parts after it. A path
  outside `tree_root` returns `False`.
- Tests (`test_store.py`): `Grammar/x.md`, `grammar/sub/x.md` → `True`;
  `Vocabulary/x.md`, `Vocabulary/Grammar/x.md`, a file named `Grammar.md` at
  the root, a path outside the root → `False`.

## 2. Parser and writer

- `parser.parse(text, filename_stem, *, grammar: bool = False)`.
  - `grammar=True`: a `### name` line inside a category opens a new `Subtitle`
    on it; the following entries (and their notes) go there until the next
    `###`, `##` or `## Tags`. A `###` with no current category (before any
    `##`, or in the tags section) is an "unrecognized line" warning.
  - `grammar=False`: unchanged, line for line.
- `writer.write`: after a category's loose entries, for each subtitle emit
  `### name`, a blank line, its entries, a blank line. No flag.
- Fixtures: `tests/fixtures/Grammar.md` — loose entries, a category with loose
  entries then two subtitles (one with a noted entry), a subtitle with no
  entries, a category with no subtitles, and tags.
- Tests (`test_parser.py`, `test_writer.py`):
  - The fixture parses into the expected structure under `grammar=True`.
  - The same text under `grammar=False` gives today's result: `###` lines are
    warnings, their entries flattened into the category.
  - Round trip `parse(write(deck), grammar=True) == deck` for the fixture, and
    `write(parse(text))` is byte-identical to the fixture text.
  - Round trip for a grammar deck with no subtitles, and a subtitle with no
    entries.
  - Copies of the dev's two real grammar files (`Asking for directions.md`,
    `Clasificadores.md`, added as fixtures) parse to the same `Deck` under
    `grammar=True` and `grammar=False`, with no new warnings.
  - `###` before any category → warning under `grammar=True`.
  - Every existing parser/writer test still passes untouched.

## 3. Compile

- `compile.render_markdown`: after a category's loose-entry table, each
  subtitle as `### name`, blank line, and its table if it has entries.
- `compile_file(source_path, notebook_path, *, grammar: bool = False)` passes
  `grammar` to `parse`.
- `compile_all` computes `grammar = is_grammar(source_path, tree_root)` per
  file and uses it for both the stamp's parse and `compile_file`.
- `base.autocompile_one` gains a `grammar` argument passed through to
  `compile_file`; Entry and Inspect Tree compute it from their `tree_root`.
  Inspect Tree's `_open_pdf` fallback compile does the same.
- Tests (`test_compile.py`):
  - `render_markdown` on a deck with subtitles emits `### name` headings in
    the right order, and an empty subtitle as a bare heading.
  - `render_markdown` on a vocabulary deck is byte-identical to before (an
    existing-output test, or assert no `###` appears).
  - `compile_all` over a tree with `Grammar/g.md` containing a subtitle
    produces a PDF (integration, real pandoc/xelatex — existing convention),
    and the intermediate markdown for it contains the subtitle heading.

## 4. `SelectField` support

- `panels.SelectField.set_choices(choices, value="")`: replaces the options in
  the deployed list and resets the value (and its display line).
- `SelectField.Changed(select_field, value)` message, posted when the user
  picks an option (not when the value is set in code).
- Tests (`test_tui_panels.py`): `set_choices` swaps the options shown on
  expand; picking an option posts `Changed` with the new value.

## 5. Entry's grammar panel

- `NodeData` gains `grammar: bool = False`, set in the file-leaf builder from
  `is_grammar(file_path, tree_root)` (`build_tree` takes `tree_root`).
- Form: add `SelectField(label="Subtitle", id="subtitle")` and
  `TextField(placeholder="new subtitle name", id="subtitle-name")` between the
  category-name field and hanzi. `FIELD_ORDER` becomes `category-name,
  subtitle, subtitle-name, hanzi, pinyin, translation, note`.
- `_apply_target_state`: the subtitle field shows only for a
  `kind == "category"` target with `grammar=True`; on entering such a target,
  parse the file (`grammar=True`) and `set_choices` to `(none)`, each existing
  subtitle of that category, `(new subtitle)`. `subtitle-name` shows only
  while the subtitle value is `(new subtitle)`.
- `on SelectField.Changed` for `#subtitle`: show/hide `subtitle-name`.
- `_visible_field_ids` / `_focus_first_field` / `_clear_form` work on any
  widget, not just `Input` (`_clear_form` clears text fields only; the subtitle
  selection is kept — see requirements).
- `_create_entry` for a grammar category target:
  - `(new subtitle)` + empty name → no-op.
  - `(new subtitle)` + name → find or create that `Subtitle` on the category;
    if hanzi is filled, append the entry to it. Save, mark dirty, refresh the
    choices, select the subtitle, notify (`"<name> added successfully!"` for
    an empty new subtitle, the hanzi's message otherwise).
  - An existing subtitle → append to it. `(none)` → append to
    `category.entries`, as today.
  - Every parse/save here uses `grammar=True`.
- Autocompile on leaving passes `grammar` per dirty file.
- Footer hint unchanged (the select uses `enter` like Settings' — no new key
  to advertise).
- Tests (`test_tui_entry_screen.py`), with a temp tree holding
  `Grammar/G.md` and `Vocabulary/V.md`:
  - A vocabulary category → no subtitle field; a grammar category → subtitle
    field present, choices `(none)` + existing + `(new subtitle)`.
  - Grammar `(uncategorized)` and `(new category)` → no subtitle field.
  - Adding with `(none)` puts the entry in `category.entries`.
  - Adding under an existing subtitle puts it there, and the file on disk has
    the `###` heading with the entry under it.
  - `(new subtitle)` + name + hanzi → subtitle created with the entry; the
    field then shows the new subtitle, and a second add goes to it.
  - `(new subtitle)` + name, no hanzi → empty subtitle created.
  - `(new subtitle)` + no name → nothing written.
  - Tab cycles through the subtitle field (and name field when shown).
  - Every existing Entry test still passes untouched.

## 6. Docs

- `specs/current/design.md`: Entry's section gains the grammar panel (subtitle
  field, `(new subtitle)`), stated once.
- `specs/current/stack.md`: the file-format section gains `###` subtitles for
  grammar files and the `Grammar/` rule.
- Update this milestone's spec files as anything changes during
  implementation.
