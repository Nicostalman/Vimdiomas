# M7 · Dialogs over the PDF preview — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M7 · Dialogs
over the PDF preview*:

> **Deliverable.**
>
> - While any screen is open over Inspect Tree (its four dialogs, or anything
>   else pushed on top), the page is not drawn. It is cleared when the screen
>   opens and redrawn when it closes, for whatever the tree's cursor is on
>   then. A render that finishes, or a resize that happens, while a dialog is
>   open does not draw the page. The redraw happens when the dialog closes.
> - On Inspect Tree, notifications are shown bottom-left, over the tree panel,
>   which never shows an image. They never reach into the preview panel.
> - `design.md` states both rules in *Inspect Tree's PDF preview pane*.
>
> **Done when.** In a terminal that shows the page (kitty graphics), with a
> file's page in the preview: `n`, `r`, `m` and `d` each open a dialog that is
> fully visible, with no part of the page over it. Escape and confirm both
> bring the page back. *Deleted … Press u to undo.* and an error notification
> (`n` with an existing name) are fully visible at the bottom left. MD mode,
> the text preview and leaving the screen behave as before. The full test
> suite passes.

The source is the dev's screenshot of 2026-11-07: Inspect Tree, PDF mode, the
cursor on *Vocabulary › Posición*, and the *New directory* dialog with its
right half under the rendered page. There is no backlog entry. The notes
([`../../guidelines/notes-sprint-8.md`](../../guidelines/notes-sprint-8.md),
*M7 added from a screenshot*) record why it joins Sprint 8.

**The bug in one line.** `PdfPreview.show_image` writes a kitty graphics
escape straight to the terminal (Sprint 5 M4). The terminal puts that image on
a layer above all text, so Textual cannot paint over it. The image is deleted
only in `_show_preview_message`, `action_back_or_quit` and `on_unmount`, so
when `ConfirmDialog` or `PromptDialog` is pushed over the screen, the page
stays on top of it.

## Decisions

Settled with the dev on 2026-11-07.

| Decision | Rationale |
| --- | --- |
| **The page is hidden while any screen is over Inspect Tree, and redrawn when it closes** | The dev's choice, over keeping the page visible and cropping out the dialog's rectangle. Cropping would mean re-rasterising for every dialog size and position, and doing it again on resize. A dialog is short-lived, and the page comes straight back from `RasterCache`. |
| **The rule is about any screen pushed on top, not the four dialogs by name** | Hooked on Textual's `ScreenSuspend` / `ScreenResume`, which fire for any screen pushed over this one. A dialog added later, or Textual's own command palette, is covered without changes here. |
| **On Inspect Tree, notifications move to the bottom-left** | The dev's choice, over clearing the page while a toast shows (the page would flicker after every action) and over leaving toasts out of scope. The tree panel never shows an image. This is the one screen whose notifications are not at the bottom-right, and `design.md` says so. |
| **The kitty z-index (drawing the page below text) is not used** | A negative z-index only goes under cell backgrounds below −2³⁰, and then the preview's own cells would need the terminal's default background for the page to show at all. Support differs across Ghostty, WezTerm and kitty. Clearing and redrawing works the same in all three. |

## 1. The page while a screen is on top

### 1.1 Cleared when a screen opens

`InspectTreeScreen` handles `events.ScreenSuspend` by calling
`PdfPreview.clear_image()` (the existing delete-all-placements escape). It
changes nothing else: `#preview-image` stays displayed and `_preview_data`
stays as it is. The pane is blank (dimmed under the dialog's backdrop) until
the screen comes back.

This applies to:

- `d` → `ConfirmDialog` (*Delete X?*)
- `r` → `PromptDialog("New name:", …)`
- `n` → `PromptDialog("New directory name:")`
- `m` → `PromptDialog("New file name:")`
- any other screen pushed while Inspect Tree is the current screen.

### 1.2 Nothing is drawn while it is not the current screen

`_show_preview_image` still sets the displays (message hidden, image shown),
but it writes the image only if `self.app.screen is self` (not
`Screen.is_current`, see §4). This covers:

- a rasterise worker that was already running when the dialog opened, and
  finishes while it is open;
- `on_resize` while a dialog is open, which calls `_update_preview` and
  starts a new rasterise;
- a dialog callback that rebuilds the tree, if Textual has not yet made
  Inspect Tree current again when it runs.

Message states (`_show_preview_message`) are ordinary Textual text and are
left alone. The dialog covers them correctly already.

### 1.3 Redrawn when the screen comes back

`InspectTreeScreen` handles `events.ScreenResume` by calling
`self._update_preview` with the tree's cursor node, after the next refresh
(see §4). This uses the cursor's node at that moment, so:

- **Escape** (cancel) brings back the same page.
- **Confirm** brings back the page for wherever the dialog's callback left the
  cursor. After a rename, new directory or new file, `_rebuild_tree` has
  already moved it. After a delete, it is on the next node.
- The page is rasterised again only if the pane's size changed (a resize while
  the dialog was open). Otherwise `RasterCache` returns it straight away.

`ScreenResume` also fires when Inspect Tree first becomes current. The redraw
is harmless there: `on_mount`'s `call_after_refresh` already does the same.
If it turns out to draw twice visibly, the resume handler skips the first
resume. Record which one happened in §4.

### 1.4 Unchanged

- Leaving the screen (`q`, escape out of the backpanel) still clears the page
  first (`action_back_or_quit`, `on_unmount`).
- MD mode, a terminal without kitty graphics (the `pdftotext` text), and the
  four message states: no image, so nothing to clear.
- `enter` in MD mode suspends the whole app for nvim. There is no image in MD
  mode, so it is not affected.

## 2. Notifications on Inspect Tree

### 2.1 Bottom-left, inside the tree panel

In `app.tcss`, scoped to `InspectTreeScreen`, the toast holder is aligned
left (`InspectTreeScreen ToastHolder { align-horizontal: left; }`, beside the
default `ToastRack` rules). The toast's width is capped so that its right
edge never goes past `#inspect-panel`'s right edge at any terminal width. The
cap is whatever CSS does that (a `max-width` on `InspectTreeScreen Toast`, or
a margin on the rack). The test in §3 checks the regions, not the CSS.

Toasts keep their own look, duration, stacking and severity colours.

### 2.2 Which notifications

Every notification shown while Inspect Tree is the current screen. Among
them: *Deleted X. Press u to undo.*, *Restored X.*, *Nothing to delete here.*,
*X already exists.*, the name-validation errors, the OS-error reports, the
compile failures from `autocompile_one`, the `nvim` warning, and M4's
*could not be read* warnings.

Not affected:

- A notification raised while a dialog is current goes to the dialog's screen
  (Textual's behaviour) and shows bottom-right over the dimmed, now blank,
  preview pane. None of the four dialogs notifies today.
- *changed since it was deleted — left alone.* is raised from `on_unmount`,
  so it shows on the screen underneath, at that screen's usual bottom-right.

## 3. Tests

In `tests/test_tui_inspect_tree.py`, using the existing pattern of wrapping
`pilot.app._driver.write` to record escapes (as in
`test_q_clears_any_kitty_image_before_leaving`). Where an image has to be
shown, `supports_kitty_graphics` and `pdftoppm_available` are patched to
`True` and the rasteriser is stubbed to return a small PNG, so no poppler is
needed.

1. **Each dialog clears the page.** For `d`, `r`, `n`, `m`: with a page
   shown, pressing the key writes a delete escape (`\x1b_Ga=d`) before or
   while the dialog is the current screen.
2. **Escape brings it back.** After escape from a `PromptDialog`, a new image
   escape (`\x1b_G` with `a=T`, whatever `render_kitty_image` emits) is
   written for the same file.
3. **Confirm brings it back for the new cursor.** `n` with a fresh name: the
   tree is rebuilt, and an image escape is written after the dialog closes,
   for the cursor's node.
4. **No image while a dialog is open.** With a dialog open, a resize (or
   calling `_show_preview_image` directly) writes no image escape. The next
   `ScreenResume` does.
5. **MD mode writes nothing.** `n` in MD mode writes no image escape on open
   or close.
6. **Toasts sit in the tree panel.** On Inspect Tree, after a notification
   (`d` on the root → *Nothing to delete here.*), the toast's region lies
   inside the screen's left half, with `toast.region.right <=
   #inspect-panel.region.right`, at two terminal sizes (e.g. 100×30 and
   200×50).
7. **Other screens are unchanged.** A notification on another screen (e.g.
   Browse) is still at the bottom-right.

The existing tests pass unchanged.

## 4. Found during implementation

- **`Screen.is_current` can't be the guard (2026-11-09).** Textual counts a
  screen as current when it is in `app._background_screens`, which is any
  screen still visible behind a translucent one. `ModalScreen` is translucent,
  so Inspect Tree stays `is_current` under its own dialogs. §1.2 checks
  `self.app.screen is self` instead.
- **The redraw waits for a refresh (2026-11-09).** A subclass's handler runs
  before `Screen._on_screen_resume`, which is what applies a resize that
  happened while the dialog was open. Redrawing straight from the handler would
  read the pane's old size, so it goes through `call_after_refresh`, as
  `on_mount`'s redraw does.
- **The cursor is read by line, not from `cursor_node` or `_preview_data`
  (2026-11-09).** A rename calls `_rebuild_tree()` with no path to select, so
  the cursor stays on the same line and no new node is highlighted. After the
  rebuild, `Tree.cursor_node` is still the old node until the tree next lays
  itself out, so the preview looked for the file under its old name and the
  renamed file's page didn't come back. `_rebuild_tree` and the redraw both ask
  `tree.get_node_at_line(tree.cursor_line)` now. The test in §3 (confirm) caught
  it.

- **A rename or new file refreshes the preview when its compile ends
  (2026-11-09).** Both compile in a worker, and a rename deletes the old PDF
  first, so at the moment the dialog closes there is no PDF and the pane says
  *No compiled PDF for this file.* Left alone, confirm would not bring the page
  back (§1.3) until the cursor moved. `_compile_and_refresh` redraws for the
  cursor's node once the compile is done, unless the screen has been left or a
  dialog is open. MD mode's recompile after nvim is unchanged.

- **The first `ScreenResume` is left alone (2026-11-09).** It adds one more
  redraw when the screen opens, next to `on_mount`'s. A trace showed the page
  written once, so the skip §1.3 allowed for wasn't needed.

## Out of scope

- **Keeping the page visible beside the dialog** (cropping): rejected above.
- **Moving notifications on any other screen.** None of them shows an image.
- **The four dialogs' own look and wording.** Unchanged.
- **Multi-page preview**, still in the Postponed table.
