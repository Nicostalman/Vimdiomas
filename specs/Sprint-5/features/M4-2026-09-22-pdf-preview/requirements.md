# M4 · PDF preview pane — requirements

## Anchor (from the roadmap)

**Deliverable.** Inspect Tree gains a second panel, to the right of the tree,
showing the PDF of whatever the cursor is on. It follows the cursor. A real
rendered page, not text: `pdftoppm` rasterises the first page and it is drawn
with the kitty graphics protocol (Ghostty 1.3.1). poppler is an optional
dependency (`doctor`'s optional tier, no block on compiling). Graceful
degradation for every failure case, stated as behaviour. Rasterising happens
off the UI thread. Everything Inspect Tree already does keeps working; the
screen goes from one panel to two, so `esc`/shift+hjkl start reaching the
backpanel per `design.md`'s own rule.

**Done when.** Moving the cursor onto a file shows its compiled PDF in the
right-hand pane; moving to another file changes it; moving fast down the tree
doesn't stall; a directory, a PDF-less file, a missing `pdftoppm` and an
image-incapable terminal each show a clear message instead of failing;
`idiomas doctor` reports `pdftoppm` as optional; `esc`/shift+hjkl behave per
`design.md` now that the screen has two panels; the dev confirms by eye in
Ghostty; the same screen in a terminal with no image support degrades to a
message (or, per this milestone's own decision below, to text) rather than
breaking; and the full test suite passes.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*implement pdf preview* — "in the right pane of the inspect tree screen."

## Decisions from the spec conversation (2026-09-22)

| Decision | Rationale |
| --- | --- |
| **Kitty graphics protocol only, no iTerm2 escape** | Dev: "im using ghostty. the program should be usable in non kitty terminals, but without preview." Scope stays the one protocol the dev's own terminal speaks; portability is handled by degrading cleanly, not by a second protocol implementation. |
| **Protocol support detected via environment variables** (`TERM_PROGRAM` / `TERM`), not a terminal capability query | Simple, no I/O, no risk of hanging on a non-responding terminal. Matches how Ghostty and kitty already advertise themselves (`TERM_PROGRAM=ghostty`, `TERM_PROGRAM=WezTerm`, `TERM=xterm-kitty`). |
| **A rasterised page is re-rendered on resize**, sized to the pane's current pixel dimensions | Keeps the preview sharp at whatever size the pane actually is, rather than blurring a fixed-DPI render to fit. |
| **Rasterised pages are cached, keyed on the PDF's own content** (independent of M2's compile-staleness cache) | Avoids re-rasterising an unchanged PDF every time the cursor revisits it. M2's cache tracks source-`.md`-to-PDF staleness; this is a second, separate cache for PDF-to-raster, keyed by the PDF's own hash so it stays correct regardless of why the PDF changed. |
| **The preview pane shows content in both PDF mode and MD mode, but different content per mode** — PDF mode shows the rasterised page, MD mode shows the `.md` source file's raw text | Dev: "md mode should preview text" — read together with a follow-up ("Raw .md source") as: the pane always shows *something* relevant to the mode you're in, not just the PDF regardless of mode. MD mode's text is the source file itself, matching what `Enter` opens in nvim in that mode — not `pdftotext` output, which needs poppler and a compiled PDF and wouldn't match the source's tab-separated triad formatting. |
| **Tree panel and preview panel split the screen evenly** (50/50) | Dev's choice; a rendered page needs real width, same as the tree does. |
| **A directory node shows "no file selected" text**, not a blank pane | Dev's choice; consistent with every other degradation case being a stated message rather than silence. |
| **A terminal without kitty-protocol support but with poppler installed falls back to `pdftotext` output** in PDF mode, not just a message | Already decided in `notes-sprint-5.md`'s Decisions table when poppler was chosen: "`pdftotext` ships with it, which gives the no-protocol fallback for free from the same install." Only a fully missing poppler installation falls back to a plain message. |
| **The rasterised page always keeps the PDF's own aspect ratio** — fit inside the pane's box, never stretched to fill it | Surfaced during the dev's manual Ghostty testing (2026-09-22): the original `-scale-to-x`/`-scale-to-y` pair stretches independently to fill the box exactly, skewing the page on a non-matching aspect ratio. |

## Scope

**In scope.**

- A second `Panel` in `InspectTreeScreen`, to the right of the existing tree
  panel, inside a `Horizontal` (mirrors `EntryScreen`'s `tree-panel`/
  `entry-form` layout — see [`design.md`](../../../current/design.md)).
- A rasterisation helper (new module, `idiomas.pdf_preview` or similar —
  `plan.md`'s call) wrapping `pdftoppm`, run in a worker thread, producing PNG
  bytes sized to the pane's current pixel dimensions.
- A kitty-graphics-protocol renderer: encodes PNG bytes as the escape
  sequence and writes it so Textual/Ghostty displays it inside the preview
  panel's region.
- A second, PDF-hash-keyed raster cache, independent of M2's compile cache.
- Runtime detection of: kitty-protocol support (env vars) and poppler
  presence (`shutil.which("pdftoppm")`).
- Degradation messages for: no poppler, no kitty-protocol support (with the
  `pdftotext` fallback when poppler is present), a directory selected, a file
  with no compiled PDF, a PDF that fails to rasterise.
- MD-mode text preview of the raw source file.
- `doctor.py` gains a `pdftoppm` check in the optional tier, with a `brew
  install poppler` message.
- Resize handling: re-rasterise (PDF mode) at the new pane size, fit inside
  it preserving the PDF's own aspect ratio (never stretched).
- `esc`/shift+hjkl now reach the backpanel and move between the two panels,
  per `design.md`'s existing rule — no new code beyond what `Panel`/
  `Backpanel` already provide, but explicitly verified in `validation.md`.

**Out of scope** (recorded here so it isn't quietly attempted mid-milestone):

- iTerm2's inline-image escape (see Decisions above).
- Multi-page preview — `specs/Sprint-5/roadmap-sprint-5.md`'s own "Not in
  this sprint" list; only the PDF's first page is ever shown.
- Any change to Entry, Browse, or any other screen.
- Any change to how PDFs are compiled (M2/M3's territory) — this milestone
  only reads existing PDFs.

## Context

- `InspectTreeScreen` (`src/idiomas/tui/screens/inspect.py`) currently has one
  `Panel` (`#inspect-panel`) holding the tree, a mode badge, and a footer
  hint. `Tree.NodeSelected` fires on `enter`; the cursor moving (without
  selecting) is a separate Textual event this milestone needs to hook —
  `plan.md`'s call on which one.
- `notebook_path_for` (`compile.py`) maps a `.md` path to its sibling `.pdf`
  path; the preview reads whatever PDF is already on disk and never triggers
  a compile itself (compiling-on-preview isn't in the roadmap and would
  contend with autocompile workers).
- `idiomas.platform` (`src/idiomas/platform/__init__.py`) is the existing
  per-OS dispatch pattern (`macos.py` vs. the inert fallback) — terminal
  detection is not OS detection, so it does not obviously belong there, but
  `plan.md` decides where the new code lives.
- `autocompile_one` (`base.py`) is the existing pattern for off-UI-thread
  work reported back to the app; the rasteriser worker follows the same
  shape (`self.app.run_worker(..., thread=True, ...)`).
- `poppler` is not currently a project dependency anywhere (`pyproject.toml`
  lists only `pypinyin`/`textual`) — this milestone's `pdftoppm`/`pdftotext`
  calls are external-tool subprocess calls, like `pandoc`/`xelatex` already
  are, not a Python package dependency.
