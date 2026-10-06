# M7 · Add a language — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The registry (§1)

- Add Italian, French, English and Spanish to `languages.LANGUAGES`, in that
  order after German, as `ALPHABETICAL` entries with the hints in §1. Add the
  Linux hints to German.
- Add the new layouts to the macOS and Linux `DISPLAY_NAMES` tables.
- Update the module docstrings that still say "Chinese and German".
- Tests (`test_languages.py`): six entries in order, each kind, all
  functional; no language's hints match another language's source IDs in
  either display-name table; `preselect_language` picks the Italian layout
  for Italian from a mixed source list.

## 2. `doctor` is language-aware (§2)

- `Check.needed_for`, `Check.install`; the CJK pair becomes
  `required=False` with `needed_for` derived from the kinds.
- `doctor.missing_for(checks, languages)`.
- A shared label helper (`required` / `optional` / the joined `needed_for`)
  used by the CLI and the wizard's `_checks_text`/`_pending_checks_text`.
- `idiomas doctor` reads the config if present and exits on `missing_for`.
- Tests (`test_doctor.py`, `test_main.py`): the CJK pair's `needed_for` is
  `("Chinese",)`; `missing_for` with `["German"]` ignores a missing xeCJK,
  with `["Chinese"]` returns it, and always returns a missing required check;
  the CLI exits 0 for a German-only config without xeCJK and 1 for a Chinese
  one; labels.

## 3. The install offer (§5)

- A shared helper (a new `tui/screens/dependencies.py`) that takes the app,
  the language names and the missing checks, and calls back with whether the
  dependencies are now satisfied. It covers no command, the `ConfirmDialog`,
  suspending, running each command without a shell, the Enter pause, the
  recheck and `OSError`. It also provides one function that words the
  refusal line, used by both callers.
- Tests: no-command refuses without a dialog; declining refuses; accepting
  runs exactly the listed commands (with `subprocess.run` and `doctor.run`
  faked) and succeeds when the recheck is clean, or fails and names what is
  still missing; an `OSError` is reported, not raised.

## 4. The wizard (§3)

- Step 1 blocks only on `required`.
- Step 3: six one-row (`compact`) checkboxes from the registry, and on *Next*
  `missing_for` → the offer from group 3 → proceed or the refusal line.
- Tests (`test_tui_wizard.py`): six checkboxes in registry order; step 1's
  *Next* works with xeCJK missing; German-only *Next* proceeds with xeCJK
  missing; Chinese with xeCJK missing shows the dialog, and declining stays on
  step 3 with the refusal line; accepting with a clean recheck proceeds; a
  full run choosing Italian writes `tree-Italian/{Vocabulary,Grammar}` and the
  config.

## 5. Settings › Add a language (§4)

- `SettingsScreen`'s option description and dispatch; the "Every supported
  language is already added." placeholder.
- `AddLanguageScreen(MenuScreen)` and `AddLanguageFormScreen(FormScreen)`.
- The write sequence: offer → `ensure_tree` → save a copy → mutate → pop two
  → notify.
- Resume-time rebuild of the landing menu, the Input methods picker and the
  *Add a language* picker from the running config, keeping the highlighted
  id.
- Tests (`test_tui_settings.py`, `test_tui_landing_menu.py`): the picker lists
  exactly the unregistered languages; all-registered → placeholder; adding
  Italian writes the folder and the config, appends to the running config,
  returns to Settings with the notification, and the landing menu then lists
  *Italian notebook* before *Settings* and opens the notebook menu; an
  existing `tree-Italian` with a file in it is adopted untouched; a failing
  `save_config` shows the error and leaves `app.config` unchanged; adding
  Chinese with xeCJK missing goes through the offer; the Input methods picker
  lists the new language.

## 6. Every alphabetical language works on arrival (§6)

- A parametrised test over Italian, French, English and Spanish: Entry adds a
  word against a temp tree, the file parses back, and a vocabulary and a
  grammar deck render (and compile, in the real-pandoc tier), with accented
  words (`perché`, `garçon`, `niño`).

## 7. Docs (§7) and the full suite

- `design.md`, `stack.md`, `README.md` as in §7.
- `pytest` in full.
