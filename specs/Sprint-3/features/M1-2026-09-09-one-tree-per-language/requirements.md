# M1 · One tree per language — requirements

## Anchor (from the roadmap)

**Deliverable.**

- `source/` and `notebook/` merge into a single `tree-Chinese/`, **flat**:
  `tree-Chinese/Vocabulary/Food.md` and `tree-Chinese/Vocabulary/Food.pdf` sit
  side by side. No `md/`/`pdf/` subfolder split.
- `Config`'s `source_root` and `notebook_root` collapse into one `tree_root`,
  named from `Config.language`.
- `compile.py`'s source→notebook path mapping becomes suffix substitution
  within one tree. `browse.py`, `entry.py` and `doctor.py` follow.
- **The visual trees do not change.** The entry screen's tree still shows
  `.md` files with their categories as leaves and still reads `Chinese
  notebook` at the root; the user should not be able to tell from the UI that
  anything moved.
- `tree-Chinese/` is untracked: `git rm --cached` for what is tracked today,
  plus a `.gitignore` entry. Already-pushed history is **not** rewritten.
  The tree stays on disk locally, for testing.
- The location stays at the project root. Moving the trees out of the
  source-code directory is the installation wizard's job — out of scope.

**Done when.** The dev's real notebook lives in one `tree-Chinese/` with `.md`
and `.pdf` beside each other; `git status` shows nothing from it; entering
vocabulary, browsing and compiling all work against the merged tree; the
entry screen looks exactly as it did before; and the full test suite passes.

(Sources: [`../../roadmap-sprint-3.md`](../../roadmap-sprint-3.md) M1;
[`../../guidelines/backlog.md`](../../guidelines/backlog.md) *Trees rework*
and *Git treatment*; [`../../guidelines/notes-sprint-3.md`](../../guidelines/notes-sprint-3.md)
Decisions.)

## Scope

In scope:

- Collapsing `Config.source_root` / `Config.notebook_root` into a single
  `Config.tree_root`, derived from `Config.language` (`tree-{language}`, e.g.
  `tree-Chinese`), at the project root.
- Silently migrating the dev's existing `.idiomas.toml` (which holds the old
  `source_root`/`notebook_root` keys) to the new format on load — no
  re-prompt.
- Rewriting `compile.py`'s path mapping as suffix substitution within one
  `tree_root`, and updating every call site (`browse.py`, `entry.py`,
  `main_menu.py`, `__main__.py`, `doctor.py` if applicable) to the new single
  root.
- Moving the dev's real `source/*.md` files into `tree-Chinese/` (preserving
  content, `git mv` semantics), then recompiling fresh `.pdf` output directly
  into `tree-Chinese/` — the old `notebook/*.pdf` files are not moved, they're
  superseded by a recompile.
- Removing the now-empty `source/` and `notebook/` directories.
- Untracking `tree-Chinese/`: `git rm --cached` on what's tracked today under
  `source/`/`notebook/`, plus a `.gitignore` entry for `tree-Chinese/`.
- Updating the five test files whose fixtures build `source_root`/
  `notebook_root` trees: `test_compile.py`, `test_config.py`,
  `test_tui_browse_screen.py`, `test_tui_entry_screen.py`,
  `test_tui_main_menu.py`.

Out of scope:

- Moving `tree-Chinese/` out of the project root (installation wizard).
- Rewriting already-pushed git history to purge the two currently-tracked
  `source/*.md` files (dev's explicit choice, recorded in notes-sprint-3.md).
- Any change to what the entry screen's tree visually shows.
- Multi-language plumbing — `Config.language` already exists and defaults to
  `"Chinese"`; M1 doesn't add a second language, just derives the folder name
  from it.

## Decisions

| Decision | Rationale |
| --- | --- |
| `.idiomas.toml` migration is **silent** | Dev's call in the spec interview (2026-09-09). On load, if the old `source_root`/`notebook_root` keys are found and no `tree_root` key exists, the app derives `tree_root` from `Config.language` and rewrites the file in the new format automatically, without prompting. |
| The merge **moves** `.md` files, and **recompiles** `.pdf`s fresh | Dev's call in the spec interview (2026-09-09). `git mv` (or equivalent) for every `.md` under `source/` into `tree-Chinese/`, preserving content and relative structure. The `.pdf`s under `notebook/` are not moved — `compile_all()` is run against the new tree to regenerate them there. Simpler than reconciling two copies, and compile is already a cheap, idempotent step in this app. |
| `tree_root` is named `tree-{Config.language}` | Roadmap text: "collapse into one `tree_root`, named from `Config.language`." Matches the git-tracked test already present, `test_tree_root_reads_language_notebook` in `test_tui_entry_screen.py`, which anticipates a language-derived root label. |
| `notebook_path_for()` becomes suffix substitution within one root | Roadmap deliverable. Replaces `source_path.relative_to(source_root)` then `notebook_root / relative.with_suffix(".pdf")` (today's `compile.py:69-72`) with `md_path.with_suffix(".pdf")` directly — same tree, same relative path, only the extension changes. |
| Old `source/` and `notebook/` directories are removed once the merge is done | Nothing else in the codebase should reference them after M1; leaving empty mirrors around invites drift. |

## Context

- Current state (surveyed 2026-09-09): `Config` is a dataclass at
  `src/idiomas/config.py:10-14` with `source_root: Path`, `notebook_root:
  Path`, `language: str = "Chinese"`. `load_or_prompt_config()` reads
  `.idiomas.toml` via `tomllib` if present, else prompts interactively
  (defaulting to `project_root/"source"` and `project_root/"notebook"`) and
  writes a hand-built TOML string via `_write_config`. This *is* the existing
  wizard/setup flow — there's no separate wizard module. No version/schema
  field exists today, so migration must detect the old shape by the presence
  of `source_root`/`notebook_root` keys.
- `compile.py:69-72`'s `notebook_path_for()` and `compile_all()` (lines
  75-86, walks `source_root.rglob("*.md")`) are the only path-mapping logic
  to rewrite.
- No abstraction layer sits between `Config` and its consumers: `browse.py`
  functions take `source_root`/`notebook_root` as plain `Path` params;
  `entry.py:171,183`, `main_menu.py:38,42,46,54,57` and `__main__.py:19` all
  read `config.source_root`/`config.notebook_root` directly and pass them
  down. Every one of these call sites needs updating to `config.tree_root`.
- `doctor.py:20-35` checks only external tooling (pandoc, xelatex, xeCJK,
  CJK font) — no mirrored-tree checks exist today, so "doctor.py follows"
  means updating any references it has to the old root names, not adding new
  checks.
- Git today tracks `source/.gitkeep`, `source/Grammar/Asking for
  directions.md`, `source/Vocabulary/Food.md`, and `notebook/.gitkeep`
  (4 files, confirmed via `git ls-files`). `.gitignore` currently only
  ignores `notebook/**/*.pdf`.
- The testing question is already answered (see roadmap): every test in
  `tests/` builds its fixture trees under pytest's `tmp_path`, so untracking
  the real trees breaks no test. The five files needing fixture updates for
  the new single-root shape are listed above under Scope.
