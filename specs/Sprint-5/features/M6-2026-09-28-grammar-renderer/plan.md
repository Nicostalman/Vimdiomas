# M6 · The grammar renderer — plan

Task groups, ordered so later groups depend only on earlier ones.

## 1. Pinyin: per-syllable splitting

- `pinyin.py`: extract `to_tone_mark_syllables(numbered: str) -> list[str]`
  from `to_tone_marks`'s existing loop over `_SYLLABLE_RE.findall(numbered)`;
  `to_tone_marks` becomes `"".join(to_tone_mark_syllables(numbered))`.
- Tests (`test_pinyin.py`):
  - `to_tone_mark_syllables("tian1qi4") == ["tiān", "qì"]`.
  - A neutral tone (`"5"` or `"0"`) syllable stays unmarked in the list, same
    as today's `to_tone_marks`.
  - `"u:"`/`"v"` still normalize to `ü` per syllable.
  - An empty string returns an empty list.
  - Every existing `to_tone_marks` test still passes unmodified (behaviour
    unchanged by the refactor).

## 2. compile.py: hanzi/pinyin character pairing

- `_is_hanzi(ch: str) -> bool`: `True` iff `ch`'s codepoint falls in
  U+4E00–U+9FFF or U+3400–U+4DBF.
- `_pair_hanzi_pinyin(hanzi: str, pinyin: str) -> list[tuple[str, str]]`:
  walks `hanzi` character by character, pulling the next item off
  `to_tone_mark_syllables(pinyin)` for each hanzi character and pairing a
  non-hanzi character with `""`; a character reached after the syllable list
  is exhausted also pairs with `""` (never raises).
- Tests (`test_compile.py`):
  - `_pair_hanzi_pinyin("天气", "tian1qi4") == [("天", "tiān"), ("气", "qì")]`.
  - `_pair_hanzi_pinyin("...", "") == [(".", ""), (".", ""), (".", "")]`.
  - `_pair_hanzi_pinyin("好啦", "hao3la5") == [("好", "hǎo"), ("啦", "la")]`
    (neutral tone).
  - A hanzi field longer than the syllable list doesn't raise — trailing
    characters pair with `""`.

## 3. Template: stacked-triad macro and subtitle heading

- `templates/xecjk.tex`:
  - `\usepackage{xcolor}` (confirmed present in this machine's TeX Live
    "basic" scheme via `kpsewhich`; no new `doctor.py` check).
  - `\newcommand{\HanziPinyin}[2]{...}`: a `[t]`-aligned two-row `tabular`,
    hanzi (`#1`) at `\Large` on top, its syllable (`#2`, or empty) at
    `\scriptsize` in a paler gray (`xcolor`) beneath, no inter-row rule, no
    column separation when several are placed side by side. Its rows are
    set at `\arraystretch{1}` inside the macro's own group, with a small
    negative row skip, so the pinyin hugs its hanzi rather than inheriting
    the vocabulary table's global `1.6` (second manual pass).
  - `\renewcommand{\subsection}{...}`: **corrected mid-implementation** —
    pandoc's own raw output (checked directly, not assumed) shows a category
    (`##`) shifts to `\section` under `--shift-heading-level-by=-1`, left at
    LaTeX's default styling, and a subtitle (`###`) shifts to `\subsection`,
    not `\subsubsection`. The existing `\subsection` redefinition (M3) is
    repurposed for the subtitle: one size down from `\section`
    (`\normalfont\large\bfseries`; **reduced to `\normalsize\bfseries` with
    an en-dash prefix in the second manual pass**), with a **negative** beforeskip
    (`-1.2em`) so `\@startsection`'s indent-suppression fires the same way
    `\section`'s own default does — a positive beforeskip (the first pass)
    left the paragraph right after a subtitle's heading indented on its
    first line. No `\subsubsection` redefinition; the dev's manual pass
    caught both the missing size distinction and the stray indent. Third
    manual pass: the beforeskip drops to `-1sp` (still negative, effectively
    zero), so the entry gap alone separates the last entry from the next
    subtitle.
- `compile.py`'s `_render_grammar_table` also prefixes its output with an
  explicit `\noindent`, since a grammar entries block is one raw-LaTeX
  paragraph (unlike `_render_table`'s `longtable`, immune to `\parindent`)
  and shouldn't depend on a heading always preceding it.
- No automated test on the template's own LaTeX content (none exists for the
  `\subsection` redefinition either) — covered by group 5's integration test
  and the dev's manual review. `test_compile.py` does assert every grammar
  block's markdown starts with `\noindent`.

## 4. compile.py: the grammar rendering path

- `_render_grammar_table(entries: list[Entry]) -> list[str]`: for each entry,
  emit a `\HanziPinyin{...}{...}` call per pair from `_pair_hanzi_pinyin`
  (each hanzi character and pinyin syllable passed through `_escape`),
  concatenated with no separator, ended by `\\[GRAMMAR_PINYIN_GAP]`; then
  the translation line (`_escape`d); then, when `entry.note` is set, the note
  on its own line as `\textit{(...)}` (second manual pass — the first pass
  put it beside the translation). The entry's last line ends with
  `\\[GRAMMAR_ENTRY_GAP]`. Two module-level length constants near
  `CJK_FONT_NAME` hold the gaps; they go in `\\[...]` arguments rather than
  standalone `\vspace` lines, which left a source-newline space indenting
  every line after the first (second manual pass).
  Exception: a block's last entry ends the paragraph with
  `\par\vspace{GRAMMAR_ENTRY_GAP}` — a `\\` right before a paragraph end
  adds an empty line, which made the gap before the next subtitle larger
  than between entries (third manual pass).
- `render_markdown(deck: Deck, *, grammar: bool = False) -> str`: every place
  it currently calls `_render_table` (uncategorized, a category's own
  entries, a subtitle's entries) calls `_render_grammar_table` instead when
  `grammar=True`. The `## `/`### ` heading emission itself is unchanged for
  both.
- `compile_file`/`compile_all`: pass their existing `grammar` bool through to
  `render_markdown` as well as `parse` (today only `parse` receives it).
- Tests (`test_compile.py`):
  - `render_markdown(deck, grammar=True)` on a deck built from the dev's real
    `Grammar/Conjunctions.md` shape (a plain category, an entry with no
    reading, an entry with a note, a subtitle) emits `\HanziPinyin` calls
    (not `longtable`/`\begin{longtable}`), the note as an italic
    parenthetical on its own line after the translation line, both gap
    constants, and each block ending `\par\vspace{GRAMMAR_ENTRY_GAP}`.
  - `render_markdown(deck, grammar=True)` on an entry with `hanzi="..."`
    emits three `\HanziPinyin` calls each with an empty second argument.
  - `render_markdown(deck, grammar=False)` (every existing vocabulary test)
    is byte-for-byte unchanged — an explicit regression test pinning this,
    beyond the existing tests just continuing to pass.
  - `compile_file`/`compile_all` pass `grammar` to `render_markdown` (spy on
    `idiomas.compile.render_markdown`, assert the kwarg).
  - Integration (`@pytest.mark.integration`, real pandoc/xelatex, extending
    the existing `test_compile_all_grammar_subtitle_produces_pdf`): a deck
    shaped like `Grammar/Conjunctions.md` compiles to a non-empty PDF whose
    extracted text contains the hanzi, the tone-marked pinyin, and the
    translation.

## 5. Docs

- `specs/current/design.md`: *The compiled notebook* section gains the
  grammar layout as a stated convention (stacked triad, per-character
  pinyin, tight/loose spacing, subtitle heading), the same place M3's
  typography lives.
- `specs/current/stack.md`: no change — this milestone adds no new external
  dependency (`xcolor`/`array` are already part of the TeX Live scheme
  `xeCJK`'s own entry already requires); the file-format section (`###`
  subtitles) was already written in M5.
- Update this milestone's spec files as anything changes during
  implementation.
