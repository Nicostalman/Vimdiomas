# M5 · Editing the tree from inside the app — requirements

## Roadmap anchor

From [`../../roadmap-sprint-3.md`](../../roadmap-sprint-3.md):

> Five keys on the Inspect Tree screen: `d` delete (with a y/n confirmation,
> `enter` does nothing there), `r` rename (prompts for a new name, pre-filled),
> `n` create a directory (always at the top level), `m` create a file (in the
> directory under the cursor), `u` undo the most recent pending delete.
> Deleting is aesthetic until the screen is left, at which point it commits
> for real. Deleting or renaming an `.md` must keep its `.pdf` — and its
> title — consistent. The y/n confirmation and the name prompt are one
> reusable, centered modal-dialog family, recorded in `design.md`.
>
> Done when a directory and a file can be created, renamed and deleted end to
> end from Inspect Tree without leaving the app; `d` never destroys anything
> without a `y`, and `enter` never accidentally does; a pending delete can be
> undone with `u` before the screen is left, and is permanent after; deleting
> or renaming an `.md` leaves no orphaned, misnamed, or mistitled `.pdf`; and
> `n` refuses to nest.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*"Notebook menu: further functionality for inspect tree"*.

## Scope

In scope:

- Five new bindings on `InspectTreeScreen`: `d`, `r`, `n`, `m`, `u`. Active in
  both PDF and MD mode — editing the tree's structure is orthogonal to which
  mode a file opens in.
- A reusable modal-dialog family (`ConfirmDialog` for y/n, `PromptDialog` for a
  single text field), added to `tui/screens/base.py` alongside the existing
  `SupaTree`/`FooterHint`/`MenuScreen` shared widgets, both centered and
  documented in `design.md` as a standing convention — not just for this
  milestone.
- Filesystem operations (delete/rename/create) act directly on the tree's
  files and directories under `tree_root`, keeping `.md`/`.pdf` pairs — and a
  renamed file's `# Title` header — consistent.
- Delete is a **soft delete** for the lifetime of the screen: hidden from the
  tree immediately, reversible with `u`, and only committed to disk
  (`shutil.rmtree`/`unlink`) when the screen is unmounted.
- The tree view refreshes (full rebuild from `walk()`, minus anything pending
  deletion) after every mutating operation.

Out of scope (deferred, unscheduled unless noted):

- Nested directories. `n` always creates at the top level; the app does not
  guard against a directory the dev creates by hand in the filesystem going
  deeper (see `notes-sprint-3.md`'s existing assumption).
- Undo for rename/create — only delete is undoable, and only until the screen
  is left.
- Multi-step undo history beyond a simple stack of pending deletes (no redo).
- Preserving tree cursor/scroll position precisely across a rebuild — best
  effort only, not a requirement.
- Multi-select / bulk delete.
- A per-screen title banner ("what window is this") — raised by the dev during
  this milestone's manual testing but not part of it; see
  `notes-sprint-3.md`'s Postponed table.

## Decisions

Settled during this milestone's spec interview (2026-09-09) and refined after
a first round of manual testing (2026-09-10):

| Decision | Rationale |
| --- | --- |
| The y/n confirmation and the name prompt are both **modal dialogs**, one small reusable family (`ConfirmDialog`, `PromptDialog`), and both are **centered** with center-aligned text | Dev's choice over an inline footer/input swap. The dev flagged the first pass as not visually centered enough during manual testing — fixed by centering the dialog's text content (`text-align: center` on `.dialog Static`) in addition to the box's own screen-centered position. |
| `ConfirmDialog`'s `enter` is **unbound** — only `y` confirms, `n`/`escape` cancel | Dev's explicit correction after manual testing: `enter` must never double as "yes" on a destructive confirmation. |
| `d` on a **non-empty directory** deletes it and everything inside it, after one confirmation naming what's being removed (e.g. "Delete Grammar/ and its 3 files?") | Dev's choice over refusing on non-empty directories. A single clear prompt is enough; no need for a second "it's not empty" gate. |
| **Delete is aesthetic, not immediate** — confirming `d` hides the file/directory from the tree and pushes it onto a per-screen undo stack, but leaves it on disk; `u` pops the stack and restores it to the tree; the real `shutil.rmtree`/`unlink` only happens in `on_unmount`, once the dev leaves Inspect Tree | Dev's explicit request after manual testing, with the undo keybinding (`u`) added to the legend. Changes the earlier "delete is immediate" decision from the spec interview — recorded here as the current, superseding decision rather than editing the interview record away. |
| `m` prompts for a **name**; an empty submission cancels; a non-empty name creates `<name>.md` whose first line is `# <name>` (matching the header-must-match-filename convention `parser.py` already enforces), and the file is **compiled immediately** on creation — not deferred to vim's exit | Dev's explicit answer. Differs from the "detect a save in vim" recompile path already built for M4: a freshly created file has content the moment it's named, so there's no need to wait for a vim session. |
| `r` (rename, formerly bound to `e`) on a file renames **whichever of `.md`/`.pdf` exist** for that stem, **rewrites the `.md`'s `# Title` header line to the new name**, and **recompiles the `.pdf`** if one existed (deleting the stale one first rather than just renaming its bytes) | Dev caught in manual testing that neither the `.md` header nor the `.pdf`'s embedded title changed on rename — `compile.py`'s `parse()` sets `deck.title` from the *filename* at compile time, so a renamed-but-not-recompiled `.pdf` keeps showing the old title. A missing `.pdf` (never compiled) is still just skipped, not created, unchanged from the original decision. |
| Rename's keybinding is **`r`, not `e`** | Dev's explicit request; `e` is no longer bound to anything on this screen. |
| A **duplicate name** on `r`/`n`/`m` refuses the operation with a notification; nothing is overwritten | Dev's choice over silent overwrite — matches the app's existing pattern of surfacing failures via `app.notify` (see `inspect.py`'s compile-failure path) rather than destructive silent behavior. A name that collides with a *pending-deleted* file (still physically present until the screen is left) is refused the same way. |
| An empty submission on `r` (rename) **cancels**, same rule as `m` | Dev confirmed this explicitly, for consistency across all three prompts (`r`/`n`/`m`). |
| `r`'s prompt is **pre-filled with the current stem** (for a file) or name (for a directory), so the dev edits rather than retypes | Agent decision, not raised as an open question — a small usability default consistent with "leave it as-is and submit empty to cancel" still working (clear the field, then submit). |
| `n` and `m` operate on the **stem only** — the prompt never asks for or accepts an extension. `n` always targets `tree_root` regardless of cursor position; `m` targets the directory under the cursor, or that file's parent directory if the cursor is on a file | Directly from the roadmap's own wording. |
| `d`/`r` on the **tree's root node** are no-ops (a notification explains why) | Agent decision — the root *is* `tree_root`; deleting or renaming it isn't a meaningful "file or directory under the cursor" operation and isn't mentioned by the roadmap or backlog. |
| The tree **rebuilds fully** (`walk()`, pruned of anything pending deletion, then `build_tree`) after every mutating operation, rather than patching the `Tree` widget's nodes in place | Simplicity — `InspectTree` already discards and rebuilds on mount; every directory is auto-expanded on build (`_add_dir_children`'s `expand=True`), so there's no meaningful expand/collapse state to lose on rebuild. Cursor position is not preserved precisely (see Out of scope). |
| `NodeData` for **directory nodes now carries a `path`** (previously `None` for every dir, including root) | Needed so "the directory under the cursor" and "always at `tree_root`" can resolve a real filesystem path for `n`/`m`/`d`/`r` — this was dead weight until now, harmless to fill in. |
| `PromptDialog` uses a **plain `Input`**, not `PanelAwareInput` | `PanelAwareInput`'s `escape` binding dispatches to `screen.defocus_panel`, an action only `NavigableScreen` implements — inside this modal it would shadow the dialog's own `escape`-to-cancel. |

## Context

- Builds on M3's `SupaTree` and M4's `InspectTree`/`InspectTreeScreen`
  (`src/idiomas/tui/screens/inspect.py`), and reuses `compile.py`'s
  `compile_file`/`notebook_path_for` (suffix-swap `.md` ↔ `.pdf`) already used
  by M4's enter/save-triggered recompile.
- `store.py`'s `walk()` only collects `.md` files into `DirNode.files` — a
  `.pdf` with no matching `.md` is invisible to the tree already (unchanged by
  this milestone).
- `compile.py`'s `parse()` sets `Deck(title=filename_stem)` — the PDF's title
  always comes from the filename at compile time, never from the `.md`'s own
  `# Title` line. This is why a rename that doesn't also rewrite the header
  and recompile leaves a stale title behind.
- `design.md`'s navigation table is unaffected — `d`/`r`/`n`/`m`/`u` are new,
  screen-local bindings, not changes to the shared key map. The new dialog
  family, however, **is** a cross-cutting convention and gets its own entry in
  `design.md`, per the roadmap's explicit instruction.
