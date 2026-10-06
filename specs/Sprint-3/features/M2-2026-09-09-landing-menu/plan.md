# M2 · Landing menu — Plan

## 1. Landing menu screen

- Add `src/idiomas/tui/screens/landing.py` with a module-level constant listing
  the registered languages and whether each is functional, e.g.
  `LANGUAGES = [("Chinese", True), ("German", False)]`.
- `LandingMenuScreen(NavigableScreen)`: composes a `VimOptionList` with one
  `Option` per language (`"{Language} notebook"`, id `f"language:{language}"`)
  followed by `Option("Settings", id="settings")`.
- Override `action_back_or_quit` to `self.app.exit()` — this screen is now the
  app's root.
- `on_option_list_option_selected`: a functional language pushes
  `MainMenuScreen()`; a dummy language pushes `PlaceholderScreen` with a message
  naming it inert (e.g. `"German notebook is not implemented yet."`); `settings`
  pushes `SettingsScreen()`.

## 2. Settings submenu

- `SettingsScreen(NavigableScreen)` in the same module: composes a
  `VimOptionList` with `Option("Add a language", id="add_language")` and
  `Option("Remove a notebook", id="remove_notebook")`.
- Both selections push a `PlaceholderScreen` with a short dummy message. No
  override of `action_back_or_quit` — `q` falls back to `NavigableScreen`'s
  default pop, back to the landing menu.

## 3. Notebook menu changes

- `MainMenuScreen` (`src/idiomas/tui/screens/main_menu.py`): remove the
  `action_back_or_quit` override entirely, so `q` inherits the default pop
  (back to whatever pushed it — the landing menu).
- Remove the `"Quit"` option from its `VimOptionList`, the `"quit"` entry from
  its handler dispatch dict, and the now-unused `_quit` method.

## 4. Shared menu aesthetic

- Add `MenuScreen(NavigableScreen)` to `src/idiomas/tui/screens/base.py`: adds
  the CSS class `menu-screen` to itself on init. Purely a styling hook — no
  behavior beyond what `NavigableScreen` already gives.
- `app.tcss`: replace the `MainMenuScreen` / `MainMenuScreen OptionList`
  selectors with `.menu-screen` / `.menu-screen OptionList`, so the centered
  layout and bordered list are declared once.
- `MainMenuScreen`, `LandingMenuScreen`, and `SettingsScreen` all inherit from
  `MenuScreen` instead of `NavigableScreen` directly.
- Document the convention in `design.md` alongside the other `base.py`
  implementation notes.

## 5. Wire the app root

- `src/idiomas/tui/app.py`: `IdiomasApp.on_mount` pushes `LandingMenuScreen()`
  instead of `MainMenuScreen()`.

## 6. Update `design.md`

- Navigation table: the `q` row's "On the main menu, exits the app instead"
  becomes "On the landing menu, exits the app instead" (or equivalent wording
  naming the landing menu as root).
- Implementation notes: the line describing `MainMenuScreen` overriding
  `action_back_or_quit` to exit is replaced with `LandingMenuScreen` doing so;
  `MainMenuScreen` is added to the list of single-panel screens leaving the
  inherited pop behavior (alongside `PlaceholderScreen`, `SettingsScreen`).

## 7. Tests

- Split `tests/test_tui_main_menu.py`:
  - A new `tests/test_tui_landing_menu.py` covering: three items in order
    (*Chinese notebook*, *German notebook*, *Settings*); selecting *Chinese
    notebook* pushes `MainMenuScreen`; selecting *German notebook* pushes a
    `PlaceholderScreen`; selecting *Settings* pushes `SettingsScreen` with its
    two dummy items, each pushing a `PlaceholderScreen`; `q` on the landing menu
    exits the app; `q` on the Settings screen returns to the landing menu;
    `j`/`k` move the highlight.
  - `tests/test_tui_main_menu.py` keeps the notebook-menu-specific tests
    (enter vocabulary, browse, compile, notebook, inspect tree, `j`/`k`), minus
    `test_menu_shows_six_items_in_order` (→ five items, no "Quit") and
    `test_quit_exits_the_app` (removed — no more "Quit" item), and adds a test
    that `q` on the notebook menu returns to `LandingMenuScreen` rather than
    exiting the app.
  - `IdiomasApp`-level fixtures in both files start the app at the landing
    menu now, so tests reaching notebook-menu screens select the language
    entry first.
