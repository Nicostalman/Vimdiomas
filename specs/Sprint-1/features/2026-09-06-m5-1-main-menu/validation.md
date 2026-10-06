# M5.1 · Main menu — Validation

Roadmap's M5.1 text: *A focusable list: Enter vocabulary, Browse, Compile, Notebook, Inspect tree, Quit. Notebook and Inspect tree are placeholders that display their resolved path; changing the shell's working directory is out of scope.*

## Checks

1. `pytest` passes, including Textual `Pilot`-based tests:
   - Main menu shows exactly the six items, in that order.
   - *Notebook* shows the resolved `notebook_root` absolute path; *Inspect tree* shows the resolved `source_root` absolute path.
   - *Compile* triggers `compile_all()` (mocked in the test) and displays a result.
   - *Enter vocabulary*/*Browse* show their "coming in M5.2/M5.3" placeholders.
   - `Escape` from any placeholder returns to the main menu.
   - *Quit* exits the app.
2. Manual, real-terminal check:
   - `python -m idiomas` (no subcommand) launches the TUI directly, showing the main menu.
   - Every item is reachable via keyboard navigation (arrow keys + Enter, or Textual's default `OptionList` bindings).
   - Selecting *Compile* actually (re)compiles stale `.md` files under the real `source/` into real PDFs under `notebook/`, and reports "up to date" on a second run with no changes.
   - Selecting *Notebook*/*Inspect tree* shows this project's actual configured paths (whatever `.idiomas.toml` currently holds).
   - `python -m idiomas compile` and `python -m idiomas doctor` still work exactly as before (unaffected by the no-arg TUI change).
3. No regressions: full `pytest` suite (M0–M4 tests included) still passes.

## Definition of done

- All of the above pass.
- `src/idiomas/tui/` exists with `app.py`, `app.tcss`, `screens/main_menu.py`, `screens/placeholder.py`.
- `__main__.py`'s no-arg path launches the TUI; `compile`/`doctor` subcommands are untouched.
- M5.2 and M5.3 remain to be started as their own separate branches/specs.
