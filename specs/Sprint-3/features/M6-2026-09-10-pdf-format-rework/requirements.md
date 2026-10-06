# M6 · PDF format rework — Requirements

## Anchor (from `roadmap-sprint-3.md`)

**Deliverable.**

- The list sits on the **left** of the page, not centred.
- The underlying table stays — it gives better alignment than tabs — but becomes
  **invisible**: no rules, no header row on show.
- A **bigger font size**.
- The LaTeX character of the output is kept. It is the part the dev likes.

**Done when.** The dev looks at a recompiled `Food.pdf` and says it is right.
There is no other bar for this one.

## Source

`guidelines/backlog.md` · *Latex/pdf format rework*:

> I dont like the format. I would like the list to be on the left side of the
> screen. I think the underlying table is ok in order to achieve more
> consistency than with tabs, but it must be invisible. I would like the font
> size to be bigger. I like the LaTeX feel. Overall the format needs a rework
> and the dev should be interviewed.

## Scope

Touches only `src/idiomas/compile.py` (`render_markdown` / `_render_table` /
`compile_file`) and `templates/xecjk.tex`. No other file changes.

## Decisions (from the M6 spec interview, 2026-09-10)

| Decision | Rationale |
| --- | --- |
| "On the left" means **both** the table's position on the page and its cell content are left-aligned — the table hugs the left margin rather than being centred, and Hanzi/Pinyin/Gloss text is left-aligned within each cell. | Dev, verbatim: "left align both the cell contents and the table, it should look like a handmade list." |
| Column widths are **tight to content** — each column sizes to its longest entry plus a small gap, not stretched to fill the page's text width. | Same interview: "Tight to content" chosen over "stretch to page width" so the result reads like a list someone wrote by hand, not a formal document table. |
| The header row (`Hanzi \| Pinyin \| Gloss`) and all table rules (top/mid/bottom) are **invisible**, but the underlying table structure is kept — it is what gives the three columns their alignment. | Dev: "i dont want the table removed. i want it to be the underlying structure. i want it to be invisible. this means, no visible header." Matches the roadmap's own wording exactly. |
| No substitute label, spacing convention, or other affordance for the missing header is added. The category heading above each table (`## Vocabulary`, etc.) is the only heading; columns are told apart by position alone. | Dev accepted this framing when it was raised as an option ("keep category name as the only heading") over adding artificial spacing or width-based cues. |
| Document font size becomes **12pt** (from the current `\documentclass[11pt]{article}`). | Dev: "12 is good," given directly as the target when asked whether to propose a size or take a specific one. |
| Table rendering moves from pandoc-interpreted markdown pipe tables to **raw LaTeX emitted directly** by `render_markdown`, passed through pandoc via the `raw_attribute` extension (fenced `` ```{=latex} `` blocks). | Getting exact control over invisible rules, no header, left alignment, and content-tight columns is not reliably achievable by tuning a markdown pipe table through pandoc's default `longtable`/`booktabs` conversion — pandoc controls too much of that translation. Emitting the LaTeX table structure directly (plain `l` columns, no `\toprule`/`\midrule`/`\bottomrule`, no header row at all) gives the milestone's formatting requirements directly, with pandoc doing header/metadata/section handling as before. |
| `longtable`'s default `\LTleft`/`\LTright` glue (both `\fill`) centers it on the page even with plain `l` columns — fixed in the template with `\setlength{\LTleft}{0pt}` / `\setlength{\LTright}{\fill}`. | Discovered while validating the first compile: content-tight `l` columns alone don't left-align a `longtable`; this is a `longtable`-specific default unrelated to column specs. |
| The LaTeX character (fontspec + xeCJK, XeLaTeX engine) is unchanged, but the **CJK font moves from `Songti SC` to `Heiti SC`**. | Backlog: "I like the LaTeX feel" — explicitly the part not being reworked. After seeing the first compiled PDF, the dev asked for less-strong serifs, in a style like Claude's own UI font — clarified to mean the *CJK* glyphs only (Latin/pinyin/gloss text stays on LaTeX's default serif). `Hiragino Sans GB` was tried first (visually right) but rejected: its embedded font in the PDF has a broken `ToUnicode` CMap, corrupting copy/paste and text search (verified via `pypdf` extraction — hanzi came back as mojibake). `Heiti SC`, a standard macOS sans-serif CJK font, gives the same clean look with a correct text layer. |
| Row spacing is increased via `\renewcommand{\arraystretch}{1.6}` in the template (applies to every `longtable`/`tabular` in the document). | Dev asked for "more linespacing" after the first compile. |
| Column gaps are widened via the column spec `l@{\hspace{2em}}l@{\hspace{2em}}l` (up from plain `lll`, which only had `\tabcolsep`'s default ~12pt gap). | Dev asked for "more space between elements in the same row" after the first compile. |

## Out of scope

- Anything about `compile_all`, `notebook_path_for`, or the compile pipeline's
  file-discovery/mtime logic — unchanged.
- Anything about how Inspect Tree or `entry.py` trigger compilation — unchanged.
- Per-column custom widths, colors, or fonts beyond the single document-wide
  12pt bump — not requested.
