# M3 · Autocompile — validation

Acceptance bar for this branch, grounded in the roadmap's **Done when**
condition ([`../../roadmap-sprint-2.md`](../../roadmap-sprint-2.md#m3--autocompile))
as narrowed by [`requirements.md`](requirements.md)'s scope decision
(condition 2 only — compile on leaving the entry screen).

## Automated

- `uv run pytest tests/test_tui_entry_screen.py -v` (or wherever the
  autocompile tests land per plan.md §5) passes, covering:
  - an entry save marks its file dirty;
  - leaving the screen with a dirty file triggers exactly one compile call
    per dirty file, with the correct `(source_path, notebook_path)` pair;
  - leaving the screen with no dirty files triggers no compile;
  - multiple dirty files (different files touched in one session) are all
    compiled on exit;
  - a failing compile produces an `app.notify(..., severity="error")` call
    naming the file, and does not crash the app or block the screen pop.
- `uv run pytest tests/test_compile.py -v` passes, including a new case for
  `notebook_path_for` and confirming `compile_all`'s existing tests are
  unaffected by the refactor.
- Full suite (`uv run pytest`) passes — no regressions elsewhere from the new
  `on_unmount` hook or the `App`-owned worker.

## Manual / hand-testing

Against an isolated scratch notebook (never the real one):

1. **Basic autocompile**: open the entry screen, add a word to a category in
   `Food.md`, press `q` to leave. Without visiting *Compile*, check
   `notebook/.../Food.pdf` — it should exist and be up to date (newer than
   the `.md`, containing the new word).
2. **No-op on no entries**: open the entry screen, move the cursor around
   without adding anything, press `q`. No compile should run (no new/updated
   PDF, no delay before the main menu reappears).
3. **Multiple files in one session**: add an entry to `Food.md`, move to a
   different file's category, add an entry there too, then press `q`. Both
   files' PDFs should be up to date afterward.
4. **Responsiveness**: with a real pandoc/xelatex install, add an entry and
   press `q` immediately — the main menu should reappear right away, not
   after however long the compile takes. (The compile is still running in
   the background — check the PDF a moment later to confirm it lands.)
5. **Failure surfaces visibly**: temporarily break compilation (e.g. rename
   `templates/xecjk.tex` or otherwise force a pandoc/xelatex error), add an
   entry, leave the screen — a toast notification should appear naming the
   failed file, rather than the failure being silent.

## Merge bar

All automated cases pass, and the manual walkthrough (1–5) is run once
against a real notebook fixture before the branch is proposed for merge.
