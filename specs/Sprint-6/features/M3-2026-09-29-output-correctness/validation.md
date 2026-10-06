# M3 · Output correctness — validation

Grounded in the roadmap's done-when condition, made concrete.

## Regression coverage, finding by finding

Each row is the report's own *Regression coverage* line and the test that
satisfies it. Every one is **written failing first**, against the current code.
The report's real-Pandoc cases run against real Pandoc, under the existing
`integration` marker — the roadmap's done-when requires it explicitly.

| # | Report's coverage line | Test |
|---|---|---|
| 4 | guessed pinyin through both PDF rendering modes for `嗯` and `呣`, and the worker's render-error path | `test_pinyin.py` (the two-line reproduction), `test_compile.py` (vocabulary **and** grammar rendering, integration), `test_tui_entry_screen.py` (autocompile after entering `嗯` raises nothing) |
| 5 | real Pandoc metadata parsing for colons, hash signs, quotes and bracket characters in titles | `test_compile.py`, integration: `Food: fruit`, `Food # drink`, and a title with `"`, `\`, `[`, `]`, `*`, `:` |
| 10 | literal backslash alone and next to braces, plus a real PDF output check | `test_compile.py`: `_escape` unit cases and an integration compile of `a\b` read back with `pdftotext` |
| 11 | compile_all → autocompile a changed source → revert the source → compile_all must rebuild | `test_compile.py`: the report's four-step reproduction against a temp cache, plus standalone-`compile_file` stamping and the failed-file retry |
| 13 | real Pandoc runs for attribute braces, trailing `#`, `*`/`_`, backslashes and `$` in category and subtitle names | `test_compile.py`, integration: six category names and the same set as subtitles in a grammar deck, each read back verbatim |
| 17 | case-only rename of a file and of a directory | `test_tui_inspect_tree.py`: end-to-end on a case-insensitive filesystem, and the `samefile` decision asserted directly so the test means something on Linux too |
| 19 | guess → vocabulary rendering → grammar pairing for mixed Latin/digit/hanzi words | `test_pinyin.py` (the report's four-row table) and `test_compile.py` (rendering and `_pair_hanzi_pinyin` for each) |

## Automated

- `.venv/bin/python -m pytest -q` — the full suite passes, integration tests
  included.
- **The done-when's three named checks**, each its own test:
  - the **compile → autocompile → revert → compile** sequence rebuilds, and the
    rebuilt PDF matches the reverted source;
  - **`嗯` compiles and prints correctly** — through both the vocabulary table
    and the grammar stacked layout, with `pdftotext` asserting the marked form;
  - **`T恤` compiles and prints correctly** — `xù` under 恤, nothing under `T`,
    in both layouts.
- **`C:\new words` as a category name compiles.** It fails outright today; after
  this milestone the file produces a PDF with that heading verbatim. (M2 made
  the failure survivable; this is where it stops failing.)
- **`to_tone_marks` never raises.** A property test over every third
  codepoint of CJK Unified Ideographs (~7,000 hanzi): each one goes through
  `guess` → `to_tone_marks` without an exception and with nothing reported
  unsupported.
- **Ordinary output is unchanged.** `render_markdown` for a deck whose headings,
  title and entries contain no punctuation is byte-identical to today's, so the
  one-time rebuild is scoped to files that actually contain the characters now
  escaped.
- **Headings keep their typography.** `Don't -- stop... "now"` passes through
  `_escape_markdown` unchanged, so pandoc still curls its quotes and sets its
  dashes and ellipsis.

## Expected one-time rebuild

`_stamp_for` hashes the intermediate markdown, so correctly changing what the
generator emits invalidates the stamps of every file it changes for. After
merging, the first Compile rebuilds any file whose **headings contain ASCII
punctuation other than `' " - .`**, whose **title is anything but letters and
single spaces** (a digit is enough: `HSK 1`), whose **entries contain a
backslash**, or whose **stored pinyin has a capital or non-hanzi prefix**
(`Txu4`). This is expected,
not a regression; the resulting PDFs are identical to the previous ones except
where the bug was visible. Called out here so it is not mistaken for #11
misbehaving.

## Manual, by the dev

The roadmap's bar is *the dev confirms the PDFs by eye*, so these are read, not
just run.

- [ ] **#11, the one that matters.** *Compile* the real tree until it reports
      everything up to date. Open *Enter vocabulary*, add an entry to a file,
      leave (it autocompiles). Now undo that edit outside the app — `git
      checkout` the file, or delete the line in nvim. Run *Compile* again: it
      **rebuilds that file**, and the PDF no longer shows the entry you removed.
      Today it reports nothing to do and the PDF keeps the entry.
- [ ] **#4.** Add an entry with hanzi `嗯` and one with `呣`. Both save, both
      autocompile without an error notification, and both print with a tone mark
      over the consonant in the PDF. Check the grammar layout too — add one to a
      file under `Grammar/`.
- [ ] **#19.** Add `T恤`, `3D打印`, `X光` and `卡拉OK`. In the form, the pinyin
      field shows only the hanzi's pinyin (`xu4`, `da3yin4`, `guang1`, `ka3la1`).
      In the vocabulary PDF they print as `xù`, `dǎyìn`, `guāng`, `kǎlā`. In a
      grammar file, the pinyin sits under the **hanzi** characters and nothing
      sits under `T`, `3D`, `X` or `OK`.
- [ ] **#19, old data.** If your tree already holds an entry like `T恤` with
      `Txu4` stored, compile it: it now prints `xù`, and the file on disk is
      **unchanged** — it still says `Txu4` until you re-save that entry.
- [ ] **#13.** Create categories named `Food {#drinks}`, `*Very* common` and
      `C:\new words`. Compile. All three files compile, and each heading prints
      exactly as typed — braces, asterisks and backslash included.
- [ ] **#5.** Create files named `Food: fruit` and `Food # drink`. Both compile,
      and each PDF's title is the full filename, not a truncated one.
- [ ] **Typography.** A category named `Don't -- stop...` prints with a curly
      apostrophe, an en dash and an ellipsis, the same as before.
- [ ] **#10.** Add an entry whose translation is `a\b`. The PDF shows `a\b`, not
      `a\{}b`.
- [ ] **#17.** *Inspect tree* → `r` on a file → change only its capitalisation
      (`food` → `Food`). The rename **succeeds**; the file is `Food.md`, its
      header is `# Food`, and its PDF is there. Same for a directory.
- [ ] **The rebuild.** The first Compile after merging rebuilds more files than
      usual. Confirm the PDFs it produced look the same as before, except the
      ones this milestone was fixing.

## Merge bar

All automated checks pass, the seven regression tests above are present and
green with the real-Pandoc cases run against real Pandoc, the three done-when
checks pass, and the dev confirms the manual list **by eye on the PDFs**.
