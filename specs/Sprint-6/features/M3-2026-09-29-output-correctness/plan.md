# M3 · Output correctness — plan

Task groups, ordered so later groups depend only on earlier ones. Groups 1–2 are
`pinyin.py`, 3–5 the markdown/LaTeX generation, 6 the staleness cache, 7 Inspect
Tree, 8 docs.

Every group starts by **re-reproducing its finding as a failing test**, per
`notes-sprint-6.md`'s first Assumption. The report's real-Pandoc cases are
reproduced against real Pandoc, under the existing `integration` marker.

## 1. #4 — syllabic consonants

- `pinyin._SYLLABIC_CONSONANTS = {"n", "m", "ng", "hm", "hng"}` — what pypinyin
  produces with no vowel.
- `pinyin._COMBINING = {"1": "\u0304", "2": "\u0301", "3": "\u030c", "4": "\u0300"}`.
- `to_tone_mark_syllables`: when `_mark_vowel_index` finds no vowel and the
  letters are a syllabic consonant, mark its `n` or `m` (the `n` of
  `ng`/`hng`, the `m` of `hm`) with the combining diacritic and `unicodedata.normalize("NFC", ...)` the result — giving `ń`/`ň`/`ǹ`
  and `ḿ` precomposed, `m̄`/`m̌`/`m̀` and the `ng` forms combining.
- When the letters are neither markable nor a known syllabic consonant: return
  the letters unchanged (tone digit dropped) and record the syllable so a caller
  can report it. `to_tone_mark_syllables` gains no new exception path — it never
  raises for tone marking again.
- Reporting: `to_tone_mark_syllables(numbered, *, unsupported: list[str] | None = None)`
  appends each such syllable to the list when one is passed; `to_tone_marks`
  forwards it.
- Tests (`test_pinyin.py`), the report's regression line:
  - `to_tone_marks("n2")` → `ń`; `to_tone_marks("m2")` → `ḿ`; `m1`, `m3`, `m4`,
    `n1`, `n3`, `n4`, `ng2`, `hm5`, `hng4` all produce a marked form and raise
    nothing.
  - `guess("嗯")` and `guess("呣")` fed straight into `to_tone_marks` raise
    nothing (the report's exact two-line reproduction).
  - A genuinely unmarkable syllable returns its letters and is appended to
    `unsupported`.
  - Every existing tone-mark test is unchanged.

## 2. #19 — non-hanzi segments

- The `_HANZI_RANGES` / `_is_hanzi` pair moves from `compile.py` to `pinyin.py`
  as `is_hanzi`, so the guesser and the renderer's pairing use one
  definition; `compile.py` imports it.
- `pinyin.guess`: send each run of consecutive hanzi to pypinyin whole, which
  keeps word context (`银行` → `yin2hang2`), and join the results. Non-hanzi
  characters contribute nothing.
- `pinyin._SYLLABLE_RE` becomes `([a-zü:]+)([0-5])` — lowercase only.
- Tests (`test_pinyin.py`), the report's table exactly:
  - `guess("T恤")` → `xu4`; `guess("3D打印")` → `da3yin4`; `guess("X光")` →
    `guang1`; `guess("卡拉OK")` → `ka3la1`.
  - `guess("牛肉")` → `niu2rou4` — unchanged for ordinary input (an existing
    test).
  - A value already on disk renders as if freshly guessed:
    `to_tone_marks("Txu4")` → `xù`, `to_tone_marks("3Dda3yin4")` → `dǎyìn`.
- Tests (`test_compile.py`): `_pair_hanzi_pinyin("T恤", guess("T恤"))` pairs `T`
  with `""` and `恤` with `xù` — the report's "Grammar pairing" column.

## 3. #10 — single-pass LaTeX escaping

- `compile._LATEX_ESCAPES` gains `"\\": r"\textbackslash{}"`.
- `compile._escape` becomes a single `re.sub` over a class built from the
  table's keys, with a lambda looking each match up — no sequential
  `str.replace`.
- Tests (`test_compile.py`), the report's regression line: `_escape("a\\b")` is
  `a\textbackslash{}b` (not `a\textbackslash\{\}b`); `_escape("a\\{b}")` escapes
  the braces the user typed and not the ones the replacement introduced; a
  string with every special character at once; and an integration test compiling
  a translation of `a\b` and asserting `pdftotext` extracts `a\b`.

## 4. #13 — heading escaping

- `compile._escape_markdown(text)`: backslash-escape every ASCII punctuation
  character (`string.punctuation`) except `' " - .`, pandoc's smart-typography
  characters (see requirements' *Refinements*).
- `render_markdown`: `## {_escape_markdown(category.name)}` and
  `### {_escape_markdown(subtitle.name)}`.
- Tests (`test_compile.py`), the report's regression line — real Pandoc runs for
  attribute braces, trailing `#`, `*`/`_`, backslashes and `$` in category and
  subtitle names:
  - `_escape_markdown` unit cases for each.
  - Integration: a deck whose categories are `Food {#drinks}`, `Level 2 #`,
    `*Very* common`, `C:\new words`, `a_b_c` and `100$` compiles, and
    `pdftotext` shows each heading **verbatim**, including `C:\new words`, which
    fails to compile today.
  - The same set as subtitle names in a grammar deck.

## 5. #5 — the YAML title

- `compile._yaml_title(title)`: a title of plain letters and single spaces
  that is not a YAML keyword is emitted as-is. Otherwise `_escape_markdown(title)`
  first, then drop control characters, then escape `\` → `\\` and `"` → `\"`,
  then wrap in `"`. A comment states the ordering and why it cannot be
  reversed.
- `render_markdown`: `f"title: {_yaml_title(deck.title)}"`.
- Tests (`test_compile.py`), the report's regression line — real Pandoc metadata
  parsing for colons, hash signs, quotes and bracket characters in titles:
  - The report's two cases: `Food: fruit` compiles (exit 0, not 64) and its
    title is `Food: fruit`; `Food # drink` compiles and its title is
    `Food # drink`, not `Food`.
  - A title containing `"`, `\`, `[`, `]`, `*` and `:` together.
  - Titles are read back out of the PDF (`pdftotext` first page, or pandoc's own
    AST via `-t json` for the metadata assertion, whichever the existing
    integration tests already do for titles).

## 6. #11 — every compile path records its stamp

- `compile.render_source(source_path, *, grammar) -> Render`: parse, render,
  stamp, and collect #4's unsupported syllables. One place; used by both
  callers below.
- `compile._run_pandoc(markdown, notebook_path)`: the subprocess call, split
  out of `compile_file` unchanged. It is the seam the compile tests fake.
- `compile_file(source_path, notebook_path, *, grammar=False, cache=None, render=None)`:
  - use the `render` `compile_all` passes, or call `render_source`;
  - run pandoc through `_run_pandoc`;
  - **on success**, record the stamp: into `cache` if one was passed, otherwise
    load → set → save the cache itself.
- `compile_all`: load the cache once, `render_source` per file for the skip
  decision, pass its own `cache` dict (and the precomputed render) into
  `compile_file`, and save once in the `finally` M2 added. A failed file records
  nothing.
- `base.autocompile_one` and `inspect._open_pdf` need no change — they call
  `compile_file` with no `cache` and so now record by default. Assert that in a
  test rather than relying on it.
- Tests (`test_compile.py`), the report's regression line — compile_all →
  autocompile a changed source → revert the source → compile_all must rebuild:
  - The report's four-step reproduction exactly, with a temporary cache path,
    asserting the final `compile_all` returns the file as compiled and the PDF
    content matches the reverted source (`pdftotext`).
  - `compile_file` called standalone on a fresh cache writes a stamp; a
    following `compile_all` then skips that file.
  - A file that fails to compile writes no stamp, and the next run retries it.
  - `force=True` still recompiles and still records (existing behaviour).
- Existing compile_all tests that faked `compile_file` and depended on the
  cache move their fake down to `_run_pandoc`, so the recording they test is
  the real one.
- `tests/conftest.py`: an autouse fixture points `CACHE_PATH` at a temp path
  for every test, since the TUI tests' autocompiles now record too.
- Tests (`test_tui_entry_screen.py`): after an in-app edit and its
  autocompile, the cache holds the new stamp.

## 7. #4's diagnostic, and #17

- `compile.CompileWarning` dataclass `(source: Path, message: str)`;
  `CompileReport` (M2) gains `warnings: list[CompileWarning]`.
- `render_markdown` collects unsupported syllables (group 1's `unsupported`
  list) and `compile_all` turns them into one `CompileWarning` per file naming
  the syllables, for every file in the tree, rebuilt or not.
- `main_menu.compile_summary` (M2) gains a `Warnings:` block below `Failed:`;
  `__main__._compile` prints them to stderr without affecting the exit code.
- `inspect.action_rename`, both branches: the collision check becomes
  "exists **and** is not the same file as the source"; when it is the same file,
  rename through a unique temporary name in the same parent directory, then to
  the target, restoring the original name if the second step fails. The `.pdf`
  sibling follows the way it already does, removed and recompiled under the
  new name. A rename to the unchanged name is a no-op.
- Tests (`test_tui_inspect_tree.py`), the report's regression line — case-only
  rename of a file and of a directory:
  - `food` → `Food` succeeds; the file is `Food.md`, its header is `# Food`, and
    its PDF moved with it.
  - The same for a directory.
  - `food` → `Food` when a genuinely different `Food.md` exists (possible only
    on a case-sensitive filesystem) is still refused — the test asserts the
    `samefile` decision directly so it is meaningful on both platforms, with the
    end-to-end case-only rename skipped where the filesystem is case-sensitive.
- Tests (`test_compile.py` / `test_tui_main_menu.py`): a deck containing a
  genuinely unmarkable syllable produces a `CompileWarning`, the file still
  compiles, and the summary screen shows the warning.

## 8. Docs

- `specs/current/stack.md`:
  - the *Pinyin* section gains: syllabic consonants are supported and marked
    with combining diacritics NFC-normalised; `guess()` emits syllables for
    hanzi characters only; an unmarkable syllable prints its letters and is
    reported.
  - the *PDF* section gains: headings and the title are markdown-escaped (and
    the title additionally YAML-quoted) while entry cells are LaTeX-escaped, and
    why the two differ; and that **every** compile path records its stamp, so
    the cache can no longer describe an older source than the PDF.
- `specs/current/design.md`: the compile results screen's *Warnings* block,
  alongside M2's *Failed* block.
- Note in the PR that this milestone invalidates the stamps of any file whose
  headings, title or entries contain the characters now escaped, so the first
  Compile after merging rebuilds them once. The PDFs are identical except where
  the bug was visible.
- Update this milestone's three spec files as anything changes during
  implementation.
