# M5 · Editing the tree from inside the app — plan

## 1. Modal dialog family (`base.py`)

- Add `ConfirmDialog(ModalScreen[bool])`: takes a message string; renders it
  centered with `y` → confirm, `n`/`escape` → cancel. **`enter` is
  deliberately unbound** — dev's explicit correction after manual testing,
  so a destructive action can never be confirmed by accident. Dismisses with
  `True`/`False`.
- Add `PromptDialog(ModalScreen[str | None])`: takes a label string and an
  optional pre-filled value; renders the label above a plain `Input` — not
  `PanelAwareInput`, whose `escape` binding dispatches to
  `screen.defocus_panel`, an action only `NavigableScreen` implements; inside
  this modal it would shadow the dialog's own `escape`-to-cancel binding.
  `enter` dismisses with the input's current text (`""` submits as cancel,
  handled by the caller — see Decisions), `escape` dismisses with `None`
  (also cancel).
- Both share a `.dialog` CSS class/base styling in `app.tcss`: small, centered,
  bordered box, with its `Static` content **center-aligned** (`text-align:
  center`) — the dev flagged the first pass as not centered enough on manual
  testing, traced to the text sitting left-aligned inside an already-centered
  box. `ModalScreen`'s own darkened backdrop is used as-is.
- Push with `self.app.push_screen(dialog, callback)` — Textual's callback-based
  modal-result pattern; `InspectTreeScreen`'s action methods below all follow
  this shape rather than blocking/awaiting.

## 2. `NodeData` gains a path for directories

- `NodeData(kind="dir", path=...)` — set on every directory node,
  including the root (`tree.root.data = NodeData(kind="dir", path=self.tree_root)`
  in `InspectTreeScreen.on_mount`, and in `_add_dir_children` for each
  child directory node, mirroring what file leaves already do).
- No change to `store.py`/`DirNode` — the path is already available at
  tree-build time (`dir_node.path`), just wasn't being threaded through.

## 3. Resolving "the target" from the cursor

Add one small helper on `InspectTreeScreen` (or a free function in
`inspect.py`) that, given the currently-selected `TreeNode[NodeData]`, returns:

- the node's own path and kind, for `d`/`r`.
- the *directory* path to create into, for `m`: the node's own path if it's a
  dir, else `path.parent` if it's a file.
- for `n`, no resolution needed — always `self.tree_root`.

Selection is read from `tree.cursor_node` (the currently highlighted node),
matching how `d`/`r`/`n`/`m` are framed as acting on "the file or directory
under the cursor."

## 4. `d` — delete (soft, undoable until the screen is left)

Delete does **not** touch the filesystem immediately. Dev's explicit request
after manual testing: within one visit to Inspect Tree, a delete only hides
the target from the tree and is undoable with `u`; the real removal happens
once the screen closes.

- `InspectTreeScreen.__init__` gains `self._pending_deletes: list[NodeData] = []`
  — an ordered stack of confirmed-but-not-yet-committed deletes, screen-local
  (a fresh screen always starts with none pending, same "not persistent"
  spirit as the PDF/MD mode reset).
- `action_delete`: resolve the cursor target. If it's the root node, notify
  and return (see Decisions).
- Build the confirmation message:
  - File: `Delete Food.md?` (using the `.md` name; a file leaf represents both
    halves of the pair).
  - Directory: count files under it (`sum(1 for _ in path.rglob("*.md"))`, or
    similar) and phrase `Delete Grammar/ and its 3 files?` (singular/plural).
- Push `ConfirmDialog`; the callback, on `True`: append the `NodeData` to
  `self._pending_deletes`, rebuild the tree (§6, which now hides it), and
  `app.notify` mentioning `u` to undo. On `False`/dismiss: no-op.
- `action_undo` (bound to `u`): if `self._pending_deletes` is empty, notify
  "nothing to undo" and return; otherwise `.pop()` the most recent entry and
  rebuild the tree (so it reappears) — a single-level undo stack, no redo.
- `InspectTreeScreen.on_unmount`: for every entry left in
  `self._pending_deletes`, perform the real removal (file: unlink the `.md`
  and, if present, its `.pdf`; directory: `shutil.rmtree`), then clear the
  list. This is what makes a delete permanent — it fires whenever the screen
  leaves the stack, regardless of how (the `q` binding, or any other pop),
  so there's no need to override `action_back_or_quit` separately.

## 5. `r` — rename (formerly `e`)

Keybinding renamed from `e` to `r` at the dev's request. Also fixes a gap
found in manual testing: renaming didn't update the `.md`'s own `# Title`
header line, and — because `compile.py`'s `parse()` sets `deck.title` from
the **filename**, not from that header line — a renamed-but-not-recompiled
`.pdf` kept showing its old title. Renaming a file must now retitle and
recompile, not just move bytes.

- `action_rename`: resolve the cursor target; root → notify and return.
- Push `PromptDialog` pre-filled with the current stem (file) or directory
  name (dir).
- Callback: `""`/`None` → cancel, no-op. Otherwise:
  - Duplicate check first: for a file, does `parent / f"{new_name}.md"` or
    `parent / f"{new_name}.pdf"` already exist? For a directory, does
    `tree_root / new_name` already exist (directories are always top-level —
    see §3)? If so, `app.notify(..., severity="error")` and stop. (This also
    naturally refuses a name that collides with a *pending-deleted* file,
    since it's still physically present until the screen is left.)
  - Directory: `path.rename(path.parent / new_name)` — unchanged, no header
    concept for a directory.
  - File:
    1. Note whether a `.pdf` exists (`old_pdf = notebook_path_for(path)`,
       `had_pdf = old_pdf.exists()`) before touching anything.
    2. Read the `.md`, replace its `# <old-title>` header line with
       `# <new_name>` (a small `_retitle(text, new_title)` helper mirroring
       `parser.py`'s own header-line detection: the first line starting with
       `# ` but not `## `), write it back.
    3. `path.rename(parent / f"{new_name}.md")`.
    4. If `had_pdf`: delete the old `.pdf` (its content is now stale) and
       schedule a recompile of the new `.md` → new `.pdf` via the same
       `app.run_worker(..., thread=True, group="autocompile")` pattern used
       elsewhere in this file, rather than renaming the old `.pdf`'s bytes.
       If there was no `.pdf`, nothing further happens — unchanged from the
       original decision.
  - Rebuild the tree (§6).

## 6. `n` — create directory

- `action_new_dir`: always targets `self.tree_root`, cursor position ignored.
- Push `PromptDialog` (empty, no pre-fill).
- Callback: `""`/`None` → cancel. Otherwise duplicate-check
  `tree_root / name`; if taken, notify and stop; else `Path.mkdir()` and
  rebuild the tree.

## 7. `m` — create file

- `action_new_file`: resolve the target *directory* via §3's helper.
- Push `PromptDialog` (empty, no pre-fill).
- Callback: `""`/`None` → cancel. Otherwise duplicate-check
  `target_dir / f"{name}.md"` (and `.pdf`, in case a stray `.pdf` exists
  without its `.md`); if taken, notify and stop.
- Else: write `target_dir / f"{name}.md"` with content `f"# {name}\n"`, then
  compile it immediately (reuse `_compile_one` via the same
  `app.run_worker(..., thread=True, group="autocompile")` pattern M4 already
  uses for post-save recompiles — creation is not latency-sensitive enough to
  need special-casing to a synchronous call).
- Rebuild the tree (§6 below, shared helper).

## 8. Shared tree-rebuild helper

- Factor the `build_tree(tree, walk(self.tree_root)); tree.focus()` sequence
  currently inline in `on_mount` into a small `self._rebuild_tree()` method,
  called from `on_mount` and from every mutating action's callback once its
  filesystem change is done.
- `_rebuild_tree` prunes anything in `self._pending_deletes` out of the
  `DirNode` tree before building — a small `_prune(dir_node, hidden_paths)`
  free function that drops any dir/file whose path is in the hidden set
  (dropping a directory drops everything under it too, without needing to
  list each descendant separately).

## 9. Bindings

- `InspectTreeScreen.BINDINGS`: `d` → `delete`, `r` → `rename`,
  `n` → `new_dir`, `m` → `new_file`, `u` → `undo`. All `show=False`,
  consistent with the existing `tab` binding.
- Extend `FOOTER_HINT_PDF`/`FOOTER_HINT_MD` to mention all five keys (short
  form, e.g. append `· d/r/n/m: delete/rename/new dir/new file · u: undo
  delete`).

## 10. `design.md`

- Add a new bullet to the Implementation list documenting `ConfirmDialog`/
  `PromptDialog` as the app's standing yes/no and text-prompt convention —
  centered, center-aligned text, `ConfirmDialog`'s `enter` deliberately
  unbound — alongside the existing `SupaTree`/`FooterHint`/`MenuScreen`
  entries.

## 11. Tests

- `tests/test_tui_inspect_tree.py` gains cases for: delete file (confirm
  hides it without touching disk, cancel keeps it visible), confirming then
  leaving the screen commits the removal to disk, `u` restores a pending
  delete (and leaving afterward leaves the files untouched), undo with
  nothing pending just notifies, delete on a non-empty directory (hides
  everything under it, commits on exit), `enter` on the confirm dialog does
  nothing, rename file (with and without an existing `.pdf`, asserting the
  recompile call and the new `.md`'s rewritten header), rename directory,
  duplicate-name refusal for `r`/`n`/`m`, `n` always targeting the root
  regardless of cursor, `m` targeting the cursor's directory vs. a file's
  parent directory, `m`'s immediate-compile behavior, and `d`/`r` no-op on
  the root node.
- Existing tests in that file are expected to keep passing, with `e`
  keypresses in the pre-existing rename tests updated to `r`.
