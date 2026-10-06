# M4 · Compile — Requirements

## Roadmap anchor

**Deliverable.** `compile.py` plus the xeCJK LaTeX template. Renders a deck to intermediate markdown with tone-marked pinyin and 3-column tables, runs pandoc through xelatex, and mirrors `source/` into `notebook/`, skipping PDFs newer than their source. A `doctor` command checks pandoc, xelatex, `xeCJK` and the CJK font, printing `sudo tlmgr install xecjk` when it is missing instead of a LaTeX traceback.

**Done when.** `python -m idiomas compile` produces `notebook/Vocabulary/Food.pdf` with hanzi rendered and `niu2rou4` shown as `niúròu`; and `doctor` gives an actionable message on a machine without xeCJK.

## Scope

This phase also folds in the roadmap's **M6 · Seed content** (normally a later milestone) so there is real content to compile against — see "M6 folded in" below. `M5 · The TUI` remains untouched; there is no interactive entry screen yet, only the CLI.

In scope:

- `src/idiomas/config.py` — a project-local config (`.idiomas.toml` at the repo root, gitignored) holding `source_root` and `notebook_root`. Loaded if present; if absent, the user is prompted once (via `input()`, with the existing `source/`/`notebook/` directories offered as defaults) and the answer is persisted. Non-interactive contexts (no stdin, e.g. tests) fall back to the offered defaults rather than hanging.
- `src/idiomas/compile.py`:
  - `render_markdown(deck: Deck) -> str` — deck to intermediate markdown: uncategorized entries as an unheaded 3-column table (Hanzi | Pinyin | Gloss) right after the title, then each category as a `##` heading with its own 3-column table. Pinyin is converted tone-numbered -> tone-marked via M2's `to_tone_marks`. A note is appended inline in the gloss cell as `gloss *(note)*` (pandoc pipe-table cells can't contain literal newlines). Tags are not rendered — they're a search concern (M3), not a print concern.
  - `compile_file(source_path, notebook_path)` — runs `render_markdown()`'s output through `pandoc` (via stdin, no intermediate file written to disk) with `--pdf-engine=xelatex`, `--template=templates/xecjk.tex`, and `--shift-heading-level-by=-1` (so a file's categories render as top-level, unnumbered sections rather than subsections nested under nothing).
  - `compile_all(source_root, notebook_root)` — mirrors every `.md` under `source_root` to a same-relative-path `.pdf` under `notebook_root`, skipping files whose output `.pdf` has a newer mtime than the source `.md`.
- `templates/xecjk.tex` — a minimal, hand-written pandoc LaTeX template (not derived from pandoc's own default, which is large and version-coupled): `article` class, `fontspec` + `xeCJK` with `\setCJKmainfont{Songti SC}`, `longtable`/`booktabs` for the tables, unnumbered sections (`secnumdepth` set to suppress numbering — this is a reference sheet, not a numbered document), `$title$`/`$body$` pandoc variables.
- `src/idiomas/doctor.py` — checks for `pandoc`, `xelatex` (both via `shutil.which`), `xeCJK.sty` (via `kpsewhich xeCJK.sty`), and the Songti SC font file. Missing xeCJK prints exactly `sudo tlmgr install xecjk` (per the roadmap) rather than letting a LaTeX compile fail with a traceback later.
- CLI wiring in `__main__.py`: `python -m idiomas compile` and `python -m idiomas doctor` as subcommands (via `argparse`). Calling `python -m idiomas` with no subcommand keeps M0's behavior — starts and exits cleanly, doing nothing.
- **M6 folded in:** real seed content under `source/`, per the roadmap's M6 deliverable text verbatim — `source/Vocabulary/Food.md` with Meat, Vegetables and Fruits categories, and `source/Grammar/Asking for directions.md` carrying `#travel` and `#"C1 exam"`. This is what makes `python -m idiomas compile` produce a real `notebook/Vocabulary/Food.pdf` end-to-end, satisfying the roadmap's own "Done when" wording literally.

Explicitly deferred:

- Anything about the TUI (M5) — no interactive entry screen, no wiring of `compile.py` into a screen; it's invoked from the CLI only.
- Watch mode (auto-recompile on save) — roadmap's own "Later" section.
- A fuller M6 seed set beyond the roadmap's own literal M6 text — this phase adds exactly what M6 specifies, not more.

## Decisions

- **Config: project-local `.idiomas.toml`, prompted once.** Confirmed with the user. Not `~/.config/idiomas/` — keeps everything about a given idiomas project self-contained in its own repo, matching the "single-user, plug-and-play" ethos in `mission.md`/`stack.md`. Gitignored since it's a local, machine-specific path choice, not project source.
- **`compile.py`'s root paths are read from config, not hardcoded** — mirrors `store.py`'s `walk(root)` design (M3) and satisfies the user's explicit ask that source/notebook roots be user-choosable, asked once.
- **xeCJK confirmed installed and working on this machine** (`sudo tlmgr install xecjk`, run by the user; verified independently with a minimal XeLaTeX smoke test producing a PDF with `牛肉` and `niúròu` rendered correctly) — see `validation.md` for the full end-to-end check this enables.
- **Custom minimal LaTeX template, not pandoc's default.** Copying pandoc's ~150-line default template would be more "complete" (bibliography, syntax highlighting, etc. support) but couples the template to a specific pandoc version and carries a lot of machinery this project never needs. A from-scratch template covering exactly title + xeCJK + tables is simpler to read, maintain, and reason about.
- **Unnumbered category headings, shifted up one level.** A vocabulary reference sheet doesn't need "1.1 Vegetables" numbering; categories render as clean unnumbered top-level headings via `--shift-heading-level-by=-1` plus `secnumdepth` suppression in the template.
- **Notes are inlined into the gloss cell**, not a fourth table column or a footnote — pandoc pipe-table cells are single-line, and a note is a rare, short annotation (per M1's fixtures), so `gloss *(note)*` reads naturally without complicating the table structure.
- **Tags are not compiled into the PDF.** They exist for `tag_index()`/search (M3), which is a discovery concern; the printed reference sheet is not where tags would be read.
- **Intermediate markdown is not persisted to disk.** It's piped to `pandoc` via stdin and discarded; nothing in the roadmap asks for the intermediate file itself to be inspectable, and not writing it avoids a class of stale-intermediate-file bugs.

## Context

- Builds on M1 (`parse()`/`Deck`/`Category`/`Entry`), M2 (`to_tone_marks`), and M3 is not directly reused here (`store.py`'s tree is for the TUI's browse screen; `compile.py` does its own `rglob("*.md")` walk since it needs each file's mtime and full parsed `Deck`, not `store.py`'s summarized categories-only tree node).
- `stack.md`'s "PDF" section already fixed pandoc → xelatex + xeCJK, Songti SC, and rejected weasyprint/plain-HTML/headless-Chrome — this phase implements exactly that pipeline, not an alternative one.
- `stack.md` listed xeCJK as missing at scaffold time; it is now installed and verified (see Decisions above), so this phase's "Done when" is checked for real, not mocked.
