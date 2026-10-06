# M8 · Remove a language — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The compile cache (§3)

- `compile.forget_tree(tree_root)`: drop the cache keys under `tree_root`,
  and save only if something changed.
- Tests (`test_compile.py`): keys under the root are dropped, keys under a
  sibling `tree-Chinese` and a prefix-sharing `tree-Chinese2` are kept, and a
  missing cache file is a no-op.

## 2. Settings › Remove a language (§1, §2)

- `SettingsScreen`: the option is relabelled *Remove a language*, with its
  description and `id="remove_language"`, and the dispatch goes to the
  picker or the "no language to remove" placeholder.
- `RemoveLanguageScreen(MenuScreen)` and the flow: the first dialog, the
  conditional second dialog with the file count, save a copy, mutate, the
  optional `rmtree` + `forget_tree`, pop, and the notification.
- Tests (`test_tui_settings.py`, replacing the placeholder test):
  - The Settings labels read *Input methods / Add a language / Remove a
    language*.
  - The picker lists the registered languages in config order.
  - `n` on the first dialog changes nothing.
  - `y` then `n` removes the language from the saved and the running config,
    keeps the folder and its files, keeps the cache entries, and lands on
    Settings with "… Its notes are still in …".
  - `y` then `y` deletes the folder, purges its cache entries and leaves
    Chinese's alone.
  - No folder on disk means a single dialog, then "Italian removed."
  - A failing `save_config` leaves `app.config`, the file and the folder
    unchanged.
  - A failing `rmtree` still removes the language and reports the folder.
  - The file count wording is right for 0, 1 and N files.

## 3. Without relaunching, and zero languages (§4, §5)

- The landing menu's *Settings* description when no language is registered.
- The *Input methods* placeholder when none is registered.
- Tests (`test_tui_settings.py`, `test_tui_landing_menu.py`, `test_main.py`):
  - After removing German, the landing menu no longer lists it, and the
    Input methods picker doesn't either.
  - Removing every language leaves the landing menu with *Settings* only,
    carrying the new description, and both pickers show their placeholders.
  - Adding one back then restores the landing entry.
  - Remove → re-add: a kept folder with a file in it reappears untouched, and
    the language opens its notebook menu.
  - `idiomas compile` and `idiomas doctor` with an empty language list exit
    0.

## 4. Docs (§6) and the full suite

- `design.md`, `README.md`, `stack.md`, and the `settings.py` docstring, as in
  §6.
- `pytest` in full.
