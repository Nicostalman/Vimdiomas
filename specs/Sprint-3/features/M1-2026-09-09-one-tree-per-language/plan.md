# M1 · One tree per language — plan

## 1. Config: collapse `source_root`/`notebook_root` into `tree_root`

- In `src/idiomas/config.py`, replace `Config`'s `source_root: Path` and
  `notebook_root: Path` fields with a single `tree_root: Path`.
- `load_or_prompt_config()`: on reading an existing `.idiomas.toml`, detect
  the old shape (presence of `source_root`/`notebook_root` keys, absence of
  `tree_root`). If found, derive `tree_root = project_root /
  f"tree-{language}"` and silently rewrite the file in the new format via
  `_write_config` (no prompt to the user).
- If no config file exists at all, the interactive prompt path
  (`_prompt_path`) now asks for a single tree location, defaulting to
  `project_root / f"tree-{language}"`.
- `_write_config` writes `tree_root` (and `language`) instead of the two old
  keys.

## 2. `compile.py`: suffix substitution within one tree

- Rewrite `notebook_path_for()` to take a single `md_path` (already inside
  `tree_root`) and return `md_path.with_suffix(".pdf")` — no more
  `relative_to`/root-swap.
- Update `compile_all()` to accept a single `tree_root`, walk
  `tree_root.rglob("*.md")`, and write each `.pdf` beside its `.md` via the
  new `notebook_path_for()`.

## 3. Update call sites: `entry.py`, `browse.py`, `main_menu.py`, `__main__.py`, `doctor.py`

- `entry.py`: replace `self.source_root = config.source_root` (and any use
  of `config.notebook_root`) with `self.tree_root = config.tree_root`;
  update the `notebook_path_for` call to the new one-argument form.
- `browse.py`: change `list_pdfs`, `paths_with_tag`, and the browse class's
  `__init__` to take one `tree_root: Path` instead of
  `source_root`/`notebook_root` pairs; update internal path construction
  accordingly (`.md` and `.pdf` are now siblings under the same root,
  distinguished only by suffix).
- `main_menu.py`: replace the `self.app.config.source_root` /
  `.notebook_root` reads with `self.app.config.tree_root`.
- `__main__.py`: `compile_all(config.source_root, config.notebook_root)` →
  `compile_all(config.tree_root)`.
- `doctor.py`: update any reference to the old root names if present; no new
  checks are added (it currently only checks external tooling).

## 4. Merge the dev's real trees on disk

- Create `tree-Chinese/` at the project root (if not already created by the
  config/prompt flow).
- Move every `.md` file under `source/` into `tree-Chinese/`, preserving
  relative path and content (`git mv` where tracked, plain move otherwise).
- Run `compile_all(tree_root)` against the new tree to regenerate `.pdf`s
  fresh into `tree-Chinese/` — the old `notebook/*.pdf` files are not moved.
- Delete the now-empty `source/` and `notebook/` directories.
- Confirm `.idiomas.toml` migration (step 1) points at `tree-Chinese/` and
  the app reads/writes correctly against it.

## 5. Untrack the merged tree

- Add `tree-Chinese/` to `.gitignore`.
- `git rm --cached` the currently-tracked files: `source/.gitkeep`,
  `source/Grammar/Asking for directions.md`, `source/Vocabulary/Food.md`,
  `notebook/.gitkeep`.
- Do not rewrite existing git history.

## 6. Update tests

- `test_config.py`: fixtures and assertions move from
  `source_root`/`notebook_root` to `tree_root`; add a case covering silent
  migration from an old-format `.idiomas.toml`.
- `test_compile.py`: fixtures build one tree instead of two;
  `notebook_path_for`/`compile_all` calls updated to the new signatures.
- `test_tui_browse_screen.py`, `test_tui_entry_screen.py`,
  `test_tui_main_menu.py`: fixture trees collapse to a single `tmp_path`
  root; any construction of a fake `Config` updated to the new field.
- Run the full suite and fix any fallout outside these five files that the
  refactor surfaces.

## 7. Manual verification

- Confirm `.idiomas.toml` on the dev's machine migrates silently on next
  launch.
- Confirm the entry screen's tree renders identically to before (categories
  as leaves, `Chinese notebook` at the root).
- Confirm entering vocabulary, browsing, and compiling all work end-to-end
  against `tree-Chinese/`.
- Confirm `git status` shows nothing from `tree-Chinese/`.
