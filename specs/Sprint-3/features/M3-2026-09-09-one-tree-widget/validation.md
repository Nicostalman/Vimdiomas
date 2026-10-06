# M3 · One tree widget — validation

Grounded in the roadmap's done-when: `EntryScreen`'s tree renders identically
to before; `tests/test_tui_entry_screen.py` passes unchanged where it can; the
base widget is documented in `design.md`; no tree styling remains duplicated
outside it.

## Automated

- `pytest tests/test_tui_entry_screen.py` passes with no changes to the test
  file itself (a change there would mean the refactor altered observable
  behavior).
- `pytest` (full suite) passes.
- `grep -rn "cursor_down\|cursor_up" src/idiomas/tui/screens/entry.py` and a
  search for `shift+left`/`shift+right` `Binding(...)` calls in `entry.py`
  return nothing — those bindings live only in `SupaTree` now.
- `grep -n "overflow-x\|border: round \$accent" src/idiomas/tui/app.tcss`
  shows the tree's border/overflow-x declared once, under `SupaTree`, not
  under `EntryScreen EntryTree`.

## Manual (dev sign-off)

- Launch the app, open *Enter vocabulary*, and confirm the tree panel looks
  exactly as before: same border, same width relative to the form panel, no
  horizontal scrollbar.
- Confirm `j`/`k` move the cursor up/down in the tree as before.
- Confirm `shift+left`/`shift+right` (and `H`/`L`) switch focus between tree
  and form panel as before.
- Confirm the tree's actual content and interaction — categories, entering
  the create-entry flow — work exactly as they did pre-refactor.

## Done when

All of the above pass, and the dev confirms by eye that the entry screen is
indistinguishable from before the refactor.
