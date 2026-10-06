# M4 · Install groundwork — requirements

## Roadmap anchor

From [`../../roadmap-sprint-4.md`](../../roadmap-sprint-4.md):

**Deliverable.**

- **PATH.** `idiomas` becomes a real command through a `[project.scripts]`
  entry. Brew packaging is out of scope, as the backlog says.
- **Nothing depends on the repo's location.** The config moves to
  `~/.config/idiomas/config.toml`. `compile.py`'s `templates/xecjk.tex` ships
  inside the package instead of being found by climbing up from `__file__`.
  The repo-root `PROJECT_ROOT` goes away.
- **New config schema:** user name, the registered languages, and per
  language its tree location and input methods. The old `.idiomas.toml` is
  **ignored, not migrated**.
- **Config-driven landing menu.** It lists the languages in the config
  instead of the hardcoded `LANGUAGES` constant. Chinese opens its notebook
  against its configured tree; German stays inert.
- **doctor, fixed and split.** It checks **Heiti SC** (M6 replaced Songti SC,
  and `doctor.py` still checks the old font), adds `macism` and `nvim`, and
  labels each check *required* (pandoc, xelatex, xeCJK, the font) or
  *optional* (`macism`, `nvim`).
- **Platform separation.** macOS-specific code — dependency checks, font
  paths, input-source switching, opening a PDF with `open` — moves behind one
  platform layer, so Windows and Linux can be added later without touching
  every call site. Only macOS is implemented.

**Done when.** `idiomas` runs as a command from any directory; running it
from outside the repo finds the template and reads the config from
`~/.config/idiomas/`; the landing menu shows the languages from the config;
`idiomas doctor` reports Heiti SC, `macism` and `nvim`, each marked required
or optional; no module outside the platform layer calls a macOS-only tool
directly; and the full test suite passes.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Instalation wizard* item 1 ("PATH? Dependencies? Discuss.") and its preamble
("More OSs (Windows, Linux) will be added in the future, so clear separation
is expected").

## Scope

**In scope.**

1. `pyproject.toml` gets a `[project.scripts]` entry (`idiomas =
   "idiomas.__main__:main"`) so `idiomas` runs as an installed command from
   any directory, without `python -m idiomas`.
2. `templates/xecjk.tex` moves under `src/idiomas/templates/` and ships as
   package data, read via `importlib.resources` — not `__file__`-climbing.
   `compile.py`'s `TEMPLATE_PATH` module constant goes away.
3. `config.py` is rewritten for the new schema and location:
   - Config lives at `~/.config/idiomas/config.toml`, independent of where
     the code is installed. The repo-root `.idiomas.toml` is never read —
     no migration path, no fallback to it.
   - Schema: a user name, a single **root folder** (not per-language — see
     Decisions), and a list of registered languages. Each language entry
     carries its name and (from M6 on) its hanzi/translation input methods;
     M4 doesn't populate or require those fields.
   - Each language's tree lives at `<root>/tree-<Language>`, same naming
     Sprint 3 already uses (`tree-Chinese`) — the app derives this path, it
     is not stored per-language in the config.
   - `PROJECT_ROOT` (`__main__.py`) is deleted along with every call site
     that threaded it through (`load_or_prompt_config(project_root)`,
     `compile.py`'s `__file__`-climbing).
4. **No config found:** `idiomas` (every subcommand) prints a clear,
   actionable message — that no config exists yet and where one is expected
   (`~/.config/idiomas/config.toml`), with an example of the schema — and
   exits non-zero. No prompt, no silently-written default; M5's wizard is
   the only thing that writes a first config. This milestone does not add
   any config-writing code (see Decisions).
5. `landing.py`'s hardcoded `LANGUAGES` constant is replaced by reading
   `app.config.languages`. Whether a language is *functional* (opens a real
   notebook) stays a code-level fact, not a config field — this sprint that
   is Chinese only, German is always inert regardless of what's registered.
6. `doctor.py`:
   - The CJK font check moves from Songti SC to Heiti SC.
   - Adds checks for `macism` and `nvim` (both currently unchecked, `nvim`
     already load-bearing for Inspect Tree's MD mode since Sprint 3 M4).
   - Every check is labeled required (pandoc, xelatex, xeCJK, the font) or
     optional (`macism`, `nvim`); a missing required tool is a different
     outcome from a missing optional one (see Decisions and `plan.md`).
7. **Platform layer.** One new module is the sole caller of macOS-specific
   tools: the CJK font path check, `open` for viewing a PDF (`browse.py`,
   `inspect.py`), and input-source switching (`input_method.py`, unchanged
   behavior, moved). `pandoc`/`xelatex`/`macism`/`nvim` presence checks stay
   on `shutil.which`, which is already OS-agnostic. Only macOS is
   implemented; other platforms get inert no-ops, consistent with
   `input_method.py`'s existing off-macOS guarantee.
8. The dev's own `~/.config/idiomas/config.toml` is hand-written (by the
   agent, in conversation) to the new schema, since M5's wizard doesn't
   exist yet to write it. This is a one-off, not code.

**Explicitly out of scope** (unchanged from the roadmap):

- Brew packaging.
- Migrating the old repo-root `.idiomas.toml`.
- Installing missing dependencies (the wizard/doctor only checks).
- A working German notebook, or anything that makes German functional.
- Windows/Linux implementations — only the separation, not a second
  platform.
- The installation wizard itself (M5) and the input-method wizard step
  (M6) — M4 only shapes the config schema and `doctor.py` they depend on.
- Writing config from code (no `save_config`/atomic-write function is added
  in M4 — see Decisions).

## Decisions

| Decision | Rationale |
| --- | --- |
| **One root folder, not a location per language.** `<root>/tree-<Language>` for every registered language | Dev's explicit correction during the spec conversation: "only the main folder is asked for location. Chinese and german will live under that same folder, they cant be separated." This narrows the roadmap's "per language its tree location" — recorded here since it also constrains M5's wizard (one location question, not one per language). |
| **No config → clear error and exit**, not a temporary prompt | Dev's choice: keep M4 simple, no throwaway prompting code that M5 immediately replaces. |
| **M4 adds no config-writing code.** The dev's real `~/.config/idiomas/config.toml` is hand-written directly (by the agent) for development, not generated by a wizard or a default-writer | Dev's explicit ask: "please hand write it yourself". Since nothing in M4 writes a config (no wizard, no migration), a `save_config` function would be unused code. The atomic-write convention below is decided now so M5 doesn't have to relitigate it, but isn't implemented until M5 needs it. |
| **Atomic config writes, when M5 needs them: write to a temp file in the same directory, then `os.replace`** | Matches `stack.md`'s existing convention ("`os.replace` for atomic saves"), already used elsewhere in the codebase. Decided now, implemented in M5. |
| **Templates packaged via `importlib.resources`** | Matches the roadmap's own expected route; the alternative (`__file__`-climbing) is exactly what breaks once installed outside the repo. |
| **Functional-language list stays in code, not config** | German is inert this sprint regardless of what the wizard or config says (Sprint 4 notes' Decisions: "Multi-language is config-driven, German stays inert"). A config field the user could flip to "unlock" German would be misleading since nothing behind it works. |
| **Platform layer scope: font path, `open`, input-source switching** — not the `shutil.which` presence checks, which already behave the same on every OS | Roadmap's own list ("dependency checks, font paths, input-source switching, opening a PDF with `open`") read together with what's actually OS-specific: `shutil.which` needs no OS branching, only paths and OS-specific commands do. |
| **`doctor.py`'s return shape changes** from `list[str]` to a structured required/optional result | Needed to let `idiomas doctor` and the future wizard (M5) tell a blocking problem from a warning; a flat message list can't express that distinction. |

## Context

- `config.py`'s current `Config` (single `tree_root`/`language`) is kept, ​
  renamed if needed, as the shape `EntryScreen`, `BrowseScreen`,
  `InspectTreeScreen` and `MainMenuScreen` already consume — it becomes a
  per-language view derived from the new top-level config when a language is
  opened from the landing menu, rather than the thing loaded from disk
  directly. `plan.md` settles the exact types.
- `__main__.py`'s `PROJECT_ROOT` and `_tui`/`_compile` currently pass it into
  `load_or_prompt_config`; both call sites go away with the function.
- `compile.py`'s `TEMPLATE_PATH` (`Path(__file__).parent.parent.parent /
  "templates" / "xecjk.tex"`) is the other `__file__`-climbing path this
  milestone removes.
- `doctor.py`'s `CJK_FONT_PATH` currently points at
  `/System/Library/Fonts/Supplemental/Songti.ttc`; `templates/xecjk.tex`
  already sets `\setCJKmainfont{Heiti SC}` (from a prior, unspecced change —
  `doctor.py` was never updated to match). The Heiti SC family resolves to
  `/System/Library/Fonts/STHeiti Light.ttc` on this machine (verified via
  `fc-list`).
- macOS-specific call sites to move behind the platform layer:
  `browse.py::open_pdf`, `inspect.py::_open_pdf` (both `subprocess.run(["open",
  ...])`), `input_method.py::_select_source` (`macism`), and `doctor.py`'s
  font-path check. `inspect.py`'s `nvim` call and every `shutil.which` check
  are not moved — they're already cross-platform calls, not OS-specific
  paths or commands.
- `tests/test_config.py` and `tests/test_doctor.py` are rewritten for the
  new schema/shape, not extended alongside the old one.
