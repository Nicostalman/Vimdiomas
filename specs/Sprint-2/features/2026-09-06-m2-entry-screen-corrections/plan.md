# M2 · Entry screen corrections — plan

See [`requirements.md`](requirements.md) for scope and decisions.

## 1. Config gains `language`

- Add `language: str = "Chinese"` to `Config` in `src/idiomas/config.py`.
- Update `_write_config` to persist it, and `load_or_prompt_config` to read it
  with a default when the key is absent from an existing `.idiomas.toml`
  (`data.get("language", "Chinese")`).
- Check the call site(s) that construct `EntryScreen` (likely `app.py`) —
  change to pass the full `Config` rather than `source_root` alone.

## 2. Thread `Config` into `EntryScreen`, rename the tree root

- Change `EntryScreen.__init__(self, config: Config)`, store `self.config`,
  derive `self.source_root = config.source_root` (or use `config.source_root`
  directly at call sites — pick whichever keeps `entry.py`'s existing
  references working with the smallest diff).
- Change `EntryTree("source", ...)` in `compose()` to
  `EntryTree(f"{config.language} notebook", ...)`.
- Update the `EntryScreen(...)` construction call site accordingly.

## 3. `(uncategorized)` under every file

- In `_add_dir_children` (`entry.py`), drop the `if file_node.has_uncategorized`
  guard around the `(uncategorized)` leaf — add it unconditionally for every
  `file_node`.
- Check `src/idiomas/store.py` (`walk`, `DirNode`/file node construction) for
  `has_uncategorized`: if nothing else reads it after this change, remove the
  field and its computation; if something else depends on it, leave it.

## 4. Inert form when the tree cursor isn't on a valid target

- In `_on_node_highlighted`, when `new_target is None`:
  - swap the top slot from `#category-name` to a warning `Static` (new widget,
    e.g. `id="target-warning"`, text "Choose a category") — both live in the
    same top-of-panel position, toggled via `.display` the way
    `#category-name` already is.
  - set `disabled = True` on hanzi/pinyin/translation/note `Input`s and the
    Create button.
- When `new_target` is a valid target (`category`, `uncategorized`,
  `new_category`): hide the warning, restore `#category-name`'s existing
  `new_category`-only visibility, and set `disabled = False` on the four
  fields + button.
- `_visible_field_ids()` / `_focus_first_field()` / `action_next_field()` walk
  fields by `.display`; confirm disabled-but-visible fields are skipped
  correctly by Textual's own focus handling (`disabled` widgets are not
  focusable), or add an explicit filter if `chain` in `action_next_field`
  needs it.
- `_create_entry` already returns early when `target is None` — no change
  needed there, but confirm the Create button being `disabled` makes this
  path unreachable via UI (defense in depth, not a behavior change).

## 5. Pinyin read-only, `tab` skips it

- Set the `#pinyin` `Input`'s `disabled` or a read-only mode — check whether
  Textual's `Input` has a native `read_only`/`disabled` distinction that still
  allows programmatic `.value` assignment from `_on_hanzi_changed` (a fully
  `disabled` input may reject that; verify before committing to one flag).
- Remove `#pinyin` from `FIELD_ORDER`'s tab-navigable set, or filter it out in
  `_visible_field_ids()` — `tab` from hanzi must land on translation directly.
- Delete `_pinyin_touched` and `_last_prefilled_value`, and the
  `_on_pinyin_changed` handler that maintained them — dead code once pinyin
  can't be typed into. `_on_hanzi_changed` keeps writing `#pinyin`'s `.value`
  unconditionally (no more touched-guard).

## 6. `gloss` → `translation` (UI layer)

- `entry.py`: `Input(..., id="gloss")` → `id="translation"`, placeholder
  `"Gloss"` → `"Translation"`, `FIELD_ORDER` entry, local variable in
  `_create_entry` (`gloss` → `translation`, still passed as
  `Entry(gloss=translation, ...)`).
- `FOOTER_HINT` and any other user-facing string mentioning "gloss".
- `tests/test_tui_entry_screen.py`: update `#gloss` queries to `#translation`.

## 7. Footer hint rewrite

- Update `FOOTER_HINT` to describe the actual M2 key map: field navigation
  (`tab`), create (`enter` on the button / hanzi flow as implemented), `H`
  back to tree, `escape` defocus — reconcile wording with what M1 shipped
  (`c03637e`) rather than restating M1's own hint verbatim.

## 8. Tree horizontal scrollbar / sizing

- In `app.tcss`, adjust `EntryScreen EntryTree` so the tree's width tracks its
  content instead of clipping and scrolling horizontally — likely removing a
  fixed `width: 40%` in favor of `width: auto` (bounded by the `Horizontal`
  layout) or setting `overflow-x: hidden` if the content itself should wrap
  instead of scroll. Verify against a real tree with long file/category names.

## 9. Thinner input cursor, app-wide

- Add a `.tcss` rule targeting `Input` (not scoped to `EntryScreen`) that
  narrows the cursor — Textual exposes cursor styling via CSS
  (`Input > .input--cursor` or similar, confirm exact selector against the
  installed Textual version) — applied once so it covers `BrowseScreen`'s
  inputs too, per the roadmap note.

## 10. Tests

- Amend `tests/test_tui_entry_screen.py`:
  - `#gloss` → `#translation` queries.
  - New assertions for the disabled-state behavior (cursor off a leaf →
    fields disabled + warning shown; cursor on a leaf → fields enabled).
  - `(uncategorized)` present for a file with no loose entries.
  - Tree root label reflects `Config.language`.
  - `tab` from hanzi lands on translation, not pinyin.
  - Remove any test coverage that specifically exercised
    `_pinyin_touched`/`_last_prefilled_value` racing, since that code is gone.
