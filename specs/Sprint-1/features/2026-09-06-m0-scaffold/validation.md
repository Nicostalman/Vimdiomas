# M0 · Documentation and scaffold — Validation

Acceptance bar for merging this branch, grounded in the roadmap's own "Done when": `pip install -e ".[dev]"` succeeds and `python -m idiomas` starts and exits cleanly, even doing nothing.

## Checks

1. **Clean install succeeds.**
   ```sh
   rm -rf .venv
   python3 -m venv .venv && source .venv/bin/activate
   pip install -e ".[dev]"
   ```
   Passes if this exits 0 with no errors, from a machine that has never had this venv before.

2. **Entry point starts and exits cleanly.**
   ```sh
   python -m idiomas; echo "exit: $?"
   ```
   Passes if it prints `exit: 0` and produces no traceback, with no arguments and doing nothing else.

3. **Package layout is correct.**
   - `src/idiomas/__init__.py` and `src/idiomas/__main__.py` exist.
   - `pip show idiomas` (inside the venv) reports the package as installed in editable mode.

4. **Trees exist.**
   - `source/` and `notebook/` both exist at the project root and are tracked by git (via `.gitkeep` or equivalent), and are empty of content otherwise.

5. **`.gitignore` is effective.**
   - After the venv is created and `pip install -e ".[dev]"` has run, `git status --porcelain` shows no `.venv/`, `__pycache__/`, or `*.egg-info/` entries as untracked.

6. **Dev environment is usable for the next milestone.**
   ```sh
   pytest
   ```
   Passes if this runs (even collecting zero tests) with no configuration errors — confirms `pytest` is correctly declared and installed for M1 to build on.

## Out of scope for this validation

- `compile` and `doctor` subcommands, and the TUI — not built in M0, so not tested here.
- Any docs content changes to `readme.md`, `mission.md`, `stack.md`, `roadmap.md` — this phase only relocates three of them under `specs/`, which was already committed to `main` before this branch was cut.

## Merge bar

All six checks pass on a clean clone of this branch. No open questions from `requirements.md` remain unresolved.
