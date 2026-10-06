# M6 · The German notebook — plan

The task groups are ordered so that each one depends only on the groups
before it. Group 1 takes the Chinese "before" snapshot while the code is still
`main`'s. Groups 2–6 are the work. Group 7 is the Chinese "after" check, and
group 8 is the docs.

## 1. Chinese baseline, before any code changes

- Run M5's
  [`check_equivalence.py`](../M5-2026-10-01-language-kinds/check_equivalence.py)
  on the unmodified branch (identical to `main`) against
  `~/Documents/Idiomas/tree-Chinese`, into `scratchpad/m6-before/`. It copies
  the tree and uses a scratch cache, so the real tree and cache are never
  touched. The script stays in M5's folder: it is read and run from there,
  not copied or edited.

## 2. The parser and writer take the kind

- `parser.parse(text, filename_stem, *, kind, grammar=False)`: row threshold
  and unpacking by `kind.has_reading`, as in `requirements.md` §2. The note
  check stays ahead of the row check.
- `writer.write(deck, *, kind)` and `writer.save(deck, path, *, kind)`:
  - `_render_entries` emits the reading column only for a kind with a
    reading;
  - for a kind without one, a non-empty `reading` raises `ValueError` naming
    the entry.
- Add `kind=CHARACTER_PHONETIC` to every existing `parse`/`write`/`save`
  call in the tests.
- New tests in `test_parser.py` (alphabetical):
  - a vocabulary fixture with categories, uncategorized rows, a note, a
    tab-indented note, tags and an extra field parses as expected, with
    `reading == ""` throughout;
  - `Haus<TAB>` is a row with an empty translation;
  - a line with no tab is an unrecognized line, as for Chinese;
  - `Haus<TAB><TAB>house` reads as `word="Haus"`, `translation=""`,
    `extra_fields=["house"]`;
  - a grammar fixture with subtitles parses with `grammar=True`;
  - **the round trip:** `parse(write(deck, kind=ALPHABETICAL),
    kind=ALPHABETICAL) == deck`, and both German fixtures re-write
    byte-identically;
  - the writer refuses an alphabetical entry with a reading;
  - the same German text parsed with `CHARACTER_PHONETIC` yields no entries:
    this pins the kind as the thing that decides.
- New fixtures: `tests/fixtures/german/Essen.md` (vocabulary) and
  `tests/fixtures/german/Grammar/Konjunktionen.md` (grammar, with subtitles).

## 3. The store and Browse take the kind

- `store.walk(root, *, kind)` and `store.tag_index(root, cache=None, *,
  kind)` pass it to `parse`.
- `browse.paths_with_tag(tree_root, tag, *, kind)` and
  `BrowseScreen(tree_root, *, kind)`. `MainMenuScreen` passes
  `config.kind`.
- Entry and Inspect Tree pass their kind to `walk`. Entry's `_read_deck` and
  its four `save` calls pass `self.config.kind`.
- Update the store, Browse, Entry and Inspect tests' calls.
- New test in `test_store.py`: `walk` on a German tree reports
  `has_uncategorized` for a file whose only entries are uncategorized
  two-column rows.

## 4. The renderer and the template

- `templates/xecjk.tex`:
  - wrap `\usepackage{xeCJK}` and `\setCJKmainfont{$cjkfont$}` in
    `$if(cjkfont)$ … $endif$`, and update the header comment;
  - add `\GrammarWord{#1}` next to `\HanziPinyin`, setting `#1` in
    `\Large` with its own line spacing, so a wrapped phrase doesn't collide.
- `compile.py`:
  - `_render_table(entries, kind, unsupported)`: one `l` per column, and
    the reading cell only when `kind.has_reading`;
  - `_render_grammar_table(entries, kind, unsupported)`: the head line is
    the `\HanziPinyin` run or `\GrammarWord{word}`, and the rest is shared;
  - `render_markdown` drops its `NotImplementedError` and passes `kind` on;
  - `_run_pandoc` adds `-V cjkfont=…` only when `kind.cjk_font` is set;
  - `_stamp_for` hashes `kind.cjk_font or ""`.
- Tests in `test_compile.py`:
  - replace the `NotImplementedError` test;
  - alphabetical vocabulary markdown: two-column spec, `{\Large word} &
    translation`, and the note as an italic parenthetical;
  - alphabetical grammar markdown: `\GrammarWord{…}` head line, the
    translation, the note line, and the gaps;
  - escaping applies to the word as it does to the hanzi;
  - the pandoc argv for alphabetical has no `cjkfont`, and for Chinese still
    has it;
  - a stamp for `ALPHABETICAL` doesn't raise and differs from Chinese's for
    the same markdown;
  - the existing Chinese render tests are unchanged in what they assert.
  - **The literal-digest stamp test** (computed on `main` in M5) is
    unchanged: it hashes the stand-in bytes `b"tmpl"`, not the real template,
    so the template edit doesn't reach it. (The plan expected it to change.)
    A test that the template loads `xeCJK` only under `$if(cjkfont)$` covers
    the edit instead.
- **Real pandoc, real xelatex:** compile both German fixtures to PDF in the
  test suite's real-toolchain tier (wherever the M3 real-Pandoc tests live),
  and include a grammar entry long enough to wrap.

## 5. German becomes functional

- `languages.py`: drop German's `functional=False`, and make the
  `ALPHABETICAL` comment final rather than provisional.
- Tests:
  - `test_languages.py`: German is functional;
  - `test_tui_landing_menu.py`: German's description and the notebook menu
    opening;
  - drop the dirty-set workaround from M5's alphabetical Entry test.
- Entry tests for German, extending M5's routing test:
  - a German notebook on a fixture tree shows the categories,
    `(uncategorized)` and `(new category)`;
  - creating an entry writes `Haus<TAB>house` under the right category, and
    clears the form;
  - on a grammar file, the Subtitle field appears, and `(new subtitle)`
    creates the subtitle and the entry under it;
  - `tab` order is Word → Translation → Note;
  - leaving the screen autocompiles with the alphabetical kind (the compile
    is faked, as in the existing autocompile tests).
- `idiomas compile` test: a config with German compiles its tree.

## 6. Chinese unchanged, and the full suite

- Run the full suite and fix anything the signature changes missed.

## 7. Chinese "after" check

- Re-run `check_equivalence.py` on the branch into `scratchpad/m6-after/`.
- Diff the two outputs:
  - per file, the markdown and argv are identical, and only the stamps
    differ;
  - every page PNG is `cmp`-identical.
- Record the result in `validation.md`.

## 8. Docs

- `stack.md` and `design.md`, as in `requirements.md` §6.
- Any mechanism or adjustment settled during implementation (for example
  `\GrammarWord`'s exact definition, or a gap retuned after the dev's look)
  goes into `requirements.md` and `design.md` when it's settled, not at the
  end.

## 9. After hand-testing: the notebook's folders, and long words

*(`requirements.md` §7 and §8.)*

- `store.ensure_tree(tree_root)`: create the tree folder, then `Vocabulary` and
  `Grammar` in it unless a folder of that name in any case is already there.
  Call it from the wizard's `_write` and from `MainMenuScreen` when it mounts.
  Tests: it creates both in an empty tree and a missing tree; it leaves an
  existing `grammar/` alone and creates no second one; it never touches
  existing files; the wizard's new trees have both; opening the notebook menu
  completes a tree with only `Vocabulary/`.
- `compile.py` (`requirements.md` §8, every kind): an em-width estimate;
  `_exception_rows(widths, columns)` picks the rows set apart (word wider than
  `WORD_CAP_EM`, then the row that most reduces the table's width while it
  exceeds the line); `_render_table` renders an exception row as a
  `\multicolumn` over every column holding a hanging-indent paragraph.
  Tests: a table that fits has no exception; a long word, and a row whose
  translation overruns, each become one; the exception is the row responsible,
  not its neighbours; it works for three columns and skips an empty reading;
  an existing Chinese fixture is unchanged; real toolchain, German and
  Chinese, no word past the margin and an indented continuation.
- `templates/xecjk.tex`: `\HanziPinyin` allows a break after each unit. Test
  with a long Chinese grammar phrase, real toolchain.
- Re-run `check_equivalence.py` (group 7): Chinese is unchanged.
- A test that the notebook menu's Compile of one language compiles only that
  language's tree, with two languages configured.
