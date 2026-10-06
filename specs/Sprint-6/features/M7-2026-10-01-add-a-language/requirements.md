# M7 · Add a language — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-6.md`](../../roadmap-sprint-6.md), *M7 · Add a
language*:

> **Deliverable.**
>
> - **A registry of supported languages**, each with its kind: Chinese
>   (character-and-phonetic); German, Italian, French, English, Spanish
>   (alphabetical). One list, read by both surfaces below.
> - **The wizard offers all six**, replacing today's hardcoded
>   `LANGUAGE_CHOICES = ["Chinese", "German"]`, still requiring at least one,
>   and still asking the per-language input-method questions for each chosen.
> - **Settings › Add a language is real.** It registers a language that was not
>   chosen at install time: writes it to the config, creates its
>   `tree-<Language>` folder, asks the same input-method questions with the
>   same widgets and the same wording the wizard uses — `design.md`'s standing
>   rule that a setting the wizard asks for is a setting Settings can change —
>   and the language appears on the landing menu without relaunching, as
>   Sprint 4 M6's input-method change already does.
> - **Every alphabetical language works on arrival**, because M5 and M6 did the
>   work: adding Italian is a registry entry, and its Entry screen and PDFs come
>   out right with no per-language code.
> - The new Settings option carries a legend description, per M4.
>
> **Done when.** The dev adds a language from Settings in the running app, sees
> it on the landing menu without relaunching, enters a word into it and
> compiles it; a fresh wizard run offers all six; and the full test suite
> passes.

Source: [`backlog.md`](../../guidelines/backlog.md)'s *Implement add a
language*: "There must be a list of possible languages. All languages that will
be supported fall under the german category (alphabetical only) or chinese
category (character and phonetic). For now only add Italian, French, English,
Spanish (german category). I suppose this means the wizard will also change."

What earlier milestones left for this one (sprint notes):

- **M5:** the kind comes from the built-in table `languages.LANGUAGES`, not the
  config; "M7 extends the same table from two entries to six". A name outside
  the registry is "not functional", never an exception.
- **M6:** "M7's *Add a language* calls the same helper", `store.ensure_tree`.
  And, Postponed to M7: `doctor` requires xeCJK and the CJK font whatever
  languages are configured.
- **M4:** options are `MenuOption`s, and *Add a language*'s "Not available
  yet." description is replaced along with its behaviour.

## Settled with the dev (2026-10-01)

| Question | Answer |
| --- | --- |
| Registered languages in the *Add a language* list: hidden or shown disabled? | **Hidden.** Only addable languages are listed. With all six registered, choosing *Add a language* shows "Every supported language is already added." and nothing else. No disabled-row style is introduced. |
| What if `tree-<Language>` already exists on disk? | **Adopted silently.** `ensure_tree` creates only what is missing and never touches what exists, exactly as the wizard does. This is what makes M8's "re-adding restores it" true. |
| Where does a new language appear on the landing menu? | **Appended**, in config order, after the languages already there, the same way the wizard keeps the order you chose languages in. |
| Does M7 make `doctor` language-aware (M6's Postponed item)? | **Yes.** xeCJK and the CJK font are needed only by a language whose kind sets a CJK face. |
| The wizard runs `doctor` before languages are chosen. How does it handle the CJK pair? | **They are checked at the languages step.** Step 1 still lists them, labelled with the language that needs them instead of `required`, and they don't block *Next*. Step 3 checks them when such a language is ticked. |
| Adding Chinese (from Settings, or ticking it in the wizard) while xeCJK or the font is missing | **The app offers to install it.** It asks first. Yes suspends the TUI and runs the platform's install command in the terminal, where `sudo` can ask for a password, then rechecks. If the dependency is still missing, or there is no command to offer, the language is refused with the command or message shown. |
| The same offer in the wizard? | **Yes, the same offer on both surfaces.** |
| Where do you land after adding a language? | **Back in Settings**, with a notification "Italian added." The picker and the form both close. |

## Agent decisions

Not raised with the dev: each follows from the roadmap, an earlier milestone's
decision, or the backlog's "for now".

| Decision | Why |
| --- | --- |
| **The registry stays fixed in code.** No user-extensible list. | The backlog's "for now only add…", and the sprint notes' Postponed row *A user-extensible language registry* already anticipated it. That row is settled as postponed, not resolved. |
| **Adding can only be undone through M8.** | The roadmap lists it as open, and *Remove a notebook* is the opposite operation, one milestone later. Before M8, removal means hand-editing the config, as it does today. |
| **Registry order is the backlog's:** Chinese, German, Italian, French, English, Spanish. | The wizard offers languages in registry order, and the add picker lists them in the same order. |
| **The *Add a language* picker is a `MenuScreen`**, with one `MenuOption` per addable language. | Same shape as Settings › Input methods' language picker (M4), so it gets the legend for free. |
| **German's input hints gain the Linux layout IDs** (`keyboard-de`, `xkb:de`). | The four new languages need them, since their hints cover both platforms' ID formats. Leaving German macOS-only in the same table would be an inconsistency introduced by this milestone. It only affects which option starts highlighted. |

## Scope

### 1. The registry

`languages.LANGUAGES` grows from two entries to six, in the order above. The
four new entries are `ALPHABETICAL` and `functional=True`, with no other
per-language field. "Adding Italian is a registry entry" is meant literally:
nothing else in `src/` names Italian, French, English or Spanish except the
platform display-name tables below.

Input hints, matched case-insensitively as substrings of a source ID (only
used for preselection; see `input_methods.preselect_language`):

| Language | Hints |
| --- | --- |
| German | `German`, `keyboard-de`, `xkb:de` |
| Italian | `Italian`, `keyboard-it`, `xkb:it` |
| French | `French`, `keyboard-fr`, `xkb:fr` |
| English | `keylayout.US`, `keylayout.ABC`, `keylayout.British`, `keyboard-us`, `keyboard-gb`, `xkb:us`, `xkb:gb` |
| Spanish | `Spanish`, `LatinAmerican`, `keyboard-es`, `keyboard-latam`, `xkb:es`, `xkb:latam` |

English deliberately avoids a bare `US`, which would match `Russian`. A test
asserts that no hint of one language matches another language's own source
IDs in the display-name tables.

The display-name tables gain the new layouts. On macOS that's
`com.apple.keylayout.Italian`, `Italian-Pro`, `French`, `French-PC`. On Linux
it's `keyboard-it`, `keyboard-fr`, `xkb:it::ita` and `xkb:fr::fra`. The tables
are only for display, and an unknown ID still falls back as it does today.

### 2. `doctor` knows which languages need what

- `Check` gains `needed_for: tuple[str, ...] = ()`, the registry languages
  that need the check, and `install: str = ""`, the platform's install command
  for it (from `install_hint`), or `""` when there is none.
- xeCJK and the CJK font are no longer `required=True`. They are
  `required=False` with `needed_for` set to every registry language whose kind
  has a `cjk_font`, derived from `LANGUAGES` and not hardcoded as "Chinese".
  `required` keeps its meaning: needed by every install.
- `doctor.missing_for(checks, languages) -> list[Check]` returns the checks
  that are not ok and are either `required` or needed by one of `languages`.
  This one rule is used by the CLI, the wizard and Settings.
- **Label.** Where `required`/`optional` is printed (the CLI and the wizard's
  step 1), a check with `needed_for` shows its languages instead, e.g.
  `[ Chinese]`, right-aligned in the same 8-wide column. If the joined names
  are wider than 8, the column widens, as `_name_width` does for names.
- **`idiomas doctor` (CLI)** reads the config if one exists and fails (exit 1)
  on `missing_for(checks, configured languages)`. Without a config, it fails
  only on `required` checks. A German-only install passes without xeCJK.

### 3. The wizard

- **Step 1 (Dependencies)** blocks *Next* only on `required` checks. The CJK
  pair is listed with its `[ Chinese]` label and never blocks there. *Recheck*
  is unchanged.
- **Step 3 (Languages)** offers all six, in registry order, with the existing
  `EnterOnlyCheckbox`es and "Choose at least one language." rule. On *Next*,
  `doctor` is re-run and `missing_for(checks, selected)` is computed:
  - Empty: proceed, as today.
  - Non-empty: the install offer (§5). If it succeeds, proceed. Otherwise
    stay on step 3 with the error line naming the language, what's missing
    and the command, e.g. "Chinese needs xeCJK, which is missing. Install it
    with `sudo tlmgr install xecjk`." and, on its own line, "Or untick the
    language that needs it." A German-only selection never reaches this.
- **The checkboxes are one row each** (`compact=True`). Found in
  implementation: six of Textual's default bordered checkboxes are three rows
  apiece and push *Next* to rows 26–29, off an 80×24 terminal. Compact
  checkboxes drop the border and keep the focus highlight on the label; the
  whole step then ends at row 19.
- The rest of the wizard is unchanged: one input-method step per chosen
  language in the order chosen, then `PathScreen`, which writes.

### 4. Settings › Add a language

- **The Settings option**: `MenuOption("Add a language", "Start a notebook for
  another language.", id="add_language")`.
- **Choosing it**, with at least one registry language not in the config,
  pushes `AddLanguageScreen(MenuScreen)`, which lists the unregistered ones in
  registry order. Each is `MenuOption(name, f"Start a notebook for {name}.",
  id=f"language:{name}")` ("Start a Italian notebook" and "a English" don't
  read, so the language comes last). With none left, it pushes `PlaceholderScreen("Every
  supported language is already added.")` instead.
  *Remove a notebook* stays the placeholder it is until M8.
- **Choosing a language** pushes `AddLanguageFormScreen(FormScreen)`, built
  like `InputMethodSettingsScreen`:
  - title `Add a language · Italian`;
  - the wizard's prompt, word for word: "Which keyboard do you type each side
    with? They may be the same.";
  - `compose_fields(language, available_sources())`, with no stored values, so
    the same preselection the wizard makes;
  - an error line (`wizard-error`), hidden until needed;
  - an **Add** button;
  - the same footer hint as Input methods.
- **Add**:
  1. If `missing_for(doctor.run(), [language])` is non-empty, the install
     offer (§5). If that fails, the error line explains it and nothing is
     written.
  2. `ensure_tree(config.tree_root(language))`, which adopts an existing
     folder.
  3. Save a **copy** of the config with the new `LanguageConfig` appended,
     through `save_config`.
  4. Only after the save succeeds, append the same `LanguageConfig` to the
     running `app.config.languages`.
  5. Pop the form and the picker, and notify "Italian added." on Settings.

  An `OSError` from step 2 or 3, or `ValueError` from the save's round-trip
  check, is shown in the error line, and the running config is unchanged. A
  folder created in step 2 before a failed save is left on disk. It is
  harmless, and the next add adopts it.
- **Without relaunching:** the landing menu, the Input methods picker and the
  *Add a language* picker are rebuilt from `app.config.languages` whenever they
  are shown again (on screen resume), not only when composed. On the landing
  menu the highlighted option stays on the same option id when it still
  exists. Back on the landing menu after adding Italian, *Italian notebook* is
  listed last before *Settings*, and opening it opens the notebook menu. Input
  methods lists Italian too.

### 5. The install offer

One shared helper, used by the wizard's step 3 and the add form, so the two
can't word it differently (`design.md`'s *Settings* rule):

- **Nothing to run.** If any missing check has no `install` command (an
  unknown Linux distro, or a font with no command), no offer is made. The
  error line names each missing dependency with its `message`, and the
  language is refused.
- **Only a language's own dependencies are offered.** If the missing list
  holds a check that no language-specific `needed_for` covers (a `required`
  one, `pandoc` or `xelatex`, which can only be missing here if it vanished
  since step 1), there is no offer: it is reported as "pandoc is missing." with
  its message. This is the "installing anything other than the CJK pair"
  exclusion below, enforced rather than only stated.
- **The helper's shape.** `ensure_dependencies(app, languages, on_done)` calls
  `on_done(None)` when the languages have what they need, or
  `on_done(reason)` with the refusal text. `refusal(missing, languages)` words
  one line per dependency ("Chinese needs xeCJK, which is missing. Install it
  with `…`." — or the check's own message when there is no command); several
  languages read "Chinese and X need …".
- **The offer.** Otherwise a `ConfirmDialog`: "Chinese needs xeCJK, which is
  missing. Install it now? This runs `sudo tlmgr install xecjk` in your
  terminal." With several missing checks, all are named and all commands are
  listed.
- **Yes.** The TUI is suspended with `app.suspend()`, the same mechanism as
  Inspect Tree's nvim. Each command is printed, then run with
  `subprocess.run(shlex.split(command))`, without a shell, connected to the
  terminal so `sudo` can prompt. After the last command:
  "Press Enter to return to Idiomas.", so the output can be read before the TUI
  redraws. Back in the TUI, `doctor.run()` again. If nothing is missing any
  more, the action continues. Otherwise the error line names what is still
  missing and the command.
- **No**, or `esc`: the error line explains what's missing and the command, and
  the language is refused.
- An `OSError` running a command (e.g. `sudo` not found) is caught and reported
  the same way as a dependency that is still missing. It is never fatal
  (`design.md`'s *Failures are reported, never fatal*).

### 6. Every alphabetical language works on arrival

Nothing is written for Italian, French, English or Spanish beyond §1. Entry,
Browse, Inspect Tree, the renderer and autocompile all behave as they do for
German, because they branch on the kind. A parametrised test covers this for
each new language. It adds a word through the Entry form against a temp tree,
then renders and (in the real-pandoc tier) compiles a vocabulary and a
grammar deck.

### 7. Docs

- `specs/current/design.md`:
  - *Settings*: *Add a language* is real, the flow above, and *Remove a
    notebook* the one remaining placeholder.
  - A new subsection, *A language's missing dependencies*, for the install
    offer, as a convention shared by the wizard and Settings.
  - The step-1 label convention.
- `specs/current/stack.md`: `doctor`'s `needed_for`/`missing_for`, and the
  registry's six entries, wherever it describes them today.
- `README.md`: the supported languages, and `doctor`'s language-aware
  requirement, wherever it lists them.

## Out of scope

- **Removing a language**: M8.
- **A user-extensible registry**: Postponed (sprint notes).
- **Per-language typography among alphabetical languages.** All five share
  Latin Modern, as M6 settled for German. Its T1 encoding covers the accents of
  Italian, French and Spanish, and xelatex reads UTF-8. If a glyph turns up
  missing in hand-testing, it's raised then.
- **Installing anything other than the CJK pair** from the app. `pandoc`,
  `xelatex` and the optional tools stay as they are: the wizard's step 1
  reports them and the user installs them.

## Context

- `config.Config.tree_root(language)` and `save_config`'s atomic write and
  round-trip check (M1, #6) are reused as they are.
- `InputMethodSettingsScreen._save` is the precedent for "save, then mutate the
  running config". This milestone saves a copy first so that a failed save
  can't leave the running config ahead of the file.
- The landing menu today builds its options once in `compose()`. Nothing yet
  needed it to change while running, because Input methods changes no option.
