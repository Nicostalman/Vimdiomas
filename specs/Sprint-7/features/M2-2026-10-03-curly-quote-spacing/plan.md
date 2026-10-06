# M2 · Curly-quote spacing — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Tests first for the Python side (§2, §3)

- `tests/test_compile.py`, unit, no external tools:
  - The quote function: every case in `validation.md` §1's table.
  - `_escape`'s callers: `render_markdown` for a vocabulary entry with
    `a "b" c` in word and translation (not reading), and in a note, for both kinds.
  - Grammar: `他说"你好"` renders `“` and `”` in the right `\HanziPinyin`
    units, and an alphabetical grammar word is curled whole.
  - `render_markdown` is unchanged for entries with no `"`: an existing
    fixture's output is compared to what it was.
- Run them. They fail, for the right reason.

## 2. The Python (§2, §3)

- `compile.py`: the quote function, applied to each field before `_escape` in
  `_render_table` and `_render_grammar_table`, including `entry.word` before
  `_pair_hanzi_pinyin`.
- The tests of group 1 pass.

## 3. Integration tests for the PDF (§1)

- In `tests/test_compile.py`, marked `integration`, next to `_right_edge_pt`: a
  helper that returns the words of a PDF with their boxes from `pdftotext
  -bbox`, skipping when `pdftotext` is missing.
- Chinese (`CHARACTER_PHONETIC`):
  - A heading, a category, a file title and an entry each with `a "b" c`
    (heading and title via pandoc's `smart`; entry typed with `“b” c`): the
    words include `“b”` and `c` as **separate** tokens, and not `“b”c`.
  - `a -- b`, `a --- b` in a heading: `–`/`—` is its own token with a gap on
    both sides.
  - `a ... b` in a heading: the text contains `…` and not `⋯`.
  - A typed `，` or `。` followed by a space and a Latin word in an entry keeps it. (Followed by a hanzi: not specified, see `requirements.md`.)
  - **The genuine-quote pin:** `他说“你好”再见` in a heading, and as an
    entry's translation, stays **one** token: no gap is added around the quotes.
- German (`ALPHABETICAL`): an entry `a "b" c` has `“b”` and `c` as separate
  tokens and the first quote is the opening one.
- They fail before the template change, apart from the pin and the German
  heading, which pass before and after.

## 4. The template (§1)

- `xecjk.tex`: the patch and the class line, inside `$if(cjkfont)$`, with their
  comment.
- The integration tests of group 3 pass.
- A structural test: the patch's lines sit between `$if(cjkfont)$` and
  `$endif$`, so an alphabetical PDF never gets them.

## 5. The guard, once (§1)

Manual, run by the agent and reported:

- Compile a Chinese file with a scratch copy of the template whose patch
  names a macro that does not exist (`\xeCJK_NoSuchMacro:`). It compiles, and
  the space after `”` is swallowed, as it is today.
- Compile one with the real template on the same file. It compiles and
  keeps the space.

## 6. Linux (§1)

- If Docker is available, build `docker/Dockerfile` and run the integration
  tests inside the Arch container, whose xeCJK is older than this machine's.
  They pass, or the failure shows exactly what the older xeCJK needs.
- If Docker is not available, say so; the dev decides whether to run it. The
  guard already means an older xeCJK cannot fail a compile.

## 7. Specs and docs (§ Docs)

- `specs/current/stack.md`: the note.
- Anything learned during the implementation goes into these three files first.

## 8. Hand off

- Full suite: `pytest` (with integration), and the lint the project uses.
- Stop for the dev's manual pass (`validation.md` §4). Not done until the dev
  says so.
- After the merge: settle M2's decisions and Postponed rows in
  `notes-sprint-7.md`.
