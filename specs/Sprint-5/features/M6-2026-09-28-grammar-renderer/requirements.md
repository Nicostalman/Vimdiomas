# M6 · The grammar renderer — requirements

## Anchor (from the roadmap)

**Deliverable.** A second rendering path in `compile.py` for grammar files,
leaving the vocabulary path untouched: the triad (hanzi, pinyin, translation)
is three stacked lines, not three columns; the gap inside a triad is tighter
than the gap between triads; pinyin is smaller and paler than the body text;
each pinyin syllable is aligned under its own hanzi character; a character
with no reading (the backlog's example: `...`) gets no pinyin under it;
subtitles render as a heading below the category heading. Pinyin stays
numbered and tone-marked at compile time (`to_tone_marks`); LaTeX escaping
(`_escape`) applies to grammar output exactly as it does to vocabulary. M2's
staleness fix is what makes this checkable: landing the milestone rebuilds
the dev's existing grammar PDFs automatically.

**Done when.** Compiling a grammar file produces the layout in
[`../../guidelines/image-1.png`](../../guidelines/image-1.png) — three
stacked lines per triad, tight within and loose between, pinyin smaller and
paler and aligned character by character, `...` and friends bare, subtitles
as headings; vocabulary PDFs are unchanged by this milestone; landing it
rebuilds the dev's grammar PDFs with no manual step; the dev approves the
result by eye against the image; and the full test suite passes.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Grammar folder* — "the hanzi-pinyin-translation structure is unchanged, but
the rendering changes. The three are not in the same line but in three
separate lines... The pinyin will be in a smaller font and in a clearer
shade... Each pinyin must be aligned with the hanzi above. Special characters
like "..." wont have any pinyin below." M5 shipped everything else in that
section; this milestone is the PDF.

## Decisions from the spec conversation (2026-09-28)

| Decision | Rationale |
| --- | --- |
| **The per-character alignment mechanism is the agent's call**, with permission to fall back to an external LaTeX package if a self-contained implementation proves too complex | Dev: "whatever works best i trust you. if you can make your own implementation work then go for it but if its too complicated just import." |
| **A triad that overflows the line width just wraps**, no forced no-wrap | Dev's choice. Real grammar entries (checked against the dev's own `Grammar/Conjunctions.md`) are short phrases, not long sentences — unlikely to bite, and simpler than guarding against it. |
| **A note renders as a parenthetical italic under the translation line**, matching vocabulary's own convention for the same field | Dev's choice. Vocabulary already appends a note to the gloss as `\textit{(...)}`; grammar keeps the same treatment, just under the translation line instead of beside it in a column. |
| **The translation line stays plain body text**, no styling of its own | Dev's choice. Matches the reference image (`clima` is unstyled) and vocabulary's own gloss column. |

## Decisions taken while speccing (agent)

| Decision | Rationale |
| --- | --- |
| **The alignment mechanism is a self-contained one: a `\HanziPinyin{hanzi}{pinyin}` LaTeX macro**, a `[t]`-aligned two-row `tabular` per character (hanzi on top, its syllable — or nothing — beneath), concatenated with no gap between characters | No new *required* dependency: the macro only needs `array` (already loaded transitively via `longtable`) and `xcolor` for the paler shade, and both are confirmed present in this machine's TeX Live "basic" scheme (`kpsewhich xcolor.sty`/`array.sty`), the same scheme `xeCJK` already has to be added to. Since a per-character box sizes to its own content, this handles double-width hanzi against variable-width Latin syllables without measuring anything in Python. `doctor.py` gains no new check — unlike `xeCJK` (Sprint 3) or `pdftoppm` (M4), nothing here is missing from a stock "basic" install. |
| **`pinyin.py` gains `to_tone_mark_syllables(numbered) -> list[str]`**, the per-syllable half of what `to_tone_marks` already does; `to_tone_marks` becomes `"".join(to_tone_mark_syllables(numbered))` | The existing regex (`_SYLLABLE_RE`) already segments a numbered string into one match per syllable — `to_tone_marks` was just joining them early. Splitting it out is a pure refactor: `to_tone_marks`'s own behaviour and tests are unchanged. |
| **`compile.py` gains a hanzi classifier** (`_is_hanzi`, Unicode ranges U+4E00–U+9FFF and U+3400–U+4DBF) **and `_pair_hanzi_pinyin(hanzi, pinyin)`**, consuming one syllable per hanzi character in the field, in order, and pairing every non-hanzi character (`.`, digits, Latin letters, anything outside the ranges) with an empty string | This is the actual rule behind "a non-hanzi character contributes no syllable": `...` has three non-hanzi characters and an empty pinyin field, so all three pair with nothing; `好啦` pairs `好`→`hǎo`, `啦`→`la`. Consuming syllables in order (rather than trying to align by counting) is correct because the pinyin field's segmentation already matches the hanzi field's character order one-for-one wherever a reading exists. |
| **The existing `\subsection` redefinition is repurposed for the subtitle heading, one size down from a category heading** — checking pandoc's own raw output showed a category (`##`) actually shifts to `\section` (LaTeX's unmodified default: `\Large\bfseries`, negative beforeskip), not `\subsection`; a subtitle (`###`) shifts to `\subsection`. The template's original `\subsection` redefinition (from M3) was based on the same wrong assumption and had been inert the whole time — it restyled a command pandoc never actually emitted, invisibly, since default `\section` already rendered the same way it was trying to produce | Corrected mid-implementation, after the dev's manual pass showed subtitle and category headings at the same size. `\subsection` is now sized `\large\bfseries` (one step below `\section`'s `\Large`) with a **negative** beforeskip (`-1.2em`, matching `\section`'s own default sign) — a positive beforeskip does the vertical spacing but never triggers `\@startsection`'s indent-suppression, which is what let a stray `\parindent` land on the first hanzi line of the first entry under a subtitle (the dev's other manual-pass finding). `design.md`'s M3 entry is corrected to match. |
| **`_render_grammar_table` prefixes its output with an explicit `\noindent`**, not left to the preceding heading | A grammar entries block is raw LaTeX text (line breaks via `\\`, not blank lines) — one paragraph, subject to `\parindent` on its own first line regardless of what precedes it (a heading, or nothing at all for `deck.uncategorized`). Explicit is more robust than depending on the heading fix above always being present before it. |
| **`render_markdown` and `compile_file`/`compile_all` thread a `grammar: bool` through to a new `_render_grammar_table`**, parallel to the existing `_render_table`, used for a grammar file's uncategorized/category/subtitle entries instead of the vocabulary `longtable` | Same shape as M5's `parse(..., grammar=...)` threading. Keeps the vocabulary path — `_render_table`, and every existing `render_markdown` call for a non-grammar deck — byte-for-byte what it is today, which matters doubly here: M2's staleness stamp hashes `render_markdown`'s output, so an unchanged vocabulary render means no vocabulary PDF recompiles when this milestone lands. |
| **Tight/loose spacing are two module-level `\vspace` constants in `compile.py`**, next to `CJK_FONT_NAME` | First-pass values, to be adjusted once the dev eyeballs a real recompile against `image-1.png` — the same iterate-after-hand-off pattern as M3 (hanzi size), M4 (aspect ratio) and M5 (focus-advance). Exact spacing and shade are explicitly the roadmap's own "eyeball decisions against the image," not decided here. |
| **Second manual pass (2026-09-29): an entry is up to four stacked lines — hanzi, pinyin, translation, note — with three distinct gaps.** Pinyin hugs its hanzi (the macro's rows are no longer stretched by the vocabulary table's global `\arraystretch{1.6}`, which is what pushed them apart), a small gap separates pinyin from translation, and a considerable one separates an entry's last line from the next entry's hanzi, so each entry reads as one unit | Dev's review of the first recompile. Supersedes the earlier row "a note renders as a parenthetical italic under the translation line": the first pass actually put it *beside* the translation, on the same line — it now gets its own line below, still italic and parenthesized. |
| **Gaps go in `\\[<length>]` line-break arguments, not standalone `\vspace` lines** — `GRAMMAR_PINYIN_GAP`/`GRAMMAR_ENTRY_GAP` in `compile.py` are bare lengths | Found in the same review: a `\vspace` line inside the paragraph leaves a non-discardable item at the start of the next line, so the source newline after it became a visible space — every line but the first sat ~1em right of the margin. A `\\[...]` break carries the space itself, and the newline after it is discarded at the line start. |
| **Subtitles shrink to body size (`\normalsize\bfseries`) and each is prefixed with an en dash** | Dev's review: the `\large` subtitle still competed with the category heading. The dash is in the template's `\subsection` style argument, not in the markdown `render_markdown` emits, so the source/heading text stays the dev's own. |
| **A subtitle's beforeskip is `-1sp` — effectively zero, still negative** (third manual pass, 2026-09-29), so the space between an entry and the next subtitle is `GRAMMAR_ENTRY_GAP` alone, the same as between two entries | Dev: the gap before a subtitle should be "the same as if it was another entry". The entries block already ends every entry with `GRAMMAR_ENTRY_GAP`; the old `-1.2em` beforeskip stacked on top of it. Kept negative (not `0pt`) because the sign is what triggers `\@startsection`'s indent suppression. Also, each entries block's last entry ends the paragraph with `\par\vspace{GRAMMAR_ENTRY_GAP}` instead of `\\[...]` — a line break right before a paragraph end adds an empty line, the rest of the extra gap. |

## Context

- The reference is `image-1.png`: a bold subtitle-style heading ("Clima"),
  then a hanzi line (天气) with its pinyin (tiān qì) in a smaller, gray shade
  aligned under each character, then the plain-text translation ("clima")
  below with more room above it than the hanzi/pinyin gap has between them.
- The dev's real `Grammar/Conjunctions.md`
  (`~/Documents/Idiomas/tree-Chinese/Grammar/`) is the acceptance sample: it
  already has a plain category before any subtitle, an entry with no pinyin
  reading (`...`), a two-character entry with a plain translation, entries
  with a note (`*test none*`, `*test en copulative*`, `*prueba new cat*`,
  `*prueba v2*`), and a `### new cat` subtitle — enough to exercise every
  case this milestone lists without inventing a synthetic file.
- `render_markdown` already emits `### <subtitle>` headings (M5); this
  milestone only changes what follows a heading — the entries' table — for a
  grammar file, and adds the heading's own LaTeX styling.
- M3 settled the notebook's typography (Songti SC, `\Large` hanzi in the
  vocabulary table, the category-heading redefinition method this milestone's
  subtitle heading copies) — this milestone builds on that baseline rather
  than making its own font or margin decisions.
- M2's staleness cache means nothing needs deleting by hand: landing this
  milestone changes `render_markdown`'s grammar-path output and
  `templates/xecjk.tex`'s bytes, both of which the cache's stamp already
  covers.

## Out of scope (this milestone)

- Anything about vocabulary rendering — `_render_table`, the `longtable`
  layout, the hanzi/pinyin/gloss columns — all unchanged.
- Multi-page or paginated grammar PDFs (not in this sprint at all — see the
  roadmap's *Not in this sprint*).
- A Linux-installable counterpart for anything this milestone adds (M7); the
  packages this milestone relies on (`xcolor`, `array`) are TeX packages, not
  system fonts, but M7's sweep still covers the template generally.
- Showing grammar-ness, subtitles, or this layout anywhere outside the
  compiled PDF (Inspect Tree's PDF preview pane already renders whatever
  `pdftoppm` rasterises — no code path there needs to know grammar from
  vocabulary).
