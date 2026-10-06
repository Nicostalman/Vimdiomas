# M2 · Landing menu — Validation

Grounded in the roadmap's done-when condition, made concrete.

## Automated

Run `pytest` (or the project's usual test command). All of the following must
pass:

- `tests/test_tui_landing_menu.py`:
  - Launching `IdiomasApp` lands on `LandingMenuScreen` showing exactly
    *Chinese notebook*, *German notebook*, *Settings*, in that order.
  - Selecting *Chinese notebook* pushes `MainMenuScreen`.
  - Selecting *German notebook* pushes a `PlaceholderScreen` (dummy — nothing
    real happens).
  - Selecting *Settings* pushes `SettingsScreen` showing *Add a language* and
    *Remove a notebook*; selecting either pushes a `PlaceholderScreen`.
  - `q` on the landing menu exits the app (`pilot.app.is_running` is `False`).
  - `q` on the Settings screen returns to `LandingMenuScreen`.
  - `j`/`k` move the highlight on the landing menu.
- `tests/test_tui_main_menu.py` (notebook menu):
  - The notebook menu shows five items, no "Quit": *Enter vocabulary*,
    *Browse*, *Compile*, *Notebook*, *Inspect tree*.
  - `q` on the notebook menu returns to `LandingMenuScreen`, not to a placeholder
    and not exiting the app.
  - Existing enter-vocabulary/browse/compile/notebook/inspect-tree/`j`/`k`
    behavior is unchanged.
- The full suite (`pytest`) passes with no regressions elsewhere.

## Manual (dev sign-off)

- Launching the app lands on the landing menu, not the notebook menu.
- *Chinese notebook* reaches the familiar notebook menu; from there, `q` goes
  back to the landing menu (not out of the app).
- *German notebook* is visibly present and does nothing but show it's not
  implemented.
- *Settings* opens a submenu with *Add a language* and *Remove a notebook*,
  both visibly present and inert.
- `q` on the landing menu exits the app.
- `specs/current/design.md` reads correctly: the landing menu is documented as
  the app's root screen.

## Done when

Matches the roadmap: launching the app lands on the language menu; *Chinese
notebook* reaches the notebook menu and `q` comes back; *German notebook* and
every *Settings* item are visibly present and do nothing; `q` on the landing
menu exits; and `design.md` reflects the new screen order. Closed only when the
dev confirms manual testing above, not when automated tests pass on their own.
