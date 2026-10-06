# M4 · The notebook menu — plan

The task groups are ordered so that each one depends only on the groups
before it. Group 1 is the shared machinery, groups 2–4 are the menus, and
group 5 is the docs.

## 1. `MenuOption`, `MenuLegend`, and `MenuScreen`

- `panels.py`: add `MenuOption(Option)` with a required `description: str`,
  stored on the instance. Its `prompt`/`id` handling is otherwise
  `Option`'s own.
- `base.py`: add `MenuLegend(FooterHint)`, which adds the `menu-legend`
  class and has `can_focus = False`.
- `MenuScreen.compose()`: yield the `VimOptionList` and then a `MenuLegend`
  (`id="menu-legend"`), both inside the flat backpanel. When an option is not
  a `MenuOption`, raise `TypeError` naming the menu class. That is the
  "description is required" guarantee.
- `MenuScreen.on_option_list_option_highlighted`: update the legend with
  `literal(option.description)`. On mount, show the highlighted option's
  description, or the first option's if nothing is highlighted yet.
- `app.tcss`: style `.menu-legend` with `width: 40`, `height: 2`,
  `padding: 0 2` (lining up with the list's horizontal padding),
  `margin: 1 0 0 0` (a blank row between the list and the legend, on top of
  the list's own bottom padding; dev, 2026-10-01), `text-style: italic`. The muted colour comes from `.footer-hint`.
  `MenuScreen Backpanel`'s `align: center middle` keeps the list and the
  legend centred as one column.
- Tests (new `tests/test_tui_menu_legend.py`, against a small test-only
  `MenuScreen` subclass):
  - the legend shows the first option's description on open;
  - `j` changes it to the second option's description, and `k` changes it
    back;
  - the legend's region height is 2 whether the description takes one line
    or two, and the list's region doesn't move between the two;
  - a plain `Option` in `menu_options()` raises `TypeError`;
  - a description containing `[b]x[/b]` is shown verbatim;
  - the legend never takes focus, and `tab` still does nothing on a menu.

## 2. The notebook menu

- `main_menu.py`: change `menu_options()` to four `MenuOption`s in this
  order: Enter vocabulary, Inspect tree, Browse, Compile. Each gets its
  description from `requirements.md` §3.
- Remove `compile_force` from the options and the handler map, along with
  `_compile_force`. `_run_compile` loses its `force` parameter and calls
  `compile_all(..., force=False)`. The `__main__.py` CLI is untouched.
- Tests (`test_tui_main_menu.py`):
  - `test_menu_shows_five_items_in_order` becomes four, in the new order;
  - delete `test_compile_force_calls_compile_all_with_force`, and add a test
    that the menu's Compile calls `compile_all` with `force=False`;
  - check each option's legend text as it is highlighted;
  - **done-when, menu level:** compile a temp tree once through the menu
    (with `_run_pandoc` faked, as the compile tests do). Then rewrite a
    source on disk outside autocompile, as Neovim would, and Compile again:
    the results screen lists that file as compiled. A third Compile reports
    "Everything is up to date."

## 3. Landing menu

- `landing.py`: change the options to `MenuOption`s. A language in
  `FUNCTIONAL_LANGUAGES` gets "Add words, explore and compile your
  *&lt;Language&gt;* notes.", any other language gets "Not available yet.",
  and Settings gets its description.
- Tests (`test_tui_landing_menu.py`): the legend for Chinese, German
  (inert) and Settings, each as it is highlighted.

## 4. Settings and the input-methods picker

- `settings.py`: change `SettingsScreen` and `InputMethodLanguagesScreen` to
  `MenuOption`s, with the descriptions from `requirements.md` §3.
- Tests (`test_tui_settings.py`): each Settings option's legend, and the
  picker's legend for a language.

## 5. Cross-menu check and docs

- One test that walks all four menus, highlights every option in turn, and
  checks that the legend is non-empty and fits in two lines at 36 columns
  (the legend's 40 minus its padding). This is the check that a description
  longer than two lines fails.
- `design.md`: add a *Menu legend* subsection under *Flat menus*, per
  `requirements.md` §4.
- Run the full suite with `.venv/bin/python -m pytest -q`.

## Implementation notes

- `test_tui_panels.py`'s `_MenuHostScreen` fixture built plain `Option`s, which
  `MenuScreen` now refuses. It builds `MenuOption`s instead.
- The test-only menu app in `test_tui_menu_legend.py` loads the real
  `app.tcss` (`CSS_PATH = IdiomasApp.CSS_PATH`); without it the legend's
  fixed height is not applied and the layout tests would measure nothing.
- The cross-menu check (§5) lives in `test_tui_menu_legend.py`.
