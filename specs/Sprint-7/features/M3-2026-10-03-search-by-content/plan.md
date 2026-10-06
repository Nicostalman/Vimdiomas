# M3 · Search by content — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Matching and indexing, pure (§3.1–§3.4, §3.7)

- `tests/test_store.py`, written first:
  - `fold` and `pinyin_key`: every pair in `validation.md` §2's tables.
  - `ContentIndex`: parses grammar files as grammar, so subtitles exist. Re-parses
    only a file whose mtime changed. Drops a deleted file. Skips an unreadable or
    non-UTF-8 file without raising.
  - `search_content(index, query, *, tree_root, kind, tagged=None)`: the hits for
    `validation.md` §2's fixture tree, in §3.4's order. Each hit carries its kind
    (entry, category or subtitle), its source path, its location parts and its
    fields. An entry matching on several fields appears once. With `tagged`, hits
    come only from those files.
- `store.py`: `fold`, `pinyin_key`, `ContentIndex`, a `ContentHit` dataclass and
  `search_content`. Files are walked in `store.walk`'s order: reuse its sort,
  don't write a second one.

## 2. Row formatting, pure (§3.5)

- Tests first, in `tests/test_tui_browse_screen.py`: `format_row` for an entry
  that fits, one where the longest field is cut first, one where every field is
  at its minimum and the location is cut from the left, a hanzi-heavy row (cell
  width, not `len`), and brackets kept literal. Its width never exceeds `W` for
  every `W` from 8 to 120 over a long grammar row.
- `browse.py`: `format_row(fields, location, width) -> Text`. `hit_fields(hit,
  kind)` builds the field list: the reading through `to_tone_marks`, empty
  fields dropped. A category or subtitle is its bare name, to be styled bold
  by the caller (`format_row` takes a `style`).

## 3. Shared PDF opening (§3.6)

- Move `InspectTreeScreen._open_pdf`'s body into one function both screens call
  (`open_source_pdf(app, source_path, *, tree_root, kind)`), in `tui/screens/base.py`
  next to `autocompile_one` — the other shared compile utility, and where
  `compile_file`/`open_file` are already imported. Inspect Tree calls it, and
  its behaviour is unchanged.
- The existing Inspect Tree tests for opening a PDF and for a failed compile
  keep their assertions unchanged; only their monkeypatch target moves from
  `idiomas.tui.screens.inspect` to `idiomas.tui.screens.base`, since that's
  where `compile_file`/`open_file` are now resolved from — the same
  convention the autocompile tests already use.

## 4. Browse layout and navigation (§1, §2)

- Update the existing Browse tests for the renamed `#query` and the
  three-panel layout. **Replace** `test_tab_cycles_filename_tag_and_results`
  and `test_escape_focuses_panel_then_does_nothing`, whose behaviour this
  milestone changes on purpose. Every other filename-mode test passes with only
  the field rename.
- New tests for §1's keys table, row by row (`validation.md` §3).
- `browse.py`: three `Panel`s in the order query, results, tag. `#query`
  replaces `#filename-filter`.
  `#mode-badge` and `#footer-hint` move into the results panel. `tab` toggles
  the mode, with the focus rule for an emptied list. `enter` in the two fields
  moves on. `FIELD_ORDER` and `action_next_field` are removed.
- `app.tcss`: the query and tag panels are one content row tall, the results
  panel is `1fr`, and `#results` drops its border. The badge reuses
  `#mode-badge`'s existing rules. Add `.mode-filename` (red) and
  `.mode-content` (blue) or generalise the existing classes, whichever is
  smaller.

## 5. Content mode in Browse (§3)

- Tests (`validation.md` §4): the empty-query hint, hits for a hanzi, its
  pinyin and its translation; German word and translation; a category and a
  subtitle; the tag filter; the query text kept across a toggle; `No matches.`;
  Enter on an entry, a category and an uncompiled file opening (or compiling
  and then opening) the right PDF; a compile failure notifying.
- `browse.py`: `_refresh_results` branches on the mode. Content mode uses the
  screen's `ContentIndex`, `paths_with_tag` turned back into source paths for
  `tagged`, and `format_row` at the list's current content width. Option ids
  map back to the hit's source path. Re-render the rows on `Resize`.

## 6. `design.md` (§4)

- *Screen modes*, the *Keys* table's `tab` row, the reachability and
  *Flat menus* paragraphs, and the Browse paragraph, as §4 lists.

## 7. Finish

- The full suite: `pytest`, integration tests included where the tools exist.
- Run the app against the dev's real trees (`validation.md` §5) and report what
  it shows before handing off.
