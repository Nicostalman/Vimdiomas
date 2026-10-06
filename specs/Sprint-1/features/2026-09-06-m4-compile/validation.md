# M4 · Compile — Validation

Roadmap's own "Done when": *`python -m idiomas compile` produces `notebook/Vocabulary/Food.pdf` with hanzi rendered and `niu2rou4` shown as `niúròu`; and `doctor` gives an actionable message on a machine without xeCJK.*

## Checks

1. `pytest` passes, including:
   - `render_markdown()` unit tests: table structure, tone-mark conversion, note inlining, no `## Tags` section.
   - `compile_all()`'s mtime-based skip logic (mocked mtimes, no real pandoc invocation needed for this part).
   - `doctor.check()`'s missing-xeCJK message is exactly actionable text including `sudo tlmgr install xecjk` (tested via mocking the xeCJK detection call to simulate absence).
   - One real end-to-end test that actually shells out to `pandoc`/`xelatex`: compiling a fixture (or the real seed `Food.md`) produces a real, non-empty PDF whose extracted text contains `niúròu` (via `pypdf`, added as a dev dependency).
2. Manual end-to-end check on this machine (already has xeCJK installed):
   ```sh
   python -m idiomas compile
   ```
   - Produces `notebook/Vocabulary/Food.pdf` and `notebook/Grammar/Asking for directions.pdf`.
   - Open `Food.pdf` (or extract its text) and confirm hanzi render (not tofu/missing-glyph boxes) and `niúròu` appears correctly tone-marked.
   - Re-run `python -m idiomas compile` immediately after: it reports the files as already up to date (skipped), not recompiled.
   - Touch/edit `source/Vocabulary/Food.md` and re-run: `Food.pdf` is regenerated (newer mtime than the previous PDF).
3. `python -m idiomas doctor` on this machine reports all checks passing (pandoc, xelatex, xeCJK, Songti SC all present).
4. No regressions: full `pytest` suite (M0–M3 tests included) still passes; `python -m idiomas` with no subcommand still exits cleanly doing nothing.

## Definition of done

- All of the above pass.
- `compile.py` exports `render_markdown`, `compile_file`, `compile_all`; `doctor.py` exports its check function; `config.py` exports `Config`/`load_or_prompt_config`. No TUI wiring (M5 untouched).
- `source/Vocabulary/Food.md` and `source/Grammar/Asking for directions.md` exist with the content the roadmap's M6 section specifies.
