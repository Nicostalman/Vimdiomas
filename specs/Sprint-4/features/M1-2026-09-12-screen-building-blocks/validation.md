# M1 · Screen building blocks — validation

The acceptance bar for merging the branch. Grounded in the roadmap's done-when:
Entry opens with the tree focused; `esc` steps tree → panel → backpanel and then
does nothing; shift+hjkl move between panels only when a panel has focus; the
same holds from inside a form field; the dev confirms by eye that Entry is
otherwise unchanged; `design.md` documents the model; and the full suite passes.

## 1. Automated

```sh
.venv/bin/pytest
```

Passes with:

- **`tests/test_tui_panels.py`** (new) — all the generic model tests listed in
  `plan.md` § 1.6.
- **`tests/test_tui_entry_screen.py`** — the rewritten and new focus tests from
  `plan.md` § 3 pass, and **every non-navigation test passes unmodified**:
  tree structure, targets, tab cycling, pinyin prefill, create, autocompile,
  input method. A diff of this file touches only the tests named in `plan.md`
  § 3 and the `FormPanel` import.
- **`tests/test_tui_browse_screen.py`, `tests/test_tui_inspect_tree.py`,
  `tests/test_tui_landing_menu.py`, `tests/test_tui_main_menu.py`** — pass with
  **no changes at all**. This is the proof that the old model still works where
  M2 hasn't reached yet.
- No test count lower than before the branch (277 at `main`), apart from tests
  consciously replaced one-for-one in `plan.md` § 3.

## 2. Manual — Entry, by the agent before hand-off

Launch `idiomas` from the repo (`.venv/bin/python -m idiomas`) → Chinese
notebook → Enter vocabulary.

| # | Do | Expect |
|---|---|---|
| 1 | Open the screen | Tree focused, cursor line lit. Tree panel border accent, form panel border dim, screen-edge border dim. |
| 2 | `esc` | Tree panel focused: its border still accent, tree cursor line dims. |
| 3 | `esc` | Backpanel focused: both panel borders dim, screen-edge border **accent**. |
| 4 | `esc` again, several times | Nothing changes; the screen stays. |
| 5 | `enter` | Back in the tree, cursor lit; screen-edge border dim again. |
| 5b | `esc`, then `tab` | Back in the tree, cursor lit — same as `enter` (dev feedback, hands-on: `tab` originally did nothing here). |
| 5c | `esc`, `esc`, then `L` (or `H`) | From the backpanel, lands in the form (rightmost panel's content) — or back in the tree with `H` (leftmost). `J`/`K` do nothing here (Entry's panels don't stack vertically). Dev feedback, hands-on. |
| 6 | `esc`, then `L` | Lands in the form. With a directory highlighted: the form panel itself (accent border, no caret). With a category highlighted: the hanzi field. |
| 7 | From the tree panel, `H` | Nothing (left edge). |
| 8 | In the tree (content, not panel), press `L`, `H`, shift+`←`, shift+`→`, shift+`↑`, shift+`↓` | No panel switch, and — dev feedback, hands-on — the tree cursor does not move either; all six are equally inert. |
| 9 | In hanzi, type `HL` | The letters appear in the field. |
| 10 | In hanzi, shift+`←` | Dev feedback, hands-on: does nothing now (no more text-selection) — same as capital `H`. Focus stays in the field. |
| 11 | In hanzi, `esc` | Form panel focused, border accent, no caret; system input source switches back to English International. |
| 12 | `esc`, `enter` | Backpanel, then back into the tree. |
| 13 | From the form panel, `H` | Tree focused. |
| 14 | From the form panel, `tab` / `enter` | First enabled field. |
| 15 | In any field, `q` | Types `q`. |
| 16 | From a panel or the backpanel, `q` | Leaves Enter vocabulary. |
| 17 | Add a word to a category, then add one with `(new category)` | Both work exactly as before M1. |

## 3. Manual — nothing else moved

| # | Do | Expect |
|---|---|---|
| 18 | Browse: shift+arrows and `H`/`L` from the filters and results | Cycle panels with wraparound, exactly as before M1. |
| 19 | Inspect Tree: open, `j`/`k`, `tab`, `q` | Unchanged. |
| 20 | Landing menu, notebook menu, Settings | Unchanged. |

## 4. By the dev

- Entry looks the same as before M1 apart from the intended visual changes
  listed in `requirements.md` § *The focus look* (tree/form border behavior,
  plus the screen-edge backpanel border added after dev feedback, hands-on).
- The keys feel right after hands-on use. Any change requested is written into
  `requirements.md`/`plan.md`/this file before the code changes.

## 5. Docs

- `specs/current/design.md` states the vocabulary, the new key table, the
  landing/going-in rules, the focus look, `panels.py`'s classes, and the
  transition note for M2.
- `specs/current/stack.md` has the *Screen composition* section.
- Nothing in these three spec files contradicts the code on the branch.
