# M4 · Unreadable notebook files — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The reader (§1)

- `store.py`: `SourceReadError(OSError)` and `read_source(path)`.
- `store._parse_file` and `ContentIndex.refresh` read through it; their
  behaviour and the warning text stay byte for byte.
- `tests/test_store.py`: `read_source` tests as §7 lists. The existing
  `test_a_file_that_cannot_be_decoded_is_still_in_the_tree` and the
  `ContentIndex` tests must pass unchanged.

## 2. Compile (§2)

- `compile.render_source` reads through `read_source`.
- `compile_all`: `render_source` under its own `try`, `SourceReadError` into
  `report.failed`, `continue`; no warnings, no cache change for that file.
- `tests/test_compile.py`, `tests/test_main.py`, `tests/test_tui_main_menu.py`
  as §7 lists (CLI exit status and stderr, the Compile screen's *Failed:*
  block, the app still running).
- Pin the single-file paths with a test each, with no code change expected:
  `autocompile_one` and `open_source_pdf` on a bad source notify and open
  nothing (`tests/test_tui_inspect_tree.py` / `test_tui_browse_screen.py`).

## 3. Browse's tag filter (§3)

- `store.tag_index`: skip a file whose `stat()` or `read_source` fails; leave
  it out of the returned cache.
- `tests/test_store.py` for `tag_index` (bad file before and after, then fixed);
  `tests/test_tui_browse_screen.py` for both modes.

## 4. Inspect Tree (§4, §5)

- `inspect.py`: the MD preview's read through `read_source`, the message
  `<name> <exc>`; `_rename_file`'s retitle read, the warning, and the skipped
  recompile.
- `tests/test_tui_inspect_tree.py` as §7 lists. Update the existing test that
  pins `Could not read …` for an `OSError`, if there is one, to the new text.

## 5. Entry (§6)

- `entry.py`: `_read_deck` through `read_source`; the callers handle
  `SourceReadError` with one shared notification helper, so the five sites say
  the same thing; `_read_category` returns nothing instead of raising and the
  subtitle select is left with no choices.
- `tests/test_tui_entry_screen.py` as §7 lists.

## 6. Specs and docs (§8)

- `design.md` and `stack.md` as §8 lists.
- If anything comes up while implementing, the three files here are updated
  first. A `read_text` site found later that §1 to §6 do not name is a gap in
  this spec: add it to the section it belongs to before touching it.

## 7. Checks before the hand-off

- Full test suite on the Mac.
- The greps and the by-hand pass in [`validation.md`](validation.md).
- Stop for the dev's review and hand-testing.

## 8. Hand-off, merge

- PR, squash-merge, cleanup per `feature-spec` step 9.
- Notes on `main`: M4's decisions into settled form.
- M4 is the sprint's last milestone: ask the dev whether to close the sprint
  now (`changelog`).
