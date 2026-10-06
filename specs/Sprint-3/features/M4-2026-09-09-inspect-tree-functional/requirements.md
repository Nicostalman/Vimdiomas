# Requirements — M4 · Inspect Tree, functional

Source: [`roadmap-sprint-3.md`](../../roadmap-sprint-3.md)'s M4 section, the
backlog's *Notebook menu: make Inspect Tree functional*
([`backlog.md`](../../guidelines/backlog.md)), and the spec interview held
2026-09-09.

## Anchor (from the roadmap)

**Deliverable.**

- The notebook menu's **Notebook** entry is removed. *Inspect tree* absorbs it.
- Inspect Tree opens a real tree — built on M3's `SupaTree` base, leaves are
  files — with two modes:
  - **PDF mode**, always the default on entry. Opening a file opens its PDF.
  - **MD mode**, reached with `tab`. Opening a file opens the `.md` in vim,
    inside the same terminal.
  - `tab` alternates between them. The mode is **not persistent**: leaving and
    re-entering always starts in PDF mode.
- Saving an `.md` with changes from vim triggers a recompile of that file.
- The screen obeys the navigation conventions in `design.md` like every other
  screen — `tab` is the only key this milestone adds.

**Done when.** *Inspect tree* opens the merged tree in PDF mode; `enter` on a
file opens its PDF; `tab` switches to MD mode and `enter` there opens vim in the
same terminal; quitting vim after a save leaves an up-to-date PDF with no visit
to *Compile*; leaving and re-entering starts in PDF mode again; and *Notebook*
is gone from the notebook menu.

## Decisions (settled in this milestone's interview, 2026-09-09)

| Decision | Rationale |
| --- | --- |
| Vim is hosted via Textual's `App.suspend()` | The roadmap's expected route; dev confirmed rather than exploring alternatives. |
| The editor launched is `nvim`, not `vim` | Dev's `.zshrc` alias (`vim` → `nvim`) doesn't take effect for a non-interactive `subprocess.run`, which doesn't source `.zshrc`. Rather than fight shell-alias resolution, the app calls `nvim` directly. Raised by the dev after manual testing (2026-09-09). |
| The tree's border color reflects the current mode: **red** in PDF mode, **blue** in MD mode | Raised by the dev after manual testing (2026-09-09) — the border showed the same accent color (orange) in both modes, giving no visual cue for which mode is active. Implemented as `.mode-pdf`/`.mode-md` CSS classes toggled on `InspectTree`, overriding `SupaTree`'s shared `$accent` border for this screen only. |
| `nvim` is added to `stack.md`'s Prerequisites table | Dev-requested, since MD mode now has a hard runtime dependency on it. |
| A mode badge (`"PDF MODE"` / `"MD MODE"`) sits above the tree, colored to match the border (red/blue) | Raised by the dev after manual testing (2026-09-09) — the border color alone wasn't a strong enough cue. |
| A PDF preview pane is **not** built this milestone | Raised by the dev after manual testing (2026-09-09), asking whether it was feasible. Not a quick add — needs a terminal graphics protocol (Kitty/iTerm2/sixel) or a library like `textual-image`, a PDF-to-image render step (Poppler's `pdftoppm`/`pdf2image`), and has no fallback on terminals without image support. Logged in `notes-sprint-3.md` as postponed to a future sprint's backlog, per the dev's agreement. |
| Opening a PDF hands it to the OS default viewer via the macOS `open` command | Same spirit as Sprint 2 M4's input-method switching: macOS-only for now, no configurable viewer. |
| A saved change is detected by **mtime comparison** — the `.md`'s mtime before suspending vim vs. after it exits | Simpler than a content hash, no extra dependency; dev's pick over exit-code (unreliable) and hashing (unneeded precision). |
| The tree has **one leaf per file-stem** (e.g. "Food"), not one leaf per physical file | `tree-Chinese/` is flat and holds `Food.md` + `Food.pdf` side by side, but the leaf represents the *file* conceptually — `enter` opens `Food.pdf` in PDF mode and `Food.md` in MD mode from the same leaf, rather than listing the two extensions as separate tree entries. |
| If PDF mode's `enter` targets a file whose `.pdf` doesn't exist yet, it is compiled on the spot (synchronously) before opening | Dev: "this situation is not expected — bug prevention, not intended functionality." Every `.md` is compiled by M1's merge and by autocompile-on-save elsewhere in the app; this only guards against a `.md` that reached the tree without ever being compiled. |
| A shared `FooterHint` widget is introduced (in `base.py`, alongside `SupaTree`/`MenuScreen`) and used by **both** Inspect Tree and Entry screen | Dev: "footer hints will be implemented in lots of places" — anticipating reuse beyond this milestone, same rationale as `SupaTree`'s "one place to change every tree." Entry screen's existing `Static(FOOTER_HINT, id="footer-hint")` is migrated onto it in this milestone rather than left to a later cleanup. This is a cross-cutting UI convention, so it is also recorded in `design.md`. |

## Scope

- New screen: Inspect Tree, reached from the notebook menu, built on `SupaTree`
  with file leaves (not category leaves, unlike `EntryTree`).
- The notebook menu's **Notebook** entry (`main_menu.py`'s `_notebook` handler
  and its `Option("Notebook", id="notebook")`) is deleted outright.
- `tab` toggles PDF/MD mode; mode resets to PDF on every fresh entry into the
  screen (no persistence across visits).
- `enter` in PDF mode: `open <path>.pdf` (compiling first if missing, per the
  Decisions table).
- `enter` in MD mode: suspend the app, run `$EDITOR`-independent `vim <path>.md`
  in the same terminal (vim is assumed to be on `PATH`, per the sprint's
  existing Assumptions), resume the app, recompile if the mtime changed.
- New shared `FooterHint` widget in `base.py`; both `EntryScreen` and the new
  Inspect Tree screen use it.
- `design.md` gains: the `FooterHint` convention, and the removal of the
  "Notebook" menu entry is *not* a design convention change (it's this
  milestone's own scope), so nothing else in `design.md`'s navigation table
  changes.

## Out of scope (deferred to M5 or later)

- `d`/`e`/`n`/`m` keybindings for delete/rename/create — M5.
- The `y`/`n` confirmation shape mentioned in M5 — not needed here since M4 adds
  no destructive action.
- Multi-language support, non-macOS PDF viewers, non-vim editors — standing
  sprint-level exclusions already recorded in `notes-sprint-3.md`.
