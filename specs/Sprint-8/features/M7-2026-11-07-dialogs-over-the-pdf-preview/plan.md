# M7 · Dialogs over the PDF preview — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The page under a dialog (§1)

- `tui/screens/inspect.py`: `on_screen_suspend` clears the image;
  `on_screen_resume` calls `_update_preview` with the tree's cursor node after
  the next refresh; `_show_preview_image` writes the image only when
  `self.app.screen is self`.
- `_rebuild_tree` and the redraw read the cursor by line, and a rename's or
  new file's compile refreshes the preview when it ends (§4).
- Update `PdfPreview`'s and `InspectTreeScreen`'s docstrings/comments where
  they list when the image is cleared.
- Tests 1–5 of §3.

## 2. Notifications on Inspect Tree (§2)

- `tui/app.tcss`: `InspectTreeScreen ToastHolder` aligned left, and the toast's
  width capped to the tree panel.
- Tests 6–7 of §3.

## 3. Specs and the real thing

- `design.md`, *Inspect Tree's PDF preview pane*: the page is hidden while a
  dialog is open and comes back when it closes; this screen's notifications
  are bottom-left, and why. *Implementation*: the suspend/resume hooks and the
  current-screen guard, next to the existing paragraph on clearing the image.
- Run the app in a kitty-graphics terminal: `n`, `r`, `m`, `d` over a shown
  page, escape and confirm, and a notification. Note what was seen in
  `validation.md` §2.
- `uv run --extra dev pytest` in full.
