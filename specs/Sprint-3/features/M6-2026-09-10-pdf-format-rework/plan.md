# M6 · PDF format rework — Plan

## 1. Template: bump font size, drop unused package

- In `templates/xecjk.tex`, change `\documentclass[11pt]{article}` to
  `\documentclass[12pt]{article}`.
- `booktabs` is dropped — group 2's raw LaTeX tables use no rules, so nothing
  in the template calls `\toprule`/`\midrule`/`\bottomrule` any more.
  `longtable`, `fontspec`, `xeCJK`, `geometry`, and the title block stay.

## 2. `compile.py`: replace the markdown pipe table with raw LaTeX

- Rewrite `_render_table` to emit a `` ```{=latex} `` fenced raw block (the
  pandoc `raw_attribute` extension) wrapping a `longtable`, instead of a
  markdown pipe table:
  - Three plain `l` columns so they size to content — left-aligned by virtue
    of `l`.
  - No `\toprule`/`\midrule`/`\bottomrule`, no header row emitted into the
    table at all — the header text (`Hanzi`, `Pinyin`, `Gloss`) is dropped
    entirely from the LaTeX output, not just hidden.
  - Keep row content identical otherwise: tone-marked pinyin (`to_tone_marks`),
    gloss with the existing note-in-italics handling (now `\textit{(...)}`
    instead of markdown `*(...)*`, since raw LaTeX isn't markdown-interpreted).
  - `_escape` reworked for LaTeX special characters instead of markdown `|`:
    `& % $ # _ { } ~ ^ \` are all escaped.
- Add `raw_attribute` to the pandoc invocation's input format in
  `compile_file` (`-f markdown+raw_attribute`) so the fenced `{=latex}` block
  passes through untouched instead of being escaped as literal text.

## 3. Recompile and verify by eye

- Recompile a real fixture and inspect visually: left-aligned, tight-to-content
  columns, no visible header or rules, larger (12pt) type, LaTeX/xeCJK
  character preserved.
- **`longtable` centers itself by default** (`\LTleft`/`\LTright` both default
  to `\fill`), even with plain `l` columns — this surfaced on the first
  compile. Fixed in the template: `\setlength{\LTleft}{0pt}` /
  `\setlength{\LTright}{\fill}`.
- Fix anything the dev flags after inspection; this loops back into groups 1–2
  and their write-up here, not a new group. One round of feedback came back
  after the first compile (2026-09-10) — see group 5.

## 4. Tests

- Update/add unit tests for `_render_table`/`render_markdown` to assert the
  new LaTeX-shaped output (no `|` pipe table, no header text, expected
  `\begin{longtable}...}` structure) rather than the old markdown table shape.
- Run the full test suite to confirm nothing else depended on the old
  intermediate markdown table shape. The existing
  `test_compile_file_produces_real_pdf_with_hanzi_and_tone_marks` integration
  test (real pandoc/xelatex, `pypdf` text extraction) doubles as a guard
  against any future CJK-font choice silently corrupting the PDF's text
  layer — see group 5.

## 5. Dev feedback round 1: spacing and CJK font (2026-09-10)

After reviewing the first compile against a real notebook file, the dev asked
for more line spacing, more space between columns, and a CJK font with less
strong serifs "similar to the Claude font" (clarified: the vibe, for the CJK
glyphs only — Latin/pinyin/gloss text stays on LaTeX's default serif).

- **Row spacing**: `\renewcommand{\arraystretch}{1.6}` in the template,
  applying to every table in the document.
- **Column spacing**: column spec changed from `lll` to
  `l@{\hspace{2em}}l@{\hspace{2em}}l`.
- **CJK font**: tried `Hiragino Sans GB` first — visually right, but its
  embedded font in the compiled PDF has a broken `ToUnicode` CMap, so
  `pypdf`/copy-paste extraction returns mojibake instead of the hanzi (caught
  by the integration test in group 4, which is exactly what it's for).
  Switched to `Heiti SC` instead: same clean sans-serif look, correct text
  layer confirmed via the same test.
- Recompiled and re-verified by eye and via the full test suite (group 4).
