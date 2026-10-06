# M4 · Install groundwork — validation

Grounded in the roadmap's done-when condition, made concrete below.

## Automated

Run the full suite:

```sh
pytest
```

All existing tests pass, updated per `plan.md`'s task 7, plus new coverage:

- [ ] `load_config()` reads a hand-written `config.toml` fixture into a
      `Config` with `user_name`, `root`, and a `languages` list of
      `LanguageConfig`.
- [ ] `load_config()` raises `ConfigNotFoundError` when
      `~/.config/idiomas/config.toml` doesn't exist.
- [ ] `Config.tree_root("Chinese")` returns `root / "tree-Chinese"`.
- [ ] A `LanguageConfig` with no input-method fields in the TOML defaults
      both to `""`.
- [ ] `doctor.run()` labels pandoc/xelatex/xeCJK/font as required and
      macism/nvim as optional, and reports each missing/present correctly
      (existing monkeypatch style, extended).
- [ ] `doctor.run()`'s font check reports Heiti SC (not Songti SC) as
      missing/present.
- [ ] `idiomas.platform.open_file`/`switch_input_source`/`cjk_font_installed`
      resolve to the `macos` module's implementations on this machine.
- [ ] The landing menu's options come from `app.config.languages`, not a
      hardcoded list; a registered-but-non-functional language (German)
      still opens the placeholder screen, not a real notebook.
- [ ] `MainMenuScreen`, `EntryScreen`, `BrowseScreen`, `InspectTreeScreen`
      tests pass against the `NotebookConfig` split (tree_root/language
      construction unchanged from the screens' point of view).

## Manual (dev sign-off)

- [ ] After `pip install -e .`, `which idiomas` resolves to a real
      executable, and running `idiomas doctor` from a directory outside the
      repo (e.g. `cd ~ && idiomas doctor`) works without error.
- [ ] With `~/.config/idiomas/config.toml` hand-written (task 8), launching
      `idiomas` from outside the repo opens the landing menu showing Chinese
      and German (from the config, not a hardcoded list).
- [ ] Selecting the Chinese notebook opens it against the configured tree
      (`~/Documents/Idiomas/tree-Chinese`, once the dev has moved their tree
      content there) — Entry, Browse, Inspect Tree and compiling all work
      exactly as before.
- [ ] Selecting German still shows "not implemented yet", unchanged from
      today.
- [ ] Renaming or removing `~/.config/idiomas/config.toml` and re-running
      `idiomas` (any subcommand) prints the clear "no config found" message
      with an example, and exits non-zero — no crash, no silent default.
- [ ] `idiomas doctor` reports Heiti SC (not Songti SC), and lists `macism`
      and `nvim` each marked required or optional, matching what's actually
      installed on the dev's machine.
- [ ] Compiling a file (`idiomas compile`, or the app's autocompile) still
      produces a correct PDF, proving `templates/xecjk.tex` is found via
      `importlib.resources` rather than the old repo-relative path — test
      this both from inside and outside the repo directory.
- [ ] Opening a PDF from Browse or Inspect Tree, and switching input methods
      from Entry's hanzi field, both still work — proving the platform-layer
      indirection didn't change behavior, only where the macOS calls live.
- [ ] `grep -rn "subprocess" src/idiomas --include=*.py` (excluding
      `platform/macos.py` and `compile.py`'s pandoc call) turns up only
      `nvim` — confirming no module outside the platform layer calls a
      macOS-only tool directly.
- [ ] `pytest` passes in full.
