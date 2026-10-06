# M4 · PDF preview pane — validation

Grounded in the roadmap's done-when condition, made concrete.

## Automated

- `pytest` — full suite passes, including new tests from `plan.md` groups
  1–4:
  - `idiomas/terminal.py`: known `TERM_PROGRAM`/`TERM` values detected
    correctly; unknown/unset returns `False`.
  - `idiomas/pdf_preview.py` (marked `integration`, needs real `pdftoppm`/
    `pdftotext` on the test machine, same convention as the existing
    pandoc/xelatex integration tests): rasterising a fixture PDF produces
    valid PNG bytes; `extract_text` returns non-empty text; a missing PDF
    path raises rather than hanging or returning garbage.
  - The raster cache: two rasterisations of an unchanged PDF hit `pdftoppm`
    once; touching the PDF's mtime forces a second call.
  - `render_kitty_image`: round-trips a known PNG's bytes through the
    base64 payload.
- `idiomas doctor` (run manually or via a test): reports `pdftoppm` in the
  optional tier, `ok=False` with the poppler install message when absent.

## Manual, by the dev, in Ghostty

- [ ] Open Inspect Tree. The screen now shows two panels: tree (left),
      preview (right), each roughly half the width.
- [ ] Move the cursor onto a vocabulary file with a compiled PDF, in PDF
      mode. The right pane shows the actual rendered first page — fonts,
      layout, the Songti SC hanzi from M3 — not a placeholder.
- [ ] Move to a different file. The preview updates to that file's PDF.
- [ ] Move the cursor rapidly down a long tree (holding `j`). The tree
      scrolls smoothly; the app does not freeze or lag waiting on
      rasterisation, and the preview settles on the file the cursor stops
      on (stale in-flight renders don't pile up or show the wrong page).
- [ ] Move the cursor onto a directory. The pane shows "Select a file to
      preview" (or equivalent), not a crash or blank pane.
- [ ] Move the cursor onto a `.md` file with no compiled PDF (create one
      with `m`, don't wait for autocompile). The pane shows a clear
      no-PDF message.
- [ ] Toggle to MD mode (`tab`) on a file. The pane now shows the raw
      `.md` source text, not the PDF render.
- [ ] Resize the terminal (e.g. `Ctrl+Shift+=`/`-`, or drag the window).
      The rasterised preview re-renders sharp at the new pane size rather
      than staying blurry or clipped.
- [ ] Resize the window to a heavily skewed shape (very wide and short, or
      very narrow and tall). The page keeps its own proportions — never
      stretched to fill the pane.
- [ ] `esc` from the tree panel's content reaches the tree panel; `esc`
      again reaches the backpanel (now reachable with two panels, per
      `design.md`). shift+`l`/shift+`→` from the tree panel moves focus
      into the preview panel; shift+`h`/shift+`←` moves back.
- [ ] Delete/rename/new-dir/new-file/undo (`d`/`r`/`n`/`m`/`u`) and
      `enter`-to-open all still work exactly as before this milestone.
- [ ] Temporarily rename `pdftoppm` off `PATH` (or run in a container
      without poppler) and confirm the pane shows the poppler-missing
      message instead of crashing, and that compiling still works
      normally (`idiomas doctor` shows it as an optional warning, not a
      blocker).
- [ ] Run the same screen in a non-kitty-protocol terminal (e.g. macOS
      Terminal.app) with poppler installed: the pane falls back to
      `pdftotext` text output rather than failing or showing nothing.

## Done when

All boxes above are checked by the dev in their own tree, in Ghostty; the
full automated suite passes; and `idiomas doctor` correctly reports
`pdftoppm`'s presence/absence in its optional tier.
