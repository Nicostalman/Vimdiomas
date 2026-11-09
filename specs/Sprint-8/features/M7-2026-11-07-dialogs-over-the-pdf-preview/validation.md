# M7 · Dialogs over the PDF preview — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [x] `uv run --extra dev pytest` passes in full.
- [x] §3's tests 1–7 exist and pass: each of `d`/`r`/`n`/`m` writes a delete
      escape when it opens; escape and confirm each write an image escape
      after the dialog closes; nothing is drawn while a dialog is open, a
      resize included; MD mode writes no image; Inspect Tree's toasts sit
      inside `#inspect-panel` at two terminal sizes; another screen's toasts
      are still bottom-right.
- [x] `test_q_clears_any_kitty_image_before_leaving` and the rest of
      `tests/test_tui_inspect_tree.py` pass unchanged.

## 2. By the agent, in the real app

In a terminal with kitty graphics, on a tree whose file has a compiled PDF:

- [ ] `n`: the *New directory* dialog is fully visible, with the pane blank
      behind it. Escape: the page comes back.
- [ ] `r`, `m`, `d`: the same.
- [ ] `n` with a new name: the directory appears and the page comes back for
      the cursor's node.
- [ ] Resize the window with a dialog open: no page over the dialog. Close
      it: the page is back at the new size.
- [ ] `d` → `y` on a file: *Deleted … Press u to undo.* is fully visible at
      the bottom-left. `n` with an existing name: the error is fully visible
      there too.

## 3. By hand (the dev)

- [ ] The screenshot's case: Inspect Tree, PDF mode, cursor on *Posición*,
      `n`. The dialog is whole, with no page over it.
- [ ] `r`, `m`, `d` over a shown page; escape and confirm each bring the page
      back.
- [ ] Delete then `u`: both notifications readable, bottom-left.
- [ ] MD mode and leaving the screen look as they did before.

Merged on the dev's word on 2026-11-09. The agent had no terminal that shows
the page, so §2 was not run by the agent, and §2 and §3 are left unticked here
rather than assumed.

## 4. Spec check

- [x] `requirements.md`, `plan.md`, `design.md` and the code agree; anything
      that changed during implementation is recorded in `requirements.md` §4.
