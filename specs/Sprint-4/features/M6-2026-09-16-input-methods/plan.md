# M6 · Input methods — plan

Task groups in dependency order: the platform layer first (it has no UI and
everything else reads from it), then the config shape, then the shared widget,
then the two surfaces built on it, then the consumer, then docs.

## 1. Platform layer: list the enabled input sources

1. Add `InputSource` (`id`, `name`) as a frozen dataclass in
   `idiomas/platform/__init__.py`, alongside the dispatch. It is the platform
   boundary's own type, so the macOS module and the non-macOS no-op agree on it.
2. `idiomas/platform/macos.py`: `list_input_sources()`.
   - `subprocess.run(["defaults", "export", "com.apple.HIToolbox", "-"], capture_output=True, check=True)`,
     parsed with `plistlib.loads`. Return `[]` on `FileNotFoundError`,
     `CalledProcessError`, or an unparseable payload — the same
     never-crash posture `switch_input_source` already has.
   - Map `AppleEnabledInputSources` per `requirements.md`'s table: keyboard
     layouts get the `com.apple.keylayout.` prefix, input modes are used
     verbatim, a `Keyboard Input Method` container is kept only when no
     `Input Mode` entry shares its `Bundle ID`, and `Non Keyboard Input Method`
     is dropped.
   - Preserve the OS's own order; drop duplicate IDs.
3. Display names: a module-level table of the common sources (`SCIM.ITABC` →
   "Pinyin – Simplified", `keylayout.USInternational-PC` → "U.S. International –
   PC", `keylayout.US`, `keylayout.ABC`, `keylayout.German`, `keylayout.British`,
   `keylayout.Spanish`, the TCIM Pinyin/Cangjie/Zhuyin modes), falling back to
   the ID's last dotted segment. Cosmetic only: the raw ID is shown next to the
   name everywhere, so a missing table entry costs nothing.
4. Non-macOS branch in `platform/__init__.py`: `list_input_sources()` returns
   `[]`. Add it to `__all__`.
5. Tests (`tests/test_platform.py`): the mapping, driven by a plist fixture
   built in the test (all five `InputSourceKind` values, a multi-mode IME with
   both container and mode present, a mode-less IME, a duplicate); the empty
   return when `defaults` is missing; the empty return on unparseable output.

## 2. Config: rename the field, carry it to the notebook

1. `LanguageConfig.hanzi_input_method` → `input_method`, in the dataclass,
   `load_config`, and `_toml_lines`. No fallback read of the old key
   (`requirements.md` · *Config schema*).
2. `NotebookConfig` gains `input_method: str = ""` and
   `translation_input_method: str = ""` — Entry already receives a
   `NotebookConfig` and nothing else, so this is how the IDs reach it.
3. `Config.language(name) -> LanguageConfig | None`, so the menu and Settings
   don't both hand-roll the lookup.
4. `main_menu._notebook_config()` fills the two new fields from
   `self.app.config.language(self.language)`.
5. Update `tests/test_config.py` for the rename and add one for
   `Config.language`.
6. Rewrite the dev's own `~/.config/idiomas/config.toml` key in place (not a
   code change; do it as part of the milestone so their install keeps working).

## 3. `SelectField`

In `idiomas/tui/screens/panels.py`, beside `TextField`:

1. `SelectField(Vertical)`, `can_focus = True`, built from a label, a list of
   `(value, label)` choices and an initial value. Composes a `Static` showing
   `<label>: <current>` and a collapsed `_SelectList(VimOptionList)` below it
   (`display = False`).
2. `enter` on the focused field expands the list and focuses it; guarded on
   `self.has_focus` with `SkipAction` on failure, exactly as `Panel`'s own
   bindings are, so a screen-level `tab`/`enter` binding still sees the key when
   the field isn't focused.
3. `_SelectList`: `escape` collapses and returns focus to the field without
   changing the value; `OptionSelected` sets the value, collapses, and returns
   focus to the field. Its `escape` must not bubble to the containing `Panel` —
   this is the *content → field* rung of `design.md`'s nesting ladder, and only
   the field's own `escape` (inherited, unbound) climbs to the panel.
4. `value` property (read/write); writing it re-renders the display line and
   moves the list's highlight.
5. Collapse on blur, so tabbing away never leaves an orphaned open list.
   Deferred with `call_after_refresh` and checked against `screen.focused`:
   focusing the list is itself a blur of the field, so where focus landed
   isn't settled inline. Checked from **both** the field and the list —
   focus can leave an open list (`tab`, or another widget focused outright)
   without ever passing back through the field.
6. CSS in `app.tcss` for `.select-field` and its expanded list, following the
   existing panel/field look (no border of its own — the panel owns the
   border). The list is `max-height: 8` and scrolls, so a machine with many
   sources can't push the button off the panel.
7. `short_labels`: the collapsed line takes a shorter form than the list
   does. An option's label carries its raw ID (needed to tell two similar
   sources apart while choosing); the collapsed line already has the field's
   own name in front of it and only the panel's width to fit in, so it shows
   the name alone.
8. Tests in `tests/test_tui_panels.py`: expand on `enter`, choose with `enter`,
   `esc` collapses leaving the value alone, `esc` from the collapsed field
   reaches the panel, and the value survives a blur.

## 4. Shared input-method form

New module `idiomas/tui/screens/input_methods.py`, used by both the wizard and
Settings so the two surfaces can't drift:

1. `LANGUAGE_HINTS` per language, and `preselect(sources, language, current)`
   implementing `requirements.md` · *Preselection*.
2. `choices(sources)` → the `(id, label)` pairs, each label pairing the display
   name with the raw ID.
3. `language_field_label(language)` → `"Chinese input"` / `"German input"`;
   the translation field is always `"Translation input"`.
4. `compose_fields(language, sources, current)` yielding the two `SelectField`s
   plus the advisory `Static` when `len(sources) < 2` (one source: "both fields
   use the only keyboard enabled…"; none: "no input sources found — add one in
   System Settings › Keyboard › Input Sources"). Never blocking.
5. `read_fields(screen)` → `(input_method, translation_input_method)`.

## 4b. `FormScreen` (surfaced during implementation)

The wizard's `_WizardStep` already cycled `tab` over a known content order,
and Settings' input-method screen needs exactly the same thing. Rather than a
second copy, that behaviour moves to `panels.FormScreen` and both subclass
it; `_WizardStep` keeps only its docstring. Recorded here because it wasn't
in the plan as first written — it only became worth extracting once the
second caller existed.

## 5. Wizard step

In `idiomas/tui/screens/wizard.py`:

1. `InputMethodScreen(_WizardStep)`, constructed with the language and its
   index in `app.languages`. Composes group 4's fields, a `Next` button on every
   step but the last and `Finish` on the last.
2. `TreeLocationScreen._finish` → `_next`: it keeps validating the root and
   stores it on the app (`self.app.root`), but **no longer** creates folders or
   saves — it pushes `InputMethodScreen(0)` instead. Folder creation and
   `save_config` move to the last input-method step, so quitting mid-wizard
   still writes nothing (M5's standing decision).
3. `WizardApp.__init__` gains `self.root: Path | None` and
   `self.input_methods: dict[str, tuple[str, str]]`, so `q` back into a step
   re-shows what was chosen.
4. Its button label and footer hint change to match (`Next` instead of
   `Finish`).
5. Tests in `tests/test_tui_wizard.py`: the step appears once per chosen
   language in order; the saved config carries both IDs per language; `q` back
   from the first input-method step returns to tree location with the root
   intact; finishing creates the folders; one source preselects both fields;
   zero sources still finishes, storing `""`.

## 6. Settings screen

1. New module `idiomas/tui/screens/settings.py`; move `SettingsScreen` out of
   `landing.py` into it (landing imports it), and add
   `Option("Input methods", id="input_methods")` above the two existing dummy
   items.
2. `InputMethodLanguagesScreen(MenuScreen)`: one option per registered language.
3. `InputMethodSettingsScreen(FormScreen)`: group 4's fields prefilled from the
   config, plus `Save`. Saving rewrites the whole `Config` through
   `save_config` (atomic, M4/M5's convention), mutates `self.app.config`'s
   `LanguageConfig` in place so the running app picks it up without a restart,
   and pops back to the language menu.
4. Tests in a new `tests/test_tui_settings.py`: the menu lists the registered
   languages; the fields open prefilled; saving writes both keys to disk and
   updates `app.config`; a screen opened for a language with nothing configured
   preselects per group 4 rather than showing blanks.

## 7. `input_method.py` and Entry

1. Rewrite `idiomas/input_method.py` around one config-driven entry point:
   `switch_to(source_id)`, a no-op on an empty string, delegating to
   `idiomas.platform.switch_input_source` otherwise. Drop
   `PINYIN_SIMPLIFIED_SOURCE_ID` / `ENGLISH_INTERNATIONAL_SOURCE_ID`,
   `switch_to_pinyin` and `switch_to_english_international`. Rewrite the module
   docstring: it no longer stands in for a wizard that doesn't exist.
2. `HanziInput` reads `self.screen.config` (the `NotebookConfig` `EntryScreen`
   already holds) at focus/blur time and switches to `input_method` /
   `translation_input_method`. Worker-thread ownership (`self.app`), the group
   name, and the `from_app_focus` / `app_focus` guards are unchanged.
3. Update `tests/test_input_method.py` and the three `HanziInput` tests in
   `tests/test_tui_entry_screen.py`, adding one that an unconfigured language
   switches nothing at all.

## 7b. Layout width (surfaced during implementation)

`.wizard-panel` is 60 columns, which cuts off an option like `Pinyin –
Simplified  (com.apple.inputmethod.SCIM.ITABC)`. The two input-method
screens override it to 76. Verified by rendering the screen and reading back
its text, not by eye alone.

## 8. Specs and docs

1. `specs/current/design.md`: `SelectField` in the *Implementation* section and
   in the nesting-model prose (content → field → panel → backpanel); a short
   *Settings* subsection stating that input methods are the one real item.
2. `specs/current/stack.md`: `list_input_sources` added to the platform layer's
   bullet with the `plistlib` rationale; the config-schema bullet updated for
   `input_method` / `translation_input_method`.
3. `specs/Sprint-4/guidelines/notes-sprint-4.md`: the milestone's decisions,
   added at merge time per the workflow — including the Settings widening,
   which contradicts this sprint's own *Settings stays all dummy items*
   assumption and has to be recorded as superseded rather than silently left
   standing.
