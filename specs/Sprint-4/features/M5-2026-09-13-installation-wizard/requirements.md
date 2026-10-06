# M5 · Installation wizard — requirements

## Roadmap anchor

From [`../../roadmap-sprint-4.md`](../../roadmap-sprint-4.md):

**Deliverable.** A sequence of Textual screens, built on M1's classes, that
runs **only when no config exists** and never again once it has written one:

1. **Dependencies.** Runs M4's doctor. A missing **required** tool blocks the
   wizard from continuing and shows the exact install command. A missing
   **optional** tool shows a warning and lets the user carry on.
2. **User name.**
3. **Languages** — Chinese and German offered. Any number can be chosen.
4. **Tree location** per language, defaulting under `~/Documents/Idiomas/` and
   editable. The tree folder is created if it doesn't exist. An existing tree
   is used as it is, never overwritten. The dev points the wizard at their
   current tree; nothing is migrated automatically.

On finishing, the config is written and the landing menu opens.

**Done when.** With no config, launching `idiomas` opens the wizard; a missing
required dependency stops it; a missing optional one only warns; finishing
writes a config the app then runs from; relaunching skips the wizard; the dev
runs it fresh against their real tree and lands on a working Chinese notebook;
and the full test suite passes.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Instalation wizard*, items 1–4 ("PATH? Dependencies? Discuss.", "Trees
locations", "User name", "Languages").

Note: the roadmap's step 4 says "Tree location per language" but Sprint 4's
notes (M4 Decisions) already narrowed this to **one root folder**, not a
location per language — `<root>/tree-<Language>` is derived, not asked for
per language. M5 follows that decision, not the roadmap's literal wording.

## Scope

**In scope.**

1. **A `WizardApp`**, a separate Textual `App` from `IdiomasApp`, holding the
   four wizard screens as a normal screen stack (push for forward, pop for
   back). It exits with the finished `Config` on success, or `None` if
   quit before the last step.
2. **Step 1 — Dependencies.** Runs `doctor.run()` and lists every check,
   labelled required/optional, **aligned into columns and colored**: green
   `ok`, or red `missing` followed by `<-- ` and the dependency's `url`
   (e.g. its GitHub repo) when it has one — not the raw install-command
   message, which can run long enough to be cut off at the panel's width;
   `idiomas doctor`'s CLI output is unaffected and still prints the full
   message. A failing required check blocks `Next`. The step offers a
   **recheck** action that re-runs `doctor.run()` in place, without
   restarting the wizard, so the dev can fix a tool and continue without
   quitting. **Recheck shows an inline spinner next to each dependency**
   (not one big indicator replacing the whole list) while it runs in a
   background thread, with a floor under how long it stays up — dev's
   request, since `doctor.run()` alone finishes too fast for feedback to
   read as intentional rather than a flash.
3. **Step 2 — User name.** One text field. `Next` does nothing on an empty
   or whitespace-only name — the same rule M3 set for the new-category name.
4. **Step 3 — Languages.** Chinese and German offered as checkboxes, any
   number selectable, but **at least one is required** to continue — an
   empty landing menu isn't a useful outcome. Selection state carries into
   step 4 (which languages get a tree folder). Checkboxes toggle only on
   `enter`, not `space` — one unambiguous key, rather than two doing the
   same thing — and render at a fixed width regardless of the language
   name's length, so "Chinese" and "German" line up.
5. **Step 4 — Tree location.** One text field for the root folder,
   pre-filled with `~/Documents/Idiomas/`, editable. On `Finish`:
   - The path is validated: it must be writable (creatable, or already a
     writable directory) and must **not** resolve inside the installed
     `idiomas` package. A failing validation blocks `Finish` and shows why.
   - The root folder is created if missing.
   - `<root>/tree-<Language>` is created for **every** language chosen in
     step 3 — including German, even though it stays inert this sprint,
     for consistency with Chinese rather than special-casing it.
   - An existing tree folder (the dev's real one, pointed at directly) is
     left exactly as it is — never overwritten, nothing migrated into it.
6. **Finishing the wizard.** A `Config` is assembled from the four steps'
   answers (German's/Chinese's `LanguageConfig` entries carry empty
   `hanzi_input_method`/`translation_input_method` — M6's job) and written
   to `CONFIG_PATH` via a new `save_config()` in `config.py`, atomically
   (temp file in the same directory, then `os.replace`, per Sprint 4 notes'
   Decisions). The wizard app then exits with that `Config`.
7. **Navigation.** `q` on any step but the first pops back to the previous
   step (existing `PanelScreen.action_back_or_quit` behaviour, reused as-is);
   `q` on the **first** step asks for confirmation (a `ConfirmDialog`,
   "Quit the installation wizard? Nothing will be saved.") before aborting
   — confirmed, the app exits with `None` and **no config file is
   written**; declined, the dialog closes and step 1 is unchanged. Bug
   caught during hands-on testing: `Screen.pop_screen()`/a naive
   `len(self.app.screen_stack) <= 1` check are both wrong here — Textual's
   `screen_stack` always carries its own implicit default screen
   underneath every screen the app pushes, so that length check never
   fires and `q` was silently popping back to that empty default screen (an
   unresponsive blank app) instead of aborting. Step 1's `action_back_or_quit`
   is unconditional: it always confirms-then-exits, never pops. Relaunching
   `idiomas` after a confirmed abort starts the wizard over from step 1
   with nothing remembered.
8. **Every screen carries a bold title and a plain-language prompt** above
   its interactive content ("Dependencies" / "Checking that everything
   Idiomas needs is installed:", "Your name" / "What should Idiomas call
   you?", "Languages" / "Which languages would you like to set up? Choose
   at least one.", "Tree location" / "Where should your language trees
   live?") — added after hands-on feedback that a bare field/checklist
   with no explanation read as unclear to a first-time user.
9. **Wiring into `__main__.py`.** `_tui()` checks `CONFIG_PATH.exists()`
   before deciding what to run:
   - Missing: run `WizardApp()`; if it exits with `None`, return without
     starting `IdiomasApp` (the dev just quit — nothing else to do); if it
     exits with a `Config`, start `IdiomasApp(config)` with it directly, in
     the same process — no re-read from disk needed.
   - Present: unchanged — `load_config()` then `IdiomasApp(config)`.
   - `_compile()` and `_doctor()` are **unaffected**: `idiomas doctor` needs
     no config today and keeps working before the wizard has ever run;
     `idiomas compile` still requires a config and keeps raising
     `ConfigNotFoundError` (with `NO_CONFIG_MESSAGE`) if run first — compiling
     before any language/tree is registered has nothing to compile.

10. **A dev-only escape hatch to open the wizard without moving a real
   config aside: `idiomas wizard`.** Added mid-milestone so the dev could
   hands-on test the wizard's screens without repeatedly backing up and
   restoring `~/.config/idiomas/config.toml`. Checked directly against
   `sys.argv` in `main()`, before `argparse` ever runs — **not** registered
   as an `argparse` subparser, since even `help=argparse.SUPPRESS` still
   leaks the name into `--help`'s usage/choices line (verified: it renders
   as a literal `wizard  ==SUPPRESS==` row). This keeps `wizard` fully
   invisible to `idiomas --help` and out of the documented CLI surface.
   An env-var version (`IDIOMAS_FORCE_WIZARD=1 idiomas`) was tried first
   and dropped: it was consistently mistyped/misunderstood in practice, so
   a plain subcommand replaced it. It doesn't change what ends the wizard:
   `Finish` still writes the real config; `q` before that still aborts and
   writes nothing, exactly as in the real no-config flow — so testing
   against a real config safely means backing out rather than finishing.

**Explicitly out of scope** (per the roadmap and Sprint 4 notes):

- Input methods (M6's own wizard step, added after tree locations).
- Installing missing dependencies — the wizard only blocks/warns.
- A working German notebook — German's folder is created, nothing else
  about it becomes functional.
- Migrating an existing `.idiomas.toml`.
- Editing wizard answers after the fact (Settings stays dummy this sprint).
- Windows/Linux — the wizard's own logic needs no OS branching; the one
  OS-specific piece it might have touched (dependency checks) is already
  behind `doctor.py`/`idiomas.platform` from M4.

## Decisions

Settled with the dev during this milestone's spec conversation, on
2026-09-13.

| Decision | Rationale |
| --- | --- |
| **Steps can be revisited: `q` goes back one step**, reusing `PanelScreen`'s existing back/quit key rather than adding a new binding | Dev's choice ("forward + backward"). The wizard screens are already on a normal Textual screen stack, so `pop_screen` naturally returns to the previous step's answers still in place. |
| **Quitting before the last step writes nothing.** `q` on step 1 aborts the whole wizard (`WizardApp` exits with `None`); relaunching starts over from scratch | Dev's choice, matching the roadmap's own parenthetical ("nothing written seems right"). No partial config, no resume-from-where-you-left-off. |
| **German's tree folder is created even though German is inert**, for consistency with Chinese | Dev's choice: don't special-case the folder step by functionality — that distinction stays where it already lives (`FUNCTIONAL_LANGUAGES` in code), not in what the wizard creates on disk. |
| **The root folder is validated: writable, and not inside the installed package** | Dev's choice (recommended option). Guards against the same class of mistake M4 fixed for the app's own config/templates — a tree accidentally nested inside `site-packages` would have the same "breaks once reinstalled" problem. |
| **`idiomas` with no subcommand launches the wizard app when no config exists**, instead of `_tui()`'s current `ConfigNotFoundError` → exit-message path | Dev's choice. `_compile`/`_doctor` are untouched — only the interactive TUI entry point gains wizard behaviour. |
| **A failing required dependency blocks `Next` but offers a recheck**, not a hard restart | Dev's choice (recommended option). Re-running `doctor.run()` in place lets the dev install the missing tool in another terminal and continue without losing step 2–4 progress (moot here since it's step 1, but keeps the same recheck affordance as any later revisit). |
| **At least one language is required to finish** | Dev's choice. A config with zero registered languages would produce an empty, useless landing menu. |
| **The user name is required, non-empty** | Dev's choice, consistent with M3's new-category name rule. |
| **A dev-only `idiomas wizard` subcommand forces the wizard open even with a config present**, checked against `sys.argv` before `argparse` runs rather than registered as a subparser | Dev's mid-milestone request during hands-on testing: moving the real config aside and back for every test run was too much friction. First tried as an `IDIOMAS_FORCE_WIZARD` env var; dropped after the dev found it consistently confusing to invoke correctly in a live shell. A plain subcommand is much harder to get wrong. Not registered via `argparse.add_parser` (even with `help=argparse.SUPPRESS`) because that still leaks `wizard` into `--help`'s usage line — verified empirically. |
| **Quitting step 1 asks for confirmation first** (`ConfirmDialog`), rather than aborting immediately | Dev's hands-on feedback: an unconfirmed full-wizard abort felt jarring ("exits to a black screen"). Matches Inspect Tree's existing "are you sure" treatment for its own destructive action (delete). |
| **Dependency check lines are aligned into columns and colored** (green ok / red failing), via a `rich.text.Text` built with fixed-width `f"{...:<10}"` fields and per-span `style=` rather than Rich markup strings | Dev's hands-on feedback: plain, unaligned text made it hard to spot a failing check at a glance. `Text.append(..., style=...)` avoids markup-escaping the check's own message text (which can contain backticks, e.g. `` `brew install pandoc` ``). |
| **Every wizard screen gets a bold title + a plain-language prompt line** above its content | Dev's hands-on feedback: a bare field/checklist with no explanation read as unclear on first use. |
| **Language checkboxes toggle only on `enter`, not `space`**, via a small `EnterOnlyCheckbox(Checkbox)` overriding `space` to a no-op | Dev's request: two keys doing the same thing was extra ambiguity for no benefit. Uses the same override pattern `NoShiftArrowsTree` already established for silencing part of a widget's inherited `BINDINGS` — verified empirically that Textual resolves a subclass's binding for a given key over its parent's, rather than replacing the whole list. |
| **Language checkboxes render at a fixed width** (`width: 20` in `app.tcss`), not sized to each label's text | Dev's request: "Chinese" and "German" rendered at slightly different widths since `Checkbox` sizes to its label by default. |
| **`Recheck`'s animation is an inline per-line spinner, not a separate `LoadingIndicator` widget** replacing the whole list, floored at `MIN_RECHECK_SECONDS = 0.4` in a background thread (`self.app.run_worker(..., thread=True)`, `call_from_thread` back to the UI) | Dev's request for "a little inoffensive animation", then explicit follow-up feedback ("it should be inline for each dependency") after seeing the first `LoadingIndicator`-based version — reworked to reuse the same `#dependencies-list` `Static` with a spinner frame in each check's status column (`_pending_checks_text()`), never swapping in a separate widget. `doctor.run()` alone (shutil.which lookups plus one `kpsewhich` subprocess call) finishes in milliseconds — too fast to read as a deliberate animation rather than a flash. |
| **A failing check shows `missing` (red) + `<-- ` + `doctor.Check.url`**, not the raw install-command message, in the wizard only | Dev's hands-on testing: the full message (e.g. "pandoc not found: install it (e.g. \`brew install pandoc\`)") got silently cut off at the wizard panel's fixed width — dev asked what a missing dependency would even look like, and the truncation was the actual finding. `Check` gained a new `url` field (`doctor.py`); `idiomas doctor`'s CLI output is untouched and still prints the full `message`, which has more room in a terminal than a 60-column panel. Heiti SC has no `url` (it ships with macOS, nothing to link to). |
| **Auto-installing missing dependencies stays out of scope**, confirmed again when the dev asked about it directly | Reaffirms Sprint 4 notes' existing Decision ("the dev chose block/warn over install... tlmgr needs sudo, and it's the least separable across OSs") rather than reopening it. Not implemented; the wizard still only checks and shows how to fix things by hand. |
| **`Backpanel`'s border is always accent, app-wide — not just on the wizard** — the one exception to `design.md`'s dim/accent focus convention | Dev's hands-on feedback, while testing M5: the backpanel was "the only element in which focusing does not trigger a visual change directly" — every panel inside it already dims when focus leaves the backpanel, so the backpanel's own border never needed to change too. This is a `panels.py`/`app.tcss`/`design.md` change, not scoped to M5's own screens — recorded here since it surfaced during this milestone's testing, but it affects every screen in the app. |
| **`MenuScreen` binds `tab` to a no-op**, fixing every menu (landing, main menu, settings) | Same bug class as `_WizardStep`'s `tab` fix, caught by the dev in the *running app*, not the wizard: a flat menu's `OptionList` is its only focusable content, so Textual's default tab-cycling moved focus onto the `Backpanel` itself (also `can_focus=True`), visibly defocusing the option list. Fixed at the shared `MenuScreen` base in `panels.py` rather than per-menu, on the same "one place to change every X" basis as the rest of the panel/backpanel model. |

## Context

- `config.py`'s `Config`/`LanguageConfig`/`NotebookConfig` shapes and
  `CONFIG_PATH`/`FUNCTIONAL_LANGUAGES` are unchanged by M5 — this milestone
  only adds a way to **write** a `Config`, on the schema M4 already
  established. `config.py`'s module docstring ("this module only reads it")
  is updated since that stops being true.
- `doctor.run()` (`doctor.py`) gained one field: `Check.url: str = ""`, a
  link (typically the tool's GitHub repo) the wizard shows next to a
  failing check. Everything else about `Check`/`run()` is reused as-is —
  `name`, `required`, `ok`, `message` are unchanged, and `idiomas doctor`'s
  CLI output (which prints `message`, not `url`) is unaffected. Five of
  six checks get a `url` (pandoc, xelatex, xeCJK, macism, nvim); Heiti SC
  doesn't, since it ships with macOS rather than being installed from a
  repo.
- The wizard is built on M1/M2's `PanelScreen`/`Panel`/`Backpanel`/
  `TextField`/`VimOptionList` (`tui/screens/base.py`, `tui/screens/panels.py`)
  — no new screen-foundation classes, only new screens that use the existing
  ones, following `design.md`'s conventions (focus-on-entry, `esc` climbs
  content → panel → backpanel, shift+hjkl only on panels).
- `WizardApp` is a second `textual.app.App` subclass alongside
  `IdiomasApp` (`tui/app.py`), not a mode of `IdiomasApp` itself — it has no
  `Config` to hold until it produces one, and its screen stack (wizard
  steps) has nothing in common with `IdiomasApp`'s (`LandingMenuScreen`
  onward). `plan.md` settles where it lives (`tui/app.py` or its own
  module) and its exact typing (`App[Config | None]`).
- `__main__.py`'s `_tui()` is the only call site that changes; `NO_CONFIG_MESSAGE`
  and the `ConfigNotFoundError` handling around `_compile()`/`_doctor()`
  stay exactly as M4 left them.
- No test today exercises `__main__.py`'s `main()` directly (checked:
  no `test___main__.py`); `plan.md` decides whether M5 adds one for the
  wizard-vs-`load_config` branch in `_tui()`.
