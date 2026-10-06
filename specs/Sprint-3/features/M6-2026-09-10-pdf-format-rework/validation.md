# M6 · PDF format rework — Validation

## The bar

Per the roadmap: **the dev looks at a recompiled `Food.pdf` and says it is
right.** There is no automated substitute for this — the checks below are
necessary but not sufficient; the milestone closes on the dev's own eye.

## Checks

1. **Recompile a real deck.**
   ```sh
   # from the project root, against the dev's real tree (or a fixture with
   # multiple categories and at least one entry with a note)
   python -m idiomas.compile ...   # or however compile_all/compile_file is invoked
   ```
   Produces a `.pdf` with no errors from `pandoc`/`xelatex`.

2. **Open the recompiled PDF and confirm, by eye:**
   - The list sits against the left margin, not centred on the page.
   - Hanzi / Pinyin / Gloss text within each row is left-aligned, not centred.
   - Columns are sized to their content (tight), not stretched to the page's
     full text width — visible gaps of empty space to the right of the list.
   - No header row (`Hanzi`, `Pinyin`, `Gloss`) is visible anywhere.
   - No table rules are visible (no horizontal lines above/below rows or
     under the header position).
   - Category headings (e.g. "Vocabulary") still appear above their table,
     unchanged.
   - Text is visibly larger than before (12pt vs. the previous 11pt).
   - CJK characters (hanzi) still render correctly via `Songti SC`/xeCJK —
     the "LaTeX feel" (title block, XeLaTeX-rendered CJK, serif body text)
     is unchanged.
   - A gloss with a note still shows the note in italics, in parentheses.

3. **Automated tests.**
   ```sh
   pytest
   ```
   Full suite passes, including any updated/new tests for
   `_render_table`/`render_markdown`'s new LaTeX-shaped output.

4. **No regressions elsewhere.** `compile_all`'s skip-if-up-to-date logic and
   `notebook_path_for`'s suffix mapping are untouched — confirm no test
   covering those broke.

## Sign-off

Merge only after the dev has viewed a recompiled PDF (ideally against their
own real notebook content, not just a test fixture) and confirmed the format
is right — per the roadmap, that confirmation *is* the acceptance bar.
