# M5 · Installation wizard — plan

## 1. Config writing

- `config.py`: add `save_config(config: Config) -> None`.
  - Serializes `Config` to the TOML shape `load_config()` already reads
    (`user_name`, `root`, `[[languages]]` tables with just `name` — M5 never
    populates `hanzi_input_method`/`translation_input_method`, so they're
    omitted rather than written empty, matching how `load_config()` already
    defaults missing keys to `""`).
  - No TOML-writing dependency exists in the project (`tomllib` is
    read-only) and the schema is small and fixed-shape, so hand-roll the
    serialization (a few `f"key = {value!r}"`-style lines) rather than
    adding a dependency.
  - Atomic write: build the text, write it to a temp file in
    `CONFIG_PATH.parent`, then `os.replace()` onto `CONFIG_PATH`. Create
    `CONFIG_PATH.parent` first if missing (`mkdir(parents=True,
    exist_ok=True)`).
  - Update the module docstring: it no longer "only reads" the config.
- `tests/test_config.py`: add cases for `save_config` — round-trips through
  `load_config()`, creates missing parent directories, and doesn't clobber
  the directory's other files. Cover a `Config` with an empty `languages`
  list and one with several.

## 2. Root-folder validation

- New helper in `config.py` (or a small module-level function next to
  `save_config`, since it's plain `pathlib`/`importlib` logic with no OS
  branching — not `idiomas.platform`'s concern): `validate_tree_root(path:
  Path) -> str | None`, returning `None` if the path is acceptable or an
  error message if not.
  - Not inside the installed package: compare against
    `importlib.resources.files("idiomas")` (or `Path(idiomas.__file__).parent`)
    — reject if the candidate path is that directory or a descendant of it.
  - Writable: if the path exists, check it's a directory and
    `os.access(path, os.W_OK)`; if it doesn't exist, walk up to the nearest
    existing ancestor and check that ancestor is writable.
- `tests/test_config.py`: cover both rejection cases and the accepting case,
  using `tmp_path`.

## 3. Wizard screens

**`doctor.py` gains one field, added mid-milestone:** `Check.url: str =
""`. Dev's hands-on testing surfaced that a failing check's full
`message` (e.g. "pandoc not found: install it (e.g. \`brew install
pandoc\`)") gets cut off at the wizard panel's 60-column width — the
actual answer to "what happens when a dependency is missing" turned out
to be a display bug, not just a question. Five of `run()`'s six checks
get a `url` (pandoc, xelatex, xeCJK, macism, nvim, each pointing at its
GitHub repo — xelatex/xeCJK link to their upstream source mirrors, not a
single canonical TeX Live repo, since neither ships as one); Heiti SC
doesn't, since it's bundled with macOS rather than installed from
anywhere. `message` is untouched and still what `idiomas doctor`'s CLI
output prints — `url` is wizard-display-only.

New module `src/idiomas/tui/screens/wizard.py`, four `PanelScreen`
subclasses, one per step, each with a single `Panel` holding its content —
following the existing panel-model conventions (focus-on-entry via
`PanelScreen.on_mount`, `esc` bubbling, `q` via `action_back_or_quit`).

**Advancing via a `Button`, not a raw keybinding.** `Panel` already claims
`enter`/`tab` (focus-content) whenever the panel itself has focus, and
`Input` consumes `enter` itself (`Input.Submitted`) whenever a field has
focus — so a screen-level `enter` binding for "advance" is unreachable from
either state, and a plain letter key (`n`) would just be typed into a
focused `TextField`/`Checkbox` instead of bubbling to an action. Every step
instead follows `EntryScreen`'s own established pattern (its `Create`
button): a real `Button` in the panel's normal tab order, wired via
`@on(Button.Pressed, ...)`, with a matching `@on(Input.Submitted, ...)` on
any text field for the fields that have one, calling the same validation
method either way.

**`tab` needs its own override, on every step — a bug caught in dev
hands-on testing, not anticipated up front.** Every step's panel holds more
than one focusable widget (a field/checkboxes plus a button), and both
`Panel` and `Backpanel` are `can_focus=True`; left to Textual's default
focus-chain cycling, `tab` visits them as extra stops (exactly the
`BrowseScreen`/`EntryScreen` precedent already documents — see
`browse.py`'s `action_next_field` docstring). A shared `_WizardStep`
base class (`PanelScreen` subclass, in `wizard.py`) gives every step the
same fix once: a `content_ids()` method naming that step's own focusable
widgets in tab order, and one `action_next_field` cycling only through
them. `DependenciesScreen`/`NameScreen`/`LanguagesScreen`/
`TreeLocationScreen` all subclass `_WizardStep` instead of `PanelScreen`
directly.

**Every screen carries a bold title (`.wizard-title`) and a plain-language
prompt (`.wizard-prompt`, `$text-muted`) above its content** — two `Static`
widgets at the top of the panel, added after dev hands-on feedback that a
bare field/checklist with no explanation read as unclear.

- **`DependenciesScreen`**
  - Title "Dependencies", prompt "Checking that everything Idiomas needs is
    installed:".
  - On mount, runs `doctor.run()` and renders the checks as one `Static`
    inside the panel, built from a `rich.text.Text` (`_checks_text()`) —
    not a plain string — so each line can carry its own color: `dim` for
    the `[required]`/`[optional]` + name prefix, `green` for `ok`, `red`
    for `missing` (plus ` <-- ` and `check.url`, when the check has one —
    not `check.message`, which can run long enough to be cut off at the
    panel's width; confirmed by hands-on testing with a real missing
    dependency, not just anticipated). Fixed-width format fields
    (`f"[{label:>8}] {name:<10} "`) keep every status starting in the same
    column regardless of check-name length. `Text.append(text,
    style=...)` is used instead of Rich markup strings, so `check.url`
    (which can contain characters Rich markup would otherwise need
    escaped) never needs escaping. This is a display, not something the
    user picks from, so it doesn't need `VimOptionList`.
  - `Recheck` and `Next` buttons. `Next` blocks (inline `Static` error,
    `.wizard-error`) if any required check still fails. `Recheck` disables
    itself and runs `doctor.run()` on a background thread
    (`self.app.run_worker(self._recheck_worker, thread=True, group=
    "doctor-recheck")`) rather than on the UI thread. While it runs, the
    **same** `#dependencies-list` `Static` is re-rendered every
    `SPINNER_INTERVAL = 0.1`s (`self.set_interval`) via
    `_pending_checks_text()` — the same aligned layout as `_checks_text()`
    but with every status column replaced by a spinner frame
    (`SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"`) — rather than swapping in a separate
    `LoadingIndicator` widget: dev's explicit follow-up feedback after
    seeing the first version ("it should be inline for each dependency"),
    not something anticipated up front. `_recheck_worker` floors the
    wall-clock time at `MIN_RECHECK_SECONDS = 0.4` (`time.sleep` for the
    remainder) so the animation is visible even though `doctor.run()`
    alone usually finishes in milliseconds, then `call_from_thread`s back
    to stop the interval timer, render the final `_checks_text()`, and
    re-enable the button.
  - `action_back_or_quit` is **overridden unconditionally** (not gated on
    a screen-stack length check — see Task Group 4 for why that check is
    wrong): `q` here always pushes a `ConfirmDialog` ("Quit the
    installation wizard? Nothing will be saved.") and only calls
    `self.app.exit(None)` if confirmed. Declining leaves step 1 exactly as
    it was. Every other step's `q` is `PanelScreen`'s unmodified
    behaviour: pops back to the previous step, no confirmation (only
    aborting the whole wizard loses enough to warrant asking).
- **`NameScreen`**
  - Title "Your name", prompt "What should Idiomas call you?".
  - One `Panel`, one `TextField` + `Next` `Button`.
  - Submitting (`Input.Submitted` or the button) does nothing on an empty/
    whitespace name (M3's pattern, shown inline via `.wizard-error`);
    otherwise stores the name on the owning `WizardApp` (see Task Group 4)
    and pushes `LanguagesScreen`.
- **`LanguagesScreen`**
  - Title "Languages", prompt "Which languages would you like to set up?
    Choose at least one.".
  - One `Panel` holding two `EnterOnlyCheckbox` widgets (Chinese, German)
    + `Next` `Button` — the simplest fit for "any number, at least one"
    from a fixed short list; no new shared *menu* class needed since
    nothing else in the app needs a multi-select yet (considered and
    deferred — see `notes-sprint-4.md`'s Postponed table). Focus moves
    between them with the panel's normal tab order.
  - `EnterOnlyCheckbox(Checkbox)`: overrides `space` to a no-op (`Binding
    ("space", "nothing", ...)`), leaving `enter` as the only way to
    toggle — dev's request, one unambiguous key instead of two doing the
    same thing. Follows the same override pattern `NoShiftArrowsTree`
    already established for silencing part of a widget's inherited
    `BINDINGS` (Textual resolves a subclass's binding for a given key over
    its parent's rather than replacing the whole list — verified
    empirically with a standalone `run_test()` check before wiring it in).
  - `.wizard-panel Checkbox { width: 20; }` in `app.tcss`: both checkboxes
    render at the same width regardless of "Chinese" vs "German"'s
    slightly different label lengths — dev's request.
  - `Next` refuses (inline error) with nothing checked.
- **`TreeLocationScreen`**
  - Title "Tree location", prompt "Where should your language trees
    live?".
  - One `Panel`, one `TextField` pre-filled with
    `str(Path.home() / "Documents" / "Idiomas")`, + `Finish` `Button`.
  - Submitting runs `validate_tree_root`; on failure, shows the message
    inline and stays; on success, creates the root and every selected
    language's `tree-<Language>` folder (`Path.mkdir(parents=True,
    exist_ok=True)` —
    already a no-op on an existing folder, satisfying "never overwritten"),
    assembles the `Config`, calls `save_config`, and calls
    `self.app.exit(config)`.
  - `FooterHint` for `enter` (finish) / `q` (back to `LanguagesScreen`).
- Each screen reads/writes its answer directly on the owning `WizardApp`
  instance (`self.app.user_name`, `self.app.languages`) — the same way
  `MainMenuScreen` already reaches `self.app.config` — rather than passing
  values through screen constructors, since steps both push forward and
  pop back to the same instance. The project has no `mypy`/type-checking
  step in CI, so no cast is needed for `self.app`'s narrower type.

## 4. `WizardApp`

- New class in `wizard.py` (co-located with the screens it owns, unlike
  `IdiomasApp`, which lives alone in `tui/app.py` because it owns an entire
  screens package): `class WizardApp(App[Config | None])`.
  - `__init__`: initializes the in-progress answer fields `user_name: str =
    ""` and `languages: list[str] = []` that each step reads and writes.
  - `on_mount`: `self.push_screen(DependenciesScreen())`.
  - **A real bug, caught in dev hands-on testing, not just a spike
    outcome:** the first pass gated `DependenciesScreen.action_back_or_quit`
    on `len(self.app.screen_stack) <= 1`, reasoning that with only one
    screen pushed, `PanelScreen`'s default `self.app.pop_screen()` would
    raise `ScreenStackError` (nothing to pop back to) and so needed a
    guard. That length check is wrong: **every** Textual `App` carries its
    own implicit default screen underneath any screen the app pushes, so
    `len(self.app.screen_stack)` is 2 (default + `DependenciesScreen`)
    even at step 1, and the guard never fired — verified directly
    (`app.screen_stack` printed `[Screen(id='_default'),
    DependenciesScreen()]`). `q` was silently falling through to the
    unconditional `pop_screen()`, landing on that empty default screen: an
    unresponsive blank app, not an aborted wizard — exactly the "exits to
    a black screen" the dev reported. The fix: `DependenciesScreen` is
    hardcoded as always-the-first-step, so its `action_back_or_quit` is
    unconditional — no stack-length check at all — and always shows the
    `ConfirmDialog` abort prompt (see Task Group 3) rather than ever
    popping. No other screen needs an override: popping back to a
    previous *wizard* step (which is genuinely on the stack, not the
    implicit default) is exactly `PanelScreen`'s existing behaviour.

## 5. Wiring into `__main__.py`

- `_run_wizard()`: runs `WizardApp()`, and starts `IdiomasApp` with its
  result if it finished (`None` on abort just returns).
- `_tui()`:
  ```python
  def _tui() -> None:
      if not CONFIG_PATH.exists():
          _run_wizard()
          return
      IdiomasApp(load_config()).run()
  ```
- `main()`'s dev-only `wizard` escape hatch (see `requirements.md`'s
  Decisions) is checked **before** `argparse` runs at all:
  ```python
  if sys.argv[1:2] == ["wizard"]:
      _run_wizard()
      return
  ```
  Not registered as an `argparse` subparser — `help=argparse.SUPPRESS` on
  a subparser still renders a `wizard  ==SUPPRESS==` row and leaves
  `wizard` in the usage line's choices (`{compile,doctor,wizard}`),
  verified empirically. Checking `sys.argv` directly keeps it fully
  invisible to `idiomas --help`.
- Import `WizardApp` from `idiomas.tui.screens.wizard`.
- `_compile()`, `_doctor()`, `NO_CONFIG_MESSAGE`, and the
  `ConfigNotFoundError` handling in `main()` are otherwise untouched.

## 6. App-wide fixes surfaced by M5's own hands-on testing

Two bugs the dev found while testing the wizard turned out not to be
wizard-specific — both live in shared code (`panels.py`, `app.tcss`) and
affect every screen, not just M5's four.

- **`Backpanel`'s border is always accent** (`panels.py`, `app.tcss`):
  `.backpanel { border: round $accent; }` unconditionally, replacing the
  old `.backpanel { border: round $panel; } .backpanel:focus { border:
  round $accent; }` pair. `.backpanel-flat:focus-within { border: round
  $accent; }` (the menu variant) is removed too — now redundant, since
  `.backpanel`'s own rule already always applies. Update `Backpanel`'s
  docstring, `MenuScreen`'s docstring, and `design.md`'s *The focus look*
  and *Flat menus* sections to match — this is a standing convention
  change, not a one-off tweak.
- **`MenuScreen` binds `tab` to a no-op** (`panels.py`): without it,
  Textual's default focus-chain cycling moves focus from the menu's
  `OptionList` (the only focusable content in a flat screen) onto the
  `Backpanel` itself, since it's also `can_focus=True` and part of that
  chain — visibly defocusing the list. Same bug class `_WizardStep`'s
  `content_ids()`/`action_next_field` already guards against (Task Group
  3); here there's only one widget, so the fix is simply "do nothing on
  tab" rather than cycling anywhere.

## 7. Tests

- `tests/test_tui_wizard.py` (new), using the same Textual `run_test()`
  pattern the existing `test_tui_*` files use:
  - Dependencies step: renders `doctor.run()`'s checks; blocks `Next` with
    a failing required check (monkeypatch `doctor.run`); recheck refreshes
    after the mocked result changes; proceeds when all required checks
    pass.
  - Name step: empty/whitespace name refused; a real name advances and is
    carried into the final `Config`.
  - Languages step: zero selected refused; one or both selected advances
    and is reflected in the final `Config.languages`.
  - Tree location step: rejects a path inside the package; rejects an
    unwritable path; accepts a good path, creates the root and every
    selected language's `tree-<Language>` folder (including German), does
    **not** touch an already-existing tree folder's contents, calls
    `save_config`, and the app exits with the assembled `Config`.
  - Back navigation: `q` from `NameScreen` returns to `DependenciesScreen`
    with its state intact. `q` from `DependenciesScreen` pushes the
    `ConfirmDialog` — declining (`n`) leaves the app running on
    `DependenciesScreen`; confirming (`y`) exits with `None` and no file
    appears at `CONFIG_PATH` (`tmp_path`-patched).
  - `tab` cycling: repeated `tab` presses on `DependenciesScreen` only ever
    land on its own buttons, never on a `Panel` or `Backpanel` instance
    (asserted directly against those classes); same check on
    `TreeLocationScreen`'s field/button pair.
  - `_checks_text()`: a failing check's status text carries the `red`
    style, an "ok" one carries `green` (checked via the returned `Text`'s
    `.spans`, not by parsing ANSI codes); every line's status starts at
    the same column regardless of check-name length (alignment).
  - Languages step: `space` on a focused checkbox leaves it unchanged;
    `enter` toggles it (regression test for `EnterOnlyCheckbox`).
  - Recheck: clicking it shows `#dependencies-loading` and disables
    `#recheck-button` immediately, and both revert once
    `app.workers.wait_for_complete()` settles (`MIN_RECHECK_SECONDS`
    monkeypatched to a small positive value just for this test, so the
    intermediate state is observable rather than racing past it; every
    other test patches it to `0` via an autouse fixture, to keep the
    suite fast).
  - Full happy path end to end: drive all four steps, assert the file at
    (patched) `CONFIG_PATH` round-trips through `load_config()` into the
    same `Config` the app exited with.
- `tests/test_tui_panels.py`: a new `_MenuHostScreen(MenuScreen)` fixture
  confirms `tab` leaves focus on the `OptionList` rather than moving it to
  `Backpanel` (Task Group 6's `MenuScreen` fix). No test asserts on border
  *color* anywhere in this file or `test_tui_landing_menu.py`/
  `test_tui_main_menu.py` — the always-accent `Backpanel` change (Task
  Group 6) has nothing to update there.
- `tests/test_main.py` (new): `_tui()`'s branching — no config runs the
  wizard and feeds its result into `IdiomasApp`; an aborted wizard (`None`)
  starts nothing; an existing config skips the wizard entirely.
  `_run_wizard()` opens the wizard even with a config present, and an
  abort from it leaves that config file untouched. `main()`'s `wizard`
  escape hatch dispatches to `_run_wizard()` when `sys.argv` is patched to
  `["idiomas", "wizard"]`, and a real subprocess run of `idiomas --help`
  never mentions "wizard" anywhere in stdout/stderr. `WizardApp`/
  `IdiomasApp` are monkeypatched with lightweight fakes so this doesn't
  drive a real Textual app (except the `--help` subprocess check, which
  runs the real CLI).
- `tests/test_config.py`: covered in Task Group 1–2.
- `tests/test_doctor.py`: new cases for `Check.url` — every check but
  Heiti SC carries one; pandoc's points at its GitHub repo. `test_tui_panels.py`
  (the M1/M2 panel tests) needed one addition of its own for the
  `MenuScreen` `tab` fix (Task Group 6), but the wizard is otherwise only
  a consumer of those classes, not a change to them.
