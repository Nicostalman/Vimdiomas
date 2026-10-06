# M5 · Language kinds — plan

The task groups are ordered so that each one depends only on the groups
before it. Group 1 takes the "before" snapshot while the code is still
`main`'s. Groups 2–6 are the refactor. Group 7 is the "after" check, and
group 8 is the docs.

## 1. Baseline snapshot, before any code changes

- Write `check_equivalence.py` in this spec folder. It is a one-off
  verification tool for this milestone, not part of the package. Given a
  tree root and an output directory, it:
  - copies the tree into a scratch directory, and points `compile.CACHE_PATH`
    at a scratch cache so the dev's real cache and PDFs are never touched;
  - wraps `compile.subprocess.run` to record each pandoc call's argv (with
    the scratch template path normalised away) and stdin, then calls the real
    `run`;
  - runs `compile_all(copy, force=True)`, passing the Chinese kind if
    `compile_all` accepts one (so the same script runs on `main` and on the
    branch);
  - writes `calls.json` (per source file: markdown, argv, stamp from the
    scratch cache) and rasterises every PDF with `pdftoppm -r 100 -png` into
    `pages/`.
- Run it on the unmodified branch (identical to `main`) against
  `~/Documents/Idiomas/tree-Chinese`, into `scratchpad/m5-before/`.

## 2. The `languages` module

- Add `src/idiomas/languages.py` with `LanguageKind`, `Language`,
  `CHARACTER_PHONETIC`, `ALPHABETICAL`, `LANGUAGES`, `get_language` and
  `is_functional`, exactly as in `requirements.md` §1.
- Tests (new `tests/test_languages.py`):
  - Chinese is `CHARACTER_PHONETIC` and functional, and German is
    `ALPHABETICAL` and not functional;
  - `CHARACTER_PHONETIC.has_reading` is true and its `guess_reading("你好")`
    is `"ni3hao3"`. `ALPHABETICAL.has_reading` is false and its
    `guess_reading` is `None`;
  - `CHARACTER_PHONETIC.cjk_font == platform.CJK_FONT_NAME`;
  - `get_language("Klingon")` is `None`, and `is_functional("Klingon")` is
    `False`;
  - registry names are unique.

## 3. `Entry`'s fields, parser and writer

- `models.Entry`: rename `hanzi`, `pinyin`, `gloss` to `word`, `reading`,
  `translation`.
- `parser.py`: unpack into the new names.
- `writer.py`: write and check the new names. The error message uses
  `entry.word` and the new field names.
- Update every test that constructs or reads `Entry` by keyword
  (`test_parser`, `test_compile`, `test_store`, the TUI tests). No test is
  dropped.
- Existing round-trip tests must pass unchanged in what they assert:
  `parse(write(deck)) == deck` for every fixture, and every fixture file
  re-written byte-identically.

## 4. Config, landing menu, CLI, wizard and Input methods

- `config.py`: delete `FUNCTIONAL_LANGUAGES` and its comment. Add `kind:
  LanguageKind` to `NotebookConfig`.
- `landing.py` and `__main__.py`: use `is_functional`.
- `wizard.py`: `LANGUAGE_CHOICES = [language.name for language in
  LANGUAGES]`.
- `input_methods.py`: delete `LANGUAGE_HINTS`, and read
  `get_language(name).input_hints`, or `()` for an unknown name.
- `main_menu.py`: `_notebook_config()` fills `kind` from `get_language`. It
  is only reached for a functional language, so the entry exists.
- Tests:
  - the existing landing, wizard and input-methods tests pass unchanged;
  - new: a config naming a language that isn't in the registry
    (`"Klingon"`) shows it on the landing menu as "Not available yet." and
    opens the placeholder, and `idiomas compile` skips it.

## 5. The compiler takes the kind

- `compile.py`: add a required keyword `kind: LanguageKind` to
  `render_markdown`, `render_source`, `compile_file` and `compile_all`, and
  thread it through to `_run_pandoc` and `_stamp_for`. Both use
  `kind.cjk_font` in place of `CJK_FONT_NAME`. Drop the `CJK_FONT_NAME`
  import.
- `render_markdown`: pick `_render_grammar_table` or `_render_table` as today
  when `kind.has_reading`, and otherwise raise `NotImplementedError("…
  alphabetical rendering arrives in Sprint 6 M6")`.
- `base.autocompile_one`: take `kind=` and pass it on. Entry passes
  `self.config.kind`. Inspect Tree has no `NotebookConfig`, so it takes a
  required `kind=` of its own (`InspectTreeScreen(tree_root, *, kind)`, filled
  by `MainMenuScreen`) and passes `self.kind`. Inspect Tree's PDF-mode `compile_file` fallback
  passes it too, and so do `main_menu._run_compile` and `__main__._compile`.
  For the last of these, `get_language(language.name).kind`, after the
  `is_functional` guard.
- Tests (`test_compile.py`):
  - update every call to pass `kind=CHARACTER_PHONETIC`;
  - new: `render_markdown(..., kind=ALPHABETICAL)` raises
    `NotImplementedError`;
  - new: the pandoc argv carries `cjkfont=<CHARACTER_PHONETIC.cjk_font>`;
  - new: the stamp of a fixed deck equals a literal hex digest computed on
    `main` before this group, which guards that no existing stamp changes.

## 6. Entry builds its fields from the kind

- `entry.py`: rename `HanziInput` to `WordInput`, and `#hanzi`/`#pinyin` to
  `#word`/`#reading`. Placeholders come from `config.kind`. `#reading` is
  only composed when `kind.has_reading`. Every
  `query_one("#reading")` site (the display toggle, the clear, the create
  paths) handles its absence. `TAB_SKIP_IDS = {"reading"}`. The
  word-changed handler calls `kind.guess_reading` when set. Fix the comment in
  `panels.py` that names the "hanzi -> pinyin auto-fill".
- Tests (`test_tui_entry_screen.py`):
  - update ids and field names. Every existing Chinese behaviour test still
    asserts the same thing: the auto-fill, the tab order skipping the reading,
    create-and-clear, the grammar subtitle flow, and the input-source switch;
  - new: the Chinese placeholders are exactly "Hanzi" and "Pinyin";
  - new, **done-when "a table entry rather than a code change"**: with
    `languages.LANGUAGES` monkeypatched to add a
    `Language("Testonese", CHARACTER_PHONETIC, input_hints=())`, and a config
    registering it, the landing menu lists it as functional; its notebook
    menu opens; Entry shows Hanzi and Pinyin with pinyin guessed from typed
    hanzi; creating an entry writes the same row Chinese would; and Compile
    calls pandoc with the CJK font. Nothing outside the monkeypatched table is
    touched;
  - new: an Entry screen given a `NotebookConfig` with `kind=ALPHABETICAL`
    composes no `#reading`, shows "Word" as the word placeholder, `tab` goes
    from Word to Translation, and creating an entry writes `word<TAB><TAB>
    translation`. This pins the routing only. Whether that is German's real
    on-disk row is M6's call, and M6 may change this test.

## 7. Equivalence check, after

- Run `check_equivalence.py` on the finished branch into
  `scratchpad/m5-after/`, then diff the two outputs:
  - `calls.json` must be identical: every file's markdown, argv and stamp;
  - every page PNG must be byte-identical (`cmp`).
- Run the full test suite.
- Record the result (file count, and "identical") in `validation.md`'s
  checklist before handing off.

## 8. Docs

- `stack.md`: add the *Languages and kinds* section, and the field-name note
  under *Storage*, per `requirements.md` §5.
- `roadmap-sprint-6.md`: add a dated correction note under M5's done-when
  pointing to `requirements.md`'s *A correction to the roadmap's done-when*.
- `notes-sprint-6.md`: add *Settled while speccing M5*, with the four dev
  decisions and the done-when correction.
