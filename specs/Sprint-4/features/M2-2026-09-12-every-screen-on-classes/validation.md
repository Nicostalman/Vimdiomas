# M2 · Every screen on the new classes — validation

The acceptance bar for merging the branch. Grounded in the roadmap's done-when:
every screen and menu opens focused on its first panel's content; `esc` climbs
content → panel everywhere, and panel → backpanel wherever the backpanel is
actually reachable (more than one panel — Entry only, among this milestone's
screens); shift+hjkl move spatially everywhere; Browse opens on the filename
filter and `esc` leaves it; the dev confirms each screen by hand-testing; and
the full test suite passes.

## 1. Automated

```sh
.venv/bin/pytest
```

Passes with:

- **`tests/test_tui_panels.py`** — the new flat-`Backpanel` cases from
  `plan.md` § 1.5, alongside every existing case unchanged.
- **`tests/test_tui_browse_screen.py`, `tests/test_tui_inspect_tree.py`,
  `tests/test_tui_landing_menu.py`, `tests/test_tui_main_menu.py`** — the
  rewritten/new navigation tests from `plan.md` § 4 pass, and every
  non-navigation test (filtering, results, file operations, dialogs, compile,
  mode toggling, item selection) passes **unmodified**.
- No test count lower than 309 (the count on `main` at branch start), apart
  from the one-for-one replacements named in `plan.md` § 4.
- `NavigableScreen`, `PanelAwareInput`, `SupaTree`, and the old `MenuScreen`
  no longer appear anywhere in `src/` or `tests/` (`grep -rn` comes back
  empty for all four).

## 2. Manual — Browse

Launch `idiomas` from the repo → Chinese notebook → Browse.

| # | Do | Expect |
|---|---|---|
| 1 | Open the screen | Filename filter focused (caret visible); panel border accent, screen-edge border dim; results list shows its own border with the first row highlighted. |
| 2 | `esc` | Panel focused: border stays accent, caret gone. |
| 3 | `esc` again | Nothing changes — one panel, so the backpanel is never reached; screen-edge border stays dim. |
| 4 | `H`/`L`/`J`/`K`/shift-arrows from the panel | Nothing — one panel, nowhere to go. |
| 5 | `enter` | Back in the filename filter. |
| 6 | `tab`, `tab`, `tab` from the filename filter | Tag filter, then results, then back to the filename filter — no bounce through the panel or backpanel. |
| 7 | Type in filename filter to narrow the results | The highlighted row stays on the new first result. |
| 8 | Filter down to one result, `enter` on it | Opens the PDF, unchanged from before. |
| 9 | In a filter field, `q` | Types `q`. |
| 10 | From the panel, `q` | Leaves Browse. |

## 3. Manual — Inspect Tree

Main menu → Inspect tree.

| # | Do | Expect |
|---|---|---|
| 1 | Open the screen | Tree focused, cursor lit; panel border accent, screen-edge dim. |
| 2 | `esc` | Panel focused, border stays accent. |
| 3 | `esc` again | Nothing changes — one panel, so the backpanel is never reached. |
| 4 | `enter` | Back in the tree. |
| 5 | shift-arrows / capital H/L/J/K on the tree (content) | Cursor doesn't move, no panel switch — same inertness as Entry's tree in M1. |
| 6 | `tab` while the tree has focus | Toggles PDF/MD mode, same as before M2. |
| 7 | `esc` (panel focused), then `tab` | Focuses the tree (not a mode toggle). |
| 8 | `d`/`r`/`n`/`m`/`u` on a node | Unchanged from before M2. |
| 9 | `q` | Leaves Inspect Tree. |

## 4. Manual — menus (Landing, Main menu, Settings)

| # | Do | Expect |
|---|---|---|
| 1 | Open any menu | List focused, highlight visible; backpanel border accent (the flat-menu look); comfortable gray padding above/below the list, not touching the highlight. |
| 2 | `esc` | Nothing changes — list stays focused, border stays accent. |
| 3 | shift-arrows / capital H/L/J/K | No-ops. |
| 4 | `j`/`k` | Move the highlight, unchanged. |
| 5 | `enter` on an item | Selects it, unchanged (opens the notebook, settings, or a placeholder). |
| 6 | `q` on the landing menu | Exits the app. |
| 7 | `q` on Settings or the main menu | Returns to the previous menu. |

## 5. Manual — placeholders

Trigger one (German notebook, a Settings item, or Compile with nothing to do).

| # | Do | Expect |
|---|---|---|
| 1 | Open | Panel focused (bordered, accent) around the message — nothing focusable inside it. |
| 2 | `esc` | Nothing changes — one panel, so the backpanel is never reached. |
| 3 | `q` | Leaves the placeholder. |

## 6. By the dev

- Every screen looks and feels consistent: same border/focus conventions
  everywhere, no leftover screen-specific navigation quirks.
- Browse's fix is confirmed by hand: it no longer opens with focus stuck on
  the results list, and `esc` from a filter field is no longer a dead end.
- **Regression check on Entry** (not touched by this milestone's screen
  list, but sharing `panels.py` with everything that was): `esc` from the
  tree panel or the form panel still reaches the backpanel — two panels, so
  `Backpanel.reachable()` is `True` there, unlike every single-panel screen
  in this milestone.
- Any change requested is written into `requirements.md`/`plan.md`/this file
  before the code changes.

## 7. Docs

- `specs/current/design.md` no longer has a *Transition* section or an old
  key table — one model, documented once, covers every screen including
  flat menus.
- `specs/current/stack.md` no longer mentions the retired trio.
- Nothing in these two spec files contradicts the code on the branch.
