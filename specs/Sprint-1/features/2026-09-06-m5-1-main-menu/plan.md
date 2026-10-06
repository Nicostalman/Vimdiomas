# M5.1 · Main menu — Plan

## 1. `__main__.py`: config-before-TUI, no-arg launches the app

- Add a `_tui()` function: calls `load_or_prompt_config(PROJECT_ROOT)`, then constructs and runs `IdiomasApp(config)`.
- `main()`: when `args.command` is `None` (no subcommand), call `_tui()` instead of returning immediately. `compile`/`doctor` branches unchanged.

## 2. `tui/` package skeleton

- `src/idiomas/tui/__init__.py`, `src/idiomas/tui/app.tcss` (minimal stylesheet: menu list styling, placeholder screen styling).
- `src/idiomas/tui/app.py`: `IdiomasApp(App)` — takes `config: Config` in `__init__`, stores it, `CSS_PATH = "app.tcss"`, `SCREENS`/`on_mount` pushes `MainMenuScreen`.

## 3. `PlaceholderScreen`

- `src/idiomas/tui/screens/placeholder.py`: `PlaceholderScreen(Screen)` taking a `message: str` in `__init__`, rendering it centered (a `Static`), bound to `Escape` -> `app.pop_screen()`.

## 4. `MainMenuScreen`

- `src/idiomas/tui/screens/main_menu.py`: `MainMenuScreen(Screen)` with an `OptionList` of the six items in roadmap order.
- On selection:
  - *Enter vocabulary* -> push `PlaceholderScreen("Entry screen coming in M5.2")`.
  - *Browse* -> push `PlaceholderScreen("Browse screen coming in M5.3")`.
  - *Compile* -> call `compile_all(app.config.source_root, app.config.notebook_root)`; push `PlaceholderScreen(...)` reporting either the list of compiled files or "Everything is up to date."
  - *Notebook* -> push `PlaceholderScreen(str(app.config.notebook_root))`.
  - *Inspect tree* -> push `PlaceholderScreen(str(app.config.source_root))`.
  - *Quit* -> `self.app.exit()`.

## 5. Tests

- `tests/test_tui_main_menu.py` using Textual's `Pilot` (`async with app.run_test() as pilot:`):
  - Main menu renders exactly the six items, in the roadmap's exact order.
  - Selecting *Notebook* shows the resolved `notebook_root` path; selecting *Inspect tree* shows the resolved `source_root` path.
  - Selecting *Compile* against a fixture source/notebook pair actually calls `compile_all` (mock it to avoid a real pandoc/xelatex invocation in this test — that's already covered by M4's own integration test) and shows its result.
  - Selecting *Enter vocabulary*/*Browse* shows the expected "coming in M5.2/M5.3" placeholder.
  - *Escape* from a placeholder screen returns to the main menu.
  - Selecting *Quit* exits the app (`pilot.app.is_running` becomes `False`, or the app's exit code/return value is as expected).
- Manual verification: run `python -m idiomas` for real in a terminal, confirm the menu looks right, navigate every item, confirm Compile actually produces/updates PDFs, confirm Quit cleanly returns to the shell.
