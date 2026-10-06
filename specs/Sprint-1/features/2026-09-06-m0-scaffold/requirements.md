# M0 · Documentation and scaffold — Requirements

## Roadmap anchor

**Deliverable.** `readme.md`, `mission.md`, `stack.md`, `roadmap.md`. `pyproject.toml` with a src layout, `.gitignore`, a venv, and the empty `source/` and `notebook/` trees.

**Done when.** `pip install -e ".[dev]"` succeeds and `python -m idiomas` starts and exits cleanly, even doing nothing.

## Scope

In scope for this phase:

- `pyproject.toml` declaring the `idiomas` package under a `src/` layout, with an `[dev]` extra.
- `src/idiomas/__init__.py` and `src/idiomas/__main__.py` so `python -m idiomas` is a valid invocation.
- `.gitignore` for a Python project (venv, bytecode, test cache).
- Empty `source/` and `notebook/` trees, per the two-tree model in readme.md, so the paths exist even before any content is entered.
- A venv, created and left activatable per the `stack.md` prerequisites section (not committed).

Explicitly deferred (belongs to later milestones):

- Any subcommand logic — `compile`, `doctor`, or the TUI itself. `python -m idiomas` in this phase does nothing beyond starting and exiting cleanly.
- Any dependency beyond what M0 itself exercises. `textual` and `pypinyin` are not declared here — they land in the milestones that actually use them (M2, M5).
- The four docs (`readme.md`, `mission.md`, `stack.md`, `roadmap.md`) already exist at the project root and were moved under `specs/` as part of setting up this feature-spec workflow — no content changes to them are in scope for M0 itself.

## Decisions

- **Package layout:** `src/idiomas/`, matching the `python -m idiomas` invocation documented in `readme.md` and the "Packaging" row of `stack.md` (`pyproject.toml`, src layout, venv).
- **CLI scope:** no-op entry point only. `src/idiomas/__main__.py` runs and exits 0 with no argument parsing. This matches the roadmap's own "Done when" bar — "starts and exits cleanly, even doing nothing" — and avoids building CLI surface (`compile`, `doctor`) ahead of the milestones (M4, M5) that give it something to do.
- **Dependencies:** `[dev]` extra declares `pytest` only, per `stack.md`'s "Tests — pytest" section. `textual` and `pypinyin` are real dependencies of later milestones, not of the scaffold, so they're added when those milestones start rather than declared unused here.

## Context

- This is the first roadmap phase; no prior spec folders existed under `specs/` before this one.
- As part of running the feature-spec workflow for this phase, `roadmap.md`, `mission.md`, and `stack.md` were moved from the project root to `specs/` (commit `92b4ba2`, on `main`, before this branch was cut). `readme.md` stays at the project root.
- `stack.md`'s "Prerequisites" table confirms Python 3.14.7, pandoc, and xelatex are already present on this machine; `xeCJK` is not, but it is not needed until M4 (Compile) and is out of scope here.
