# M5 · Editing the tree from inside the app — validation

Grounded in the roadmap's done-when: *"A directory and a file can be created,
renamed and deleted end to end from Inspect Tree without leaving the app; `d`
never destroys anything without a `y`, and `enter` never accidentally does; a
pending delete can be undone with `u` before the screen is left, and is
permanent after; deleting or renaming an `.md` leaves no orphaned, misnamed,
or mistitled `.pdf`; and `n` refuses to nest."*

## Automated

- `pytest tests/test_tui_inspect_tree.py` — all M4 cases still pass unchanged
  (with `e` keypresses in the original rename tests updated to `r`), plus the
  M5 cases from plan.md §11:
  - Delete a file: confirming hides it from the tree but leaves both `.md`
    and `.pdf` on disk; dismissing (`n`/escape) leaves it visible and
    untouched.
  - Confirming a delete, then leaving the screen (popping it), commits the
    removal — both halves are gone from disk only at that point.
  - `u` restores the most recently hidden delete to the tree; leaving the
    screen afterward leaves its files untouched (the undo took effect before
    commit).
  - `u` with nothing pending notifies and changes nothing.
  - Delete a non-empty directory: confirming hides the directory and
    everything under it from the tree (still present on disk); leaving the
    screen removes it all; the confirmation message names the file count.
  - `enter` on the confirm dialog does nothing — the dialog stays open, the
    target stays visible and undeleted.
  - Rename a file that has a `.pdf`: both are renamed to the new stem, the
    `.md`'s header line is rewritten to the new name, and the `.pdf` is
    recompiled against the new content (assert the `compile_file` call).
  - Rename a file with no `.pdf` (never compiled): only the `.md` is renamed,
    its header is still rewritten, no `.pdf` appears.
  - Rename a directory: the directory itself is renamed, contents untouched.
  - `r`/`n`/`m` each refuse a duplicate name with a notification and change
    nothing on disk.
  - Empty submission on `r`/`n`/`m` cancels — no filesystem change.
  - `n` creates at `tree_root` regardless of which node the cursor is on.
  - `m` creates in the cursor's directory, or in a file's parent directory
    when the cursor is on a file.
  - `m` writes `# <name>` as the new file's first line and triggers a compile
    immediately (assert the compile call, mirroring how M4's tests assert
    `compile_calls`).
  - `d`/`r` on the tree's root node are no-ops (no dialog pushed, or dialog
    pushed but nothing changes — whichever the implementation does; assert no
    filesystem change and a notification).
- `pytest` (full suite) — no regressions elsewhere.
- No `ruff`/type-check config exists in this project (`pyproject.toml` has
  none, no pre-commit config) — nothing to run there.

## Manual (dev, on the real `tree-Chinese/`)

Since this milestone touches real files for the first time from inside the
app (not just reading them), validate against a throwaway copy or the dev's
own tree with care:

1. Open Inspect Tree. Press `n`, type a name, confirm a new top-level
   directory appears.
2. Press `n` again, submit empty — nothing is created.
3. Stand on the new directory, press `m`, name a file — a `.md` appears with
   a `# <name>` header, and its `.pdf` exists immediately (no trip to
   Compile).
4. Stand on a file inside a different directory, press `m` — the new file
   lands beside it, not at the top level.
5. Press `r` on a file, change its name — both `.md` and `.pdf` are renamed;
   opening the new `.pdf` shows the *new* title, not the old one; the tree
   reflects the new name without leaving the screen.
6. Press `r` on a file with no compiled `.pdf` yet — only the `.md` renames,
   its header updates too, no crash, no stray `.pdf`.
7. Press `d` on a file, answer `n` — nothing happens. Press `d` again, answer
   `y` — the file disappears from the tree. Confirm on disk (outside the app)
   that it's still there.
8. Press `u` — the file reappears in the tree. Leave the screen (`q`) and
   confirm it's genuinely still on disk.
9. Delete the same file again, this time leave the screen (`q`) without
   undoing — confirm both `.md` and `.pdf` are now actually gone from disk.
10. Press `d` on a directory with files in it, confirm the message states how
    many files, answer `y` — it disappears from the tree; leave the screen
    and confirm it's gone from disk too.
11. While a delete is pending (before leaving the screen), press `enter` on
    the confirm dialog for a *different* delete — confirm it does nothing;
    only `y` confirms.
12. Try `r`/`n`/`m` with a name that collides with an existing file/directory
    — refused, with a visible notification, nothing overwritten.
13. Confirm the delete-confirmation and rename/create-name dialogs both
    appear centered on screen, with centered text inside the box.
14. Confirm all five keys (`d`/`r`/`n`/`m`/`u`) work identically in both PDF
    mode and MD mode (`tab` to switch, retry a create/rename/delete/undo in
    the other mode).
15. Confirm `d`/`r` on the tree's root do nothing destructive.

**Done when the dev has run through the manual list above against real
content and is satisfied** — this milestone, like the others in this sprint,
closes on the dev's own testing, not on the automated suite passing alone.
