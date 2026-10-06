# Validation — M4 · Inspect Tree, functional

Grounded in the roadmap's done-when condition, made concrete.

## Automated

- `pytest` — full suite passes, including:
  - `tests/test_tui_inspect_tree.py` (new): tree structure, PDF-mode `enter`
    (mocked `open`), MD-mode `enter` (mocked `suspend`/`nvim`), recompile
    triggered iff mtime changed, `tab` toggling, mode resets to PDF on fresh
    construction, missing-PDF compiles first.
  - `tests/test_tui_main_menu.py`: no "Notebook" option; "Inspect tree" pushes
    `InspectTreeScreen`.
  - `tests/test_tui_entry_screen.py`: unchanged pass count after the
    `FooterHint` migration — confirms no visible/behavioral regression on
    Entry screen.

## Manual (dev, against the real notebook)

- From the notebook menu, *Notebook* is gone; only *Inspect tree* remains for
  browsing the tree directly.
- Selecting *Inspect tree* opens the tree in **PDF mode** by default, border
  **red**, with a `"PDF MODE"` badge above the tree in red.
- Standing on a file and pressing `enter` opens its `.pdf` in the OS viewer.
- Pressing `tab` switches to **MD mode** (footer hint reflects the change,
  border turns **blue**, badge reads `"MD MODE"` in blue).
- `enter` on a file in MD mode drops into `nvim` on the `.md`, in the same
  terminal (no separate window, no corrupted terminal state on return).
- Editing and saving in nvim, then quitting, leaves an up-to-date `.pdf`
  without visiting *Compile* — confirmed by opening the PDF afterward (still
  in PDF mode requires `tab` back, or re-enter) and seeing the edit reflected.
- Quitting nvim **without** saving does not trigger a recompile.
- Leaving Inspect Tree (`q`) and re-entering starts back in **PDF mode**, even
  if MD mode was active before leaving.
- A file whose `.pdf` doesn't exist yet still opens correctly in PDF mode
  (compiled on the spot) — exercised with a fresh `.md` that has no sibling
  `.pdf`.
- Entry screen's footer hint still reads and behaves as before the
  `FooterHint` migration (dev's own eye, per M3's precedent for
  visually-identical refactors).

## Done when

All of the above hold, and the dev confirms after hands-on testing — matching
this project's standing rule that a milestone closes on the dev's word, not on
green tests alone.
