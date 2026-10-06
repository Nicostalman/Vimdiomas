# M3 · One tree widget — plan

## 1. Add `SupaTree` to `base.py`

- In `src/idiomas/tui/screens/base.py`, add `SupaTree`, a generic `Tree`
  subclass carrying:
  - `Binding("j", "cursor_down", "Down", show=False)`
  - `Binding("k", "cursor_up", "Up", show=False)`
  - `Binding("shift+left", "screen.panel_prev", "Previous panel", show=False)`
  - `Binding("shift+right", "screen.panel_next", "Next panel", show=False)`
- Keep it generic over the node-data type (`Tree[T]` is already generic in
  Textual), so subclasses declare their own data type the same way
  `EntryTree(Tree[NodeData])` does today, just through `SupaTree` instead.
- Carry over the explanatory docstring content from `EntryTree` that is
  actually about the shared bindings (h/l have nothing to alias, shift+left/
  right are reserved for panel-switching) — the parts about `NodeData`/
  category selection stay behind in `entry.py`.

## 2. Move the shared CSS into a `SupaTree` rule

- In `src/idiomas/tui/app.tcss`, add a `SupaTree { ... }` rule carrying the
  generic aesthetic: `width: auto`, `border: round $accent`,
  `overflow-x: hidden`.
- Trim `EntryScreen EntryTree { ... }` down to just `max-width: 60%` — the
  one declaration that is about sharing the screen with the form panel, not
  about trees in general.

## 3. `EntryTree` adopts `SupaTree`

- In `src/idiomas/tui/screens/entry.py`, change `EntryTree(Tree[NodeData])`
  to `EntryTree(SupaTree[NodeData])`, drop the now-duplicated `BINDINGS` list
  and the docstring paragraphs that moved to the base, and update the import
  from `idiomas.tui.screens.base` to include `SupaTree`.
- Everything else in `entry.py` — `NodeData`, `NodeKind`,
  `VALID_TARGET_KINDS`, `build_tree`, `_add_dir_children` — is untouched.

## 4. Document the convention in `design.md`

- Add `SupaTree` to the "Implementation" list under Navigation conventions in
  `specs/current/design.md`, alongside `VimOptionList`/`PanelAwareInput`:
  what it carries (j/k, shift+left/right dispatch, the bordered/content-sized/
  no-h-scroll aesthetic), and that it is the one place to change every
  tree's shared look and feel, per the backlog's stated wish.

## 5. Verify no duplication, run tests

- Grep the codebase to confirm `j`/`k`/`shift+left`/`shift+right` tree
  bindings and the border/overflow-x/width CSS exist in exactly one place
  each (`SupaTree` and its CSS rule).
- Run `tests/test_tui_entry_screen.py` and the full suite; fix anything the
  refactor broke without changing intended behavior.
- Manually launch the app and compare the entry screen's tree, by eye,
  against its pre-refactor look and behavior (border, width, j/k, shift+left/
  right panel switching) before handing off to the dev.
