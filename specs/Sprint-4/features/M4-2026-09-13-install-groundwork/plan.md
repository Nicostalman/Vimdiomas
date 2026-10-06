# M4 · Install groundwork — plan

## 1. `idiomas` as a real command

- Add to `pyproject.toml`:
  ```toml
  [project.scripts]
  idiomas = "idiomas.__main__:main"
  ```
- `main()` in `__main__.py` already exists and takes no arguments beyond
  `sys.argv` via `argparse` — no change needed to it beyond what tasks 2–3
  require.
- Reinstall editable (`pip install -e .`) so the console-script shim is
  regenerated; verify `which idiomas` resolves and `idiomas doctor` runs from
  a directory outside the repo.

## 2. Templates as package data

- Move `templates/xecjk.tex` to `src/idiomas/templates/xecjk.tex`.
- `pyproject.toml`: add
  ```toml
  [tool.setuptools.package-data]
  idiomas = ["templates/*.tex"]
  ```
- `compile.py`: delete the `TEMPLATE_PATH` module constant. In
  `compile_file`, resolve the template with
  `importlib.resources.as_file(importlib.resources.files("idiomas") /
  "templates" / "xecjk.tex")` as a context manager around the `pandoc`
  subprocess call, so it works whether the package is installed from a
  wheel/zip or in editable mode.

## 3. New config schema and location

- Rewrite `config.py`:
  - `CONFIG_PATH = Path.home() / ".config" / "idiomas" / "config.toml"`
    (replaces `CONFIG_FILENAME` + the `project_root` parameter everywhere).
  - `LanguageConfig` dataclass: `name: str`, `hanzi_input_method: str = ""`,
    `translation_input_method: str = ""`. The two input-method fields are
    unused this milestone (M6 populates and reads them) but are part of the
    schema now so M6 doesn't need a migration.
  - `Config` dataclass (top-level, loaded from disk): `user_name: str`,
    `root: Path`, `languages: list[LanguageConfig]`.
  - `Config.tree_root(language: str) -> Path` returns `self.root /
    f"tree-{language}"`.
  - `NotebookConfig` dataclass (unchanged shape from today's `Config`):
    `tree_root: Path`, `language: str`. This is what `EntryScreen` and the
    rest of the per-language screens already take — keep that call shape
    stable, only its constructor changes (see task 5).
  - `class ConfigNotFoundError(Exception)`.
  - `load_config() -> Config`: read `CONFIG_PATH`; raise
    `ConfigNotFoundError` if it doesn't exist. Parse `languages` as a list of
    tables (`[[languages]]`) into `LanguageConfig`, defaulting the two input-
    method fields to `""` when absent (M4's own hand-written config omits
    them).
  - Delete `_prompt_path`, `_write_config`, `load_or_prompt_config`, and the
    old-format migration branch entirely — no code path writes or migrates a
    config this milestone (see `requirements.md`'s Decisions).
- `__main__.py`:
  - Delete `PROJECT_ROOT`.
  - `_tui`, `_compile`, `_doctor` (and `main`) call `load_config()` and catch
    `ConfigNotFoundError` in one place (`main`, around the dispatch), printing:
    ```
    No config found at ~/.config/idiomas/config.toml.

    Example:

        user_name = "Your Name"
        root = "/Users/you/Documents/Idiomas"

        [[languages]]
        name = "Chinese"
    ```
    and exiting with `SystemExit(1)`. (The installation wizard, M5, will
    replace this message with an actual wizard launch.)

## 4. Config-driven landing menu

- `landing.py`: delete the hardcoded `LANGUAGES` list. `LandingMenuScreen`
  reads `self.app.config.languages` (the new top-level `Config`) to build its
  options.
- Keep a small code-level constant, `FUNCTIONAL_LANGUAGES = {"Chinese"}`, to
  decide whether selecting a language opens `MainMenuScreen` or the inert
  `PlaceholderScreen` — not stored in config (see `requirements.md`'s
  Decisions).
- `MainMenuScreen` gains a `language: str` constructor argument (the name
  selected from landing). It builds the `NotebookConfig` itself —
  `NotebookConfig(tree_root=self.app.config.tree_root(language),
  language=language)` — and passes that into `EntryScreen`,
  `BrowseScreen(...tree_root)`, `InspectTreeScreen(...tree_root)`,
  `compile_all(...tree_root)` exactly as it does today, just sourced from the
  constructed `NotebookConfig` instead of `self.app.config` directly.
- `IdiomasApp.__init__` takes the new top-level `Config` (unchanged
  signature, different type).

## 5. `doctor.py`: Heiti SC, macism/nvim, required/optional

- `CJK_FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"` (Heiti SC),
  replacing the Songti SC path.
- Introduce:
  ```python
  @dataclass
  class Check:
      name: str
      required: bool
      ok: bool
      message: str  # actionable, only meaningful when not ok
  ```
- `run() -> list[Check]` replaces `check() -> list[str]`, producing one
  `Check` each for pandoc, xelatex, xeCJK, the CJK font (all `required=True`)
  and two new ones, `macism` and `nvim` (`required=False`), using
  `shutil.which`.
- The CJK font check now goes through the platform layer (task 6) instead of
  `os.path.exists` directly, so `doctor.py` itself no longer hardcodes a
  macOS path.
- `__main__.py::_doctor`: iterate `doctor.run()`, print each check
  (`[required]`/`[optional]` + ok/message), and exit non-zero only if any
  **required** check failed; a failed optional check prints a warning but
  exits 0 alongside an otherwise-clean run.

## 6. Platform layer

- New package `src/idiomas/platform/`:
  - `macos.py`: `open_file(path: Path) -> None` (today's `subprocess.run(["open",
    str(path)])`), `switch_input_source(source_id: str) -> None` (today's
    `input_method._select_source`, minus its own `platform.system()` guard —
    that check now lives one level up), `cjk_font_installed(font_path: str) ->
    bool` (today's `os.path.exists`).
  - `__init__.py`: dispatches on `platform.system()` (stdlib). On `"Darwin"`,
    re-exports the three functions from `macos.py`. On anything else, defines
    no-op equivalents (`open_file`/`switch_input_source` do nothing,
    `cjk_font_installed` returns `False`), mirroring `input_method.py`'s
    existing off-macOS guarantee.
- `browse.py::open_pdf` and `inspect.py::_open_pdf` call
  `idiomas.platform.open_file` instead of `subprocess.run(["open", ...])`
  directly; their `subprocess` import is dropped if nothing else in the file
  needs it (`inspect.py` still needs it for `nvim`).
- `input_method.py::_select_source` becomes a thin call into
  `idiomas.platform.switch_input_source`; the module's own
  `platform.system() != "Darwin"` check and `subprocess` import are removed
  (still true no-op, now enforced one layer down). Its `PINYIN_SIMPLIFIED_SOURCE_ID`
  / `ENGLISH_INTERNATIONAL_SOURCE_ID` constants and `switch_to_pinyin`/
  `switch_to_english_international` functions are unchanged — M6 is what
  replaces them with config-driven IDs, out of scope here.
- `doctor.py`'s font check calls `idiomas.platform.cjk_font_installed(CJK_FONT_PATH)`.

## 7. Update tests

- `tests/test_config.py`: replace entirely — cover `load_config()` reading a
  hand-written `config.toml` fixture (via `monkeypatch` on `CONFIG_PATH` to a
  `tmp_path`), `ConfigNotFoundError` when the file is absent,
  `Config.tree_root("Chinese")` deriving `root / "tree-Chinese"`, and
  `LanguageConfig` defaulting its input-method fields when the TOML omits
  them.
- `tests/test_doctor.py`: update for `run() -> list[Check]`; keep the same
  monkeypatch style (stub `shutil.which`, `idiomas.platform.cjk_font_installed`,
  `doctor._has_xecjk`) but assert on `Check.ok`/`.required`/`.message` and add
  cases for `macism`/`nvim` present and missing.
- `tests/test_tui_main_menu.py`, `tests/test_tui_landing_menu.py`,
  `tests/test_tui_entry_screen.py`: update `Config(...)` construction sites
  to the new `NotebookConfig`/`Config` split; add a landing-menu test that
  the options come from `app.config.languages`, not a hardcoded list, and
  that a registered-but-non-functional language still opens the placeholder.
- New test file `tests/test_platform.py`: on this (macOS) machine, asserts
  `idiomas.platform.open_file`/`switch_input_source`/`cjk_font_installed` are
  the `macos` module's functions (dispatch works); doesn't attempt to fake a
  non-Darwin run (no CI matrix for that yet — out of scope).

## 8. Hand-write the dev's config

- Create `~/.config/idiomas/config.toml` (outside the repo, not committed):
  ```toml
  user_name = "Nico"
  root = "/Users/you/Documents/Idiomas"

  [[languages]]
  name = "Chinese"

  [[languages]]
  name = "German"
  ```
- Note in `validation.md` that the dev still needs to move (or symlink) the
  existing `tree-Chinese/` content from the repo into
  `~/Documents/Idiomas/tree-Chinese/` by hand — this milestone doesn't
  migrate tree contents, only the config format (per Sprint 4 notes: moving
  `tree-Chinese/` out of the repo is the dev's own manual step).
- The repo's committed `.idiomas.toml` (old format, currently checked in) is
  left as-is or removed as a repo cleanup — flag to the dev during
  implementation rather than deciding unilaterally, since it's tracked in
  git.

## 9. Spec/design bookkeeping

- No change expected to `specs/current/design.md` — this milestone has no
  user-facing navigation/keybinding surface. `stack.md` gets the new
  architecture: config location, package-data templates, and the platform
  layer (per the roadmap's own deliverable line), added under a short new
  subsection.
- After the dev signs off, fold this milestone's Decisions into
  `specs/Sprint-4/guidelines/notes-sprint-4.md` (settled form), including the
  "one root folder, not per-language" correction to the roadmap's wording.
