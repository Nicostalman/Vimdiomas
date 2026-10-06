# Plan — M4 · Inspect Tree, functional

## 1. Shared `FooterHint` widget

- Add `FooterHint` to `tui/screens/base.py`, alongside `SupaTree`/`MenuScreen`/
  `VimOptionList`/`PanelAwareInput`: a small `Static` subclass (or thin wrapper)
  that takes a hint string and renders it the way Entry screen's
  `#footer-hint` `Static` does today. Give it a stable CSS class (e.g.
  `.footer-hint`) so `app.tcss` styles it from one place.
- Migrate `EntryScreen`: replace `Static(FOOTER_HINT, id="footer-hint")` with
  `FooterHint(FOOTER_HINT, id="footer-hint")`. No behavior change — verify
  `tests/test_tui_entry_screen.py` still passes unchanged.
- Record the widget in `design.md`'s implementation notes, next to `SupaTree`.

## 2. Inspect Tree screen scaffold

- New module `tui/screens/inspect.py`.
- `NodeData` dataclass local to this module: `kind: Literal["dir", "file"]`,
  `path: Path | None` (the `.md` path for a file leaf).
- `InspectTree(SupaTree[NodeData])` — no extra keys/aesthetic beyond what
  `SupaTree` gives; leaves are files, not categories.
- `build_tree(tree, dir_node)` walking `store.walk()`'s `DirNode`/`FileNode`
  output: one child node per subdirectory (kind="dir", expanded), one **leaf**
  per `FileNode` (kind="file", path=file_node.path — the `.md` path), named by
  the file's stem. No per-file category expansion (that's `EntryTree`'s job,
  not this tree's).
- `InspectTreeScreen(NavigableScreen)`: single-panel screen (`InspectTree` is
  the only widget), `mode: Literal["pdf", "md"]` instance attribute, always
  reset to `"pdf"` in `__init__`/`on_mount` (no persistence across pushes).
  Footer hint via the new `FooterHint`, e.g. "Tab: switch PDF/MD ·
  Enter: open".

## 3. Wire into the notebook menu

- `main_menu.py`: delete the `Option("Notebook", id="notebook")` entry and its
  `_notebook` handler/dispatch-table row.
- `_inspect_tree` now pushes `InspectTreeScreen(self.app.config.tree_root)`
  instead of the placeholder.
- Update `tests/test_tui_main_menu.py` for the removed option (drop
  the "Notebook" assertions, add coverage that "Inspect tree" pushes the real
  screen rather than a placeholder — matching how `test_tui_main_menu.py`
  already checks `enter_vocabulary`/`browse`).

## 4. PDF mode

- `tab` binding toggles `self.mode` between `"pdf"`/`"md"`, updates the footer
  hint text, and toggles `.mode-pdf`/`.mode-md` CSS classes on the tree
  widget — `app.tcss` gives these a red/blue border respectively, overriding
  `SupaTree`'s shared `$accent` border, so the current mode is visible at a
  glance and not just inferred from the footer text.
- A `Static#mode-badge` above the tree reads `"PDF MODE"`/`"MD MODE"`, colored
  red/blue via the same `.mode-pdf`/`.mode-md` classes (styled by `id` there,
  since the badge and the tree need different rules — border vs. text color
  — off the same class names).
- `enter` (via `Tree.NodeSelected`) on a `kind="file"` node in PDF mode:
  - Compute the `.pdf` path with `compile.notebook_path_for(node.data.path)`.
  - If it doesn't exist, compile it synchronously first
    (`compile.compile_file`) — per the "not expected, bug prevention" decision,
    this runs inline rather than through a background worker; it should be
    rare enough not to block the UI meaningfully, and doing it synchronously
    means `open` never races an in-flight compile.
  - `subprocess.run(["open", str(pdf_path)])`.
- `enter` on a `kind="dir"` node: expand/collapse only (`Tree`'s default
  behavior) — no file action.

## 5. MD mode + nvim + recompile

- `enter` on a `kind="file"` node in MD mode:
  - Capture the `.md` path's mtime (or `None` if the file somehow doesn't
    exist — shouldn't happen since the tree is built from `walk()`, which only
    lists files that exist).
  - `with self.app.suspend(): subprocess.run(["nvim", str(md_path)])` — `nvim`
    directly, not `vim`: the dev's shell alias from `vim` to `nvim` doesn't
    apply to a non-interactive `subprocess.run`.
  - After resuming, compare mtimes; if changed, recompile via the same
    worker-thread pattern `EntryScreen._autocompile_dirty_files`/`_compile_one`
    already use (reuse those functions directly from `entry.py`, or lift them
    to `compile.py` if reuse across two screens makes `entry.py` the wrong
    home — decide during implementation based on how it reads).
  - Surface compile failures the same way Entry screen does: `app.notify(...,
    severity="error")`.

## 6. Tests

- `tests/test_tui_inspect_tree.py` (new): tree construction from a fixture
  directory (mirrors `test_tui_entry_screen.py`'s fixture-tree setup), PDF-mode
  `enter` invoking `open` with the right path (mock `subprocess.run`), MD-mode
  `enter` invoking `app.suspend()` + `nvim` (mock both), mtime-change triggering a
  recompile call and no-change not triggering one, `tab` toggling mode and
  resetting to PDF on fresh screen construction, missing-PDF-compiles-first
  case.
- `tests/test_tui_main_menu.py`: update per Group 3.
- Full suite run at the end (`pytest`) to confirm no regressions in
  `test_tui_entry_screen.py` after the `FooterHint` migration.
