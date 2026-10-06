# M4 · PDF preview pane — plan

Task groups, ordered so later groups depend only on earlier ones.

## 1. Terminal capability detection

- New module `idiomas/terminal.py`: `supports_kitty_graphics() -> bool`,
  reading `TERM_PROGRAM`/`TERM` env vars (`ghostty`, `wezterm`, or
  `TERM=xterm-kitty`; `kitty` itself sets `TERM_PROGRAM=kitty` too in some
  configs — check for the set of known values rather than just `ghostty`).
- Unit tests: each known value returns `True`; an unset/unknown value
  returns `False`. Pure function, no subprocess, trivially testable.

## 2. Rasterisation

- New module `idiomas/pdf_preview.py`:
  - `pdftoppm_available() -> bool` (`shutil.which("pdftoppm")`).
  - `page_aspect_ratio(pdf_path: Path) -> float`: runs `pdfinfo -f 1 -l 1
    <pdf>`, parses the `Page 1 size: <w> x <h> pts (...)` line, returns
    `w / h`. Needed because `rasterise_page` fits inside a box rather than
    stretching to it (below) — without the page's own ratio there's no way
    to know which of the box's two dimensions is the binding one.
  - `rasterise_page(pdf_path: Path, width_px: int, height_px: int) -> bytes`:
    **`pdftoppm` turns out to have no stdout mode** (discovered during
    implementation — passing `-` as the output root writes a literal file
    named `--1.png` instead of writing to stdout, unlike `pdftotext`, which
    does support `-` for stdout). Runs `pdftoppm -png -singlefile -f 1 -l 1
    <pdf> <tmp-root>` into a `tempfile.TemporaryDirectory()`, reads
    `<tmp-root>.png` back, returns its bytes.
    **Fits inside the `width_px` x `height_px` box preserving the page's own
    aspect ratio, rather than stretching to fill it** (surfaced during the
    dev's manual Ghostty testing — the original independent `-scale-to-x`
    *and* `-scale-to-y` pair skews the page on a non-matching box). A second
    surprise here: `pdftoppm` does **not** compute the other dimension
    proportionally when only one of `-scale-to-x`/`-scale-to-y` is given
    (checked against the installed poppler build) — the unset one just
    falls back to a default 150dpi resolution. So both target dimensions
    are always computed explicitly, from `page_aspect_ratio` and whichever
    of the box's two is the tighter constraint, and passed together —
    already matching the page's ratio, so `pdftoppm` has nothing left to
    stretch.
    Raises `FileNotFoundError` for a missing PDF (checked explicitly, before
    ever shelling out) or `subprocess.CalledProcessError` on a nonzero
    `pdftoppm`/`pdfinfo` exit — the caller turns either into a degradation
    message.
  - `extract_text(pdf_path: Path) -> str`: runs `pdftotext <pdf> -`, returns
    stdout decoded — the no-kitty-protocol fallback.
- Unit tests against a real small PDF fixture (marked `integration`, like
  the existing pandoc/xelatex tests) covering: successful rasterisation
  produces valid PNG bytes (sniff the PNG magic number) *and* preserves
  the page's aspect ratio inside a skewed box (sniff the PNG's own
  width/height header, not just its magic number); a nonexistent PDF path
  raises; `extract_text` returns non-empty text for a known-text fixture
  PDF.

## 3. Raster cache

- New module-level cache in `idiomas/pdf_preview.py` (or a small dedicated
  class), separate from `compile.py`'s `CACHE_PATH` — in-memory only
  (`dict[tuple[Path, int, int], bytes]` keyed on PDF path + target pixel
  size), not persisted to disk. An in-memory cache is enough: it only needs
  to survive repeat cursor visits within one running session, and avoids a
  second on-disk cache format decision this milestone doesn't need.
- Invalidate an entry when the PDF's mtime has changed since it was cached
  (store `(mtime, bytes)`; compare on lookup).
- Unit test: rasterising the same PDF+size twice calls `pdftoppm` once
  (mock/count subprocess calls); touching the PDF's mtime and rasterising
  again calls it a second time.

## 4. Kitty graphics protocol renderer

- New function in `idiomas/terminal.py` (or a `kitty_graphics.py` if it grows):
  `render_kitty_image(png_bytes: bytes) -> str`, building the APC escape
  sequence (`\x1b_G...` chunks, base64-encoded payload, per the kitty
  graphics protocol spec) as a string ready to write to stdout.
- A Textual widget, `PdfPreview(Static)` (or similar) in
  `idiomas/tui/screens/inspect.py`, whose `render()`/`on_mount` writes the
  escape sequence directly to the terminal at its own screen position
  (Textual doesn't composite raw terminal graphics itself, so this widget
  is deliberately a thin wrapper that positions the cursor and writes the
  escape codes, then reserves blank space in the layout so Textual doesn't
  overdraw it) — study Textual's `App.on_resize`/`region` APIs for how to
  get the widget's on-screen pixel region reliably.
- Unit test: `render_kitty_image` on a known small PNG produces output
  containing the expected escape prefix/suffix and a base64 payload that
  decodes back to the same bytes.

## 5. `InspectTreeScreen` — the second panel

- Wrap the existing `#inspect-panel` and a new `#preview-panel` in a
  `Horizontal` inside `Backpanel()`, mirroring `EntryScreen`'s
  `tree-panel`/`entry-form` layout. `app.tcss`: both panels `width: 50%`.
- `#preview-panel` holds the `PdfPreview` widget plus a `Static` for
  degradation messages (only one visible at a time).
- Hook the tree's cursor movement (not just `Tree.NodeSelected`, which only
  fires on `enter`/select) — Textual's `Tree` has a `cursor_line`
  reactive/`NodeHighlighted` message; use whichever fires on cursor move
  without selecting, confirmed against the installed Textual version.
- On cursor move to a node, dispatch by `NodeData.kind` and `self.mode`:
  - `dir` → message: "Select a file to preview."
  - `file`, `mode == "md"` → read and show the source `.md` text directly
    (no worker needed — a text read is cheap and synchronous, unlike
    rasterisation).
  - `file`, `mode == "pdf"`:
    - no compiled PDF (`notebook_path_for` doesn't exist) → message: "No
      compiled PDF for this file."
    - PDF exists, no `pdftoppm` → message: "Install poppler for a PDF
      preview (`brew install poppler`)."
    - PDF exists, `pdftoppm` present, no kitty support → run
      `extract_text` in a worker, show the result as plain text.
    - PDF exists, `pdftoppm` present, kitty support → run
      `rasterise_page` in a worker (via the cache), render with
      `render_kitty_image`.
- All worker dispatch follows `autocompile_one`'s shape: `run_worker(...,
  thread=True, exclusive=True, group="preview")` — `exclusive=True` here,
  unlike autocompile's `False`, because a fast-moving cursor should cancel
  a stale in-flight render rather than queue it (this is the mechanism that
  satisfies "moving fast down the tree doesn't stall").
- On resize (`on_resize` / watching the preview panel's size), re-rasterise
  the currently shown PDF at the new pixel size if in PDF+kitty mode, fit
  inside it preserving the PDF's own aspect ratio (never stretched).

## 6. `doctor.py`

- Add a `Check("pdftoppm", required=False, ...)` entry, `ok=
  pdftoppm_available()`, message pointing at `brew install poppler`, url
  to poppler's project page — same shape as the existing `macism`/`nvim`
  optional checks.

## 7. `design.md`

- Add Inspect Tree's two-panel layout and the preview pane's behaviour to
  the standing conventions (the two-panel `esc`/shift+hjkl consequence is
  already covered generally by the existing rules — this only needs to
  state that Inspect Tree now has two panels and what the second one does).

## 8. Tests and validation pass

- Run the full suite; add/verify coverage per `validation.md`.
- Hand off to the dev for a real Ghostty check.
