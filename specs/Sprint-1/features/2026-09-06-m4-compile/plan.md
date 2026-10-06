# M4 · Compile — Plan

## 1. Config

- `src/idiomas/config.py`: a `Config` dataclass (`source_root: Path`, `notebook_root: Path`).
- `load_or_prompt_config(project_root: Path) -> Config`: read `.idiomas.toml` via `tomllib` if present; otherwise prompt via `input()` for each path (showing `source/`/`notebook/` as defaults, accepted on empty input), write the result as TOML, and return it. Wrap the prompt in a `try/except EOFError` so non-interactive contexts (tests, CI) fall back to the defaults instead of hanging.
- Add `.idiomas.toml` to `.gitignore`.

## 2. LaTeX template

- `templates/xecjk.tex`: `article` class, `fontspec`, `xeCJK` with `\setCJKmainfont{Songti SC}`, `longtable` + `booktabs`, `secnumdepth` set to suppress section numbering, `\title{$title$}`/`\maketitle`, `$body$`.
- Sanity-check it directly with a minimal `pandoc ... --template=templates/xecjk.tex` smoke test before wiring it into `compile.py`.

## 3. Intermediate markdown rendering

- `src/idiomas/compile.py`: `render_markdown(deck: Deck) -> str`.
- Uncategorized entries (if any): an unheaded 3-column pipe table (`Hanzi | Pinyin | Gloss`) right after the YAML title metadata.
- Each category: a `##` heading (`category.name`) followed by its own 3-column table.
- Per entry: pinyin converted via `idiomas.pinyin.to_tone_marks`; gloss cell is `gloss` or `gloss *(note)*` when `entry.note` is set. Escape any literal `|` in a cell (table-column separator) defensively, even though the current fixtures don't have one.
- No `## Tags` section is emitted.

## 4. Single-file and mirrored compile

- `compile_file(source_path: Path, notebook_path: Path) -> None`: parse the source file, render its markdown, run `pandoc -f markdown -t pdf --pdf-engine=xelatex --template=templates/xecjk.tex --shift-heading-level-by=-1 -o notebook_path` with the markdown piped via `input=` on `subprocess.run`; create `notebook_path`'s parent directories as needed.
- `compile_all(source_root: Path, notebook_root: Path) -> list[Path]`: walk `source_root` for `.md` files, compute each mirrored `.pdf` path under `notebook_root`, skip when the `.pdf` already exists with a newer mtime than the source, else call `compile_file`. Returns the list of paths actually (re)compiled, for reporting.

## 5. `doctor`

- `src/idiomas/doctor.py`: `check() -> list[str]` (or similar) returning human-readable problem lines; empty list means healthy.
- Checks, in order: `shutil.which("pandoc")`, `shutil.which("xelatex")`, `subprocess.run(["kpsewhich", "xeCJK.sty"])` for xeCJK, and the Songti SC font file's existence. Each missing check appends its own actionable line; xeCJK's line is exactly `sudo tlmgr install xecjk`.

## 6. CLI wiring

- `__main__.py`: `argparse` with subcommands `compile` and `doctor`; no subcommand keeps today's no-op behavior (M0). `compile` loads/prompts config, calls `compile_all`, and prints a short summary (how many files compiled/skipped). `doctor` calls the doctor checks and prints either "all good" or the actionable lines, exiting non-zero if anything is missing.

## 7. M6 seed content

- `source/Vocabulary/Food.md`: Meat, Vegetables, Fruits categories, per the roadmap's M6 text. Include `牛肉`/`niu2rou4` so the roadmap's own M4 "Done when" wording (`niúròu` in the rendered PDF) is checked against real seed content, not a throwaway fixture.
- `source/Grammar/Asking for directions.md`: carrying `#travel` and `#"C1 exam"` tags, per the roadmap's M6 text.

## 8. Tests

- `render_markdown()`: assert the table structure, tone-mark conversion, note inlining, and absence of a Tags section, against a small in-memory `Deck`.
- `compile_all()`'s skip logic: unit test with fake mtimes (no real pandoc call needed) confirming an up-to-date `.pdf` is left alone and a stale one is regenerated.
- `doctor.check()`: test the missing-xeCJK message text directly; for the "all present" path, only assert it returns no problems on this machine (can't easily fake presence/absence of real binaries without mocking `shutil.which`/`subprocess.run`, so mock those for the negative-path checks).
- One real, non-mocked end-to-end test: `compile_all()` against `source/` (or a fixture tree) actually invoking pandoc/xelatex, asserting the resulting `Food.pdf` exists, is non-empty, and (via a PDF text-extraction check, e.g. `pypdf` or shelling out to `pdftotext` if available) contains `niúròu`.
