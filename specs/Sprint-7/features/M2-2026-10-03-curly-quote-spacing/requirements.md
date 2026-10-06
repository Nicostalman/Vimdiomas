# M2 · Curly-quote spacing — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-7.md`](../../roadmap-sprint-7.md), *M2 · Curly-quote
spacing*:

> **Deliverable.** A closing curly quote followed by a space keeps the space in a
> Chinese PDF, in a title, a heading, a category and an entry. The fix is a
> setting in `src/idiomas/templates/xecjk.tex` (xeCJK's punctuation classes, or
> equivalent), with no change to the markdown or the parser. Alphabetical PDFs
> come out byte-for-byte as before. Sprint 5 M2's staleness rules make every
> Chinese file rebuild on the next Compile, because the template changed.
>
> **Done when.** A Chinese file with `a "b" c` in a heading and in an entry
> compiles with the space intact, checked by an automated test. The dev's real
> Chinese notebooks recompile with no visible change except the restored spaces,
> and the dev confirms by eye. The full test suite passes.

The bug came out of Sprint 6 M3 and was recorded in `notes-sprint-6.md`'s
Postponed table: xeCJK treats `”` as full-width CJK punctuation, so `a "b" c`
prints as `a “b”c`.

This milestone widens the roadmap's text in the ways the spec conversation
settled (see *Decisions*). Where the two differ, **this file wins**:

- It also fixes `…` printing as a mid-height `⋯` in Chinese PDFs.
- It also fixes a straight `"` typed in an entry, which printed as `”b”` in
  every language. That changes alphabetical PDFs for entries containing a `"`.
- "Byte-for-byte" is read as *same text and same positions*: a PDF is never
  byte-identical between two compiles (it carries a creation timestamp).

## What was measured

Before specifying, the bug was reproduced and four candidate fixes were compiled
against the real template (`xelatex` from TeX Live 2026, Songti SC). Every
claim below was measured on this machine, with `pdftotext -bbox`.

- **The cause.** In `xeCJK.sty`, `’ ” – — …` and the other CJK punctuation are
  class *FullRight*. When a space follows a FullRight character, xeCJK's
  `\xeCJK_FullRight_and_Boundary:` ends with `\ignorespaces`, which drops it. It
  is there so a hard-wrapped line of Chinese source does not print a gap.
- **What is affected.** A typed space after `”` `’` `—` (from `---`) and `…`
  (from `...`). `–` (from `--`) is *not* affected: it keeps its space in the
  unpatched template too (found at implementation, and pinned by a test). The opening `“` `‘` are FullLeft and keep the
  space *before* them. The straight `"` in an entry is not affected: TeX reads
  it as an ASCII character, not as U+201D.
- **Where it shows.** The title, `##` and `###` headings (pandoc's `smart`
  extension turns `"b"`, `--`, `---` and `...` into the Unicode characters), and
  any entry text where the user typed the Unicode character themselves.
- **`...` also prints the wrong glyph.** In a Chinese heading it comes out as
  `⋯`, the CJK font's mid-height ellipsis, because FullRight characters are set
  in the CJK font.
- **Rejected: `\xeCJKsetup{LatinPunct}`.** It fixes the spaces, but it makes
  `“你好”` use Latin Modern half-width glyphs and adds about 3.9pt of glue
  between the hanzi and the quote (measured: a line of hanzi with four quotes
  grew by 18.6pt). It does not cover `–` and `—`. Genuine hanzi quotes would
  change, which the roadmap rules out.
- **Rejected: `\xeCJKsetup{CheckFullRight}`.** It has no effect on this.
- **Rejected: declaring `“ ” ‘ ’ – — …` as `Default` class.** The spaces come
  back, but `“你好”` prints as `“ 你好 ”`, with a gap on both sides.
- **Chosen:** keep xeCJK's classes, and make `\xeCJK_FullRight_and_Boundary:`
  stop at the end of its own body instead of ignoring the spaces after it. The
  same text, `他说“你好”他说，说“你好”他说。她说‘你好’了——好的。` (no typed
  spaces), compiles to **identical** `pdftotext -bbox` output with and without
  the change, and `a “b” c` keeps both spaces.

## Decisions

| Decision | Rationale |
| --- | --- |
| **The fix keeps typed spaces: `\ignorespaces` is removed from xeCJK's FullRight-then-space macro** | Asked in the spec conversation, over `LatinPunct`. It leaves genuine full-width quotes and every non-space case byte-identical in layout. |
| **Every full-width punctuation character keeps a typed space before a Latin character** (`，` `。` `、` `）` `」` as well as `” ’ — …`) | Asked. The macro does not look at which character it follows, and a per-character list would need more of xeCJK's internals. The source's spaces are the author's. **Limit, found at implementation:** this is about a Latin character after the space. A space between full-width punctuation and a *hanzi* (`二。 三`) is a different case: measured, it is dropped in a heading on this machine, kept in an entry on this machine, and dropped in an entry on Linux (Noto Serif CJK SC). It follows xeCJK's own CJK-to-CJK handling, which varies by context and font, and Chinese is not typed with spaces there. It is not specified and not tested. |
| **`--wrap=none` is *not* added to the pandoc call** | The first draft added it, so a wrap after `，` would not print a gap. Measured at implementation: pandoc wraps only at spaces, which are the author's already, so a wrapped long Chinese heading compiles to identical `pdftotext -bbox` output with and without it. It did nothing, and was dropped. |
| **U+2026 `…` is declared `Default` class** | Asked: "yes, fix it too". `...` in a heading prints as Latin Modern's `…` and not `⋯`. **Consequence, accepted:** a real Chinese `……` also prints with the Latin glyph and gains xeCJK's usual hanzi/Latin glue. |
| **A straight `"` in an entry becomes `“` or `”`, for every language** | Asked: "yes, add it to M2". Entry text is raw LaTeX, where TeX turns `"` into `”` at both ends. Headings are untouched: pandoc already curls them. |
| **A straight `'` in an entry is not changed** | Not asked. TeX already prints it as `’`, which is right for `don't` and wrong for an opening `'x'`, but a rule cannot tell `'x'` from `'tis` or `'90s`. Postponed. |
| **The patch is guarded and degrades to today's behaviour** | The macro is an xeCJK internal. On a TeX Live without it (or with a body that has no `\ignorespaces`), the lines do nothing and the PDF compiles as it does now. A missing name must never fail a compile. |

## Scope

### In

- `src/idiomas/templates/xecjk.tex`: the patch and the `…` class, inside the
  existing `$if(cjkfont)$` block.
- `src/idiomas/compile.py`: curling a straight `"` in entry text.
- Tests, and the docs listed under *Docs*.

### Out

- **The markdown, the parser and `store.py`.** What is written to disk does not
  change. The quote is curled when the PDF is rendered, so the source `.md`
  keeps the `"` the user typed.
- **A straight `'` in an entry** (see Decisions).
- **Spacing before an opening `“` or `‘`.** Not broken.
- **How `……` and `——` look in real Chinese text** beyond the `…` consequence
  above.
- **Alphabetical templates.** The patch and the class line are inside
  `$if(cjkfont)$`, so an alphabetical PDF still never loads xeCJK.

## 1. The template

Inside the `$if(cjkfont)$ … $endif$` block, after `\setCJKmainfont`:

```latex
\ExplSyntaxOn
\tl_new:N \g_idiomas_fullright_tl
\cs_if_exist:NT \xeCJK_FullRight_and_Boundary:
  {
    \tl_gset:Ne \g_idiomas_fullright_tl
      { \exp_not:o { \xeCJK_FullRight_and_Boundary: } }
    \tl_gremove_all:Nn \g_idiomas_fullright_tl { \tex_ignorespaces:D }
    \tl_gremove_all:Nn \g_idiomas_fullright_tl { \ignorespaces }
    \cs_gset_protected:Npn \xeCJK_FullRight_and_Boundary: { \g_idiomas_fullright_tl }
  }
\ExplSyntaxOff
\xeCJKDeclareCharClass{Default}{"2026}
```

This is the prototype that was measured. It reads the macro's own body, removes
`\ignorespaces` (under both spellings), and puts it back, rather than copying
the body, so it follows whatever else the installed xeCJK does there. The
implementation may adjust the spelling to what compiles cleanly on every
supported TeX Live, but not the behaviour. The comment above it says what
it does and why, in the template's own comment style: the cause, the measured
rejects, and that the guard makes it safe on an xeCJK without the macro.

The header comment of the file ("the file keeps its name, which predates
that") stays accurate and is left alone.

## 2. Pandoc

Nothing changes in `_run_pandoc` (see the `--wrap=none` row of *Decisions*).

## 3. Straight quotes in entries

A new function in `compile.py`, applied to an entry's word, translation and
note (not its reading, which is pinyin and never prose), **before** `_escape` and before the field is split into pieces:

- `"` is an opening quote, `“`, when it is the first character of the field or
  follows whitespace or one of `( [ { < - – — /`. Anywhere else it is a closing
  quote, `”`, with one exception found while implementing: right after a
  hanzi, when no quote is open and a non-space character follows, it is an
  opening one, since Chinese is typed with no space before a quote (`他说"你好"`,
  whose first `"` follows `说`). A
  quote is open from a `“` (typed or curled) until the next `”` or `"`.
- A typed `“` or `”` is left as it is. Nothing else is rewritten.
- The grammar tables split the word into one `\HanziPinyin` unit per character
  (`_pair_hanzi_pinyin`). The curling happens on the **whole** `entry.word`
  first, so `他说"你好"` yields `“` after `说` and `”` after `好`, and not an
  opening quote on both because each is the first character of its unit.
- The field a note is wrapped around is curled on its own, as `_escape` already
  treats it: a note that starts with `"` starts with `“`.
- It is not the heading path. Headings and the title stay markdown, and pandoc
  curls them.

The curled characters go into the intermediate markdown as UTF-8, not as
`\textquotedblleft{}`. The source `.md` is unchanged.

## 4. What recompiles

`_stamp_for` hashes the template's bytes, so editing the template changes every
file's stamp: **the next Compile rebuilds every PDF in every language**, German
included. The roadmap says "every Chinese file". It is every file. An alphabetical
PDF rebuilds to the same text and positions, except in an entry containing a
straight `"`.

## Docs

- `specs/current/stack.md`'s typography/template section gets a short note: the
  xeCJK patch and why, and entry-quote curling. Written at
  implementation, with the code.
- `specs/current/design.md`: nothing. No user-facing convention changes beyond
  quotes printing correctly.
- The readme: nothing. M5 rewrites it.
- `notes-sprint-7.md`: M2's settled decisions and its new Postponed rows (a
  straight `'`, anything found while implementing), written at merge.

## Context

- **Sprint 6 M3's requirements** carry the original finding and, for headings
  and the title, the markdown-escaping rule that keeps `' " - .` for pandoc's
  `smart`. That rule is unchanged.
- **Only Chinese loads xeCJK** (Sprint 6 M6). Nothing in the template change
  can reach an alphabetical PDF.
- **A title with quotes** comes from the file's name. The filename `a "b" c.md`
  is legal on macOS and Linux, and is one of the cases in `validation.md`.
- **`pdftotext` and `pypdf`.** `pdftotext` is already used by the compile tests
  (`_right_edge_pt`) and skips when it is missing. `pypdf` is used through
  `importorskip`. Checking the spaces needs word boundaries, which `pdftotext
  -bbox` reports and `pypdf`'s text extraction does not reliably keep.
