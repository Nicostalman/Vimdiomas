# M5 · Aligned rows and pinyin punctuation — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M5 · Aligned
rows and pinyin punctuation*:

> **Deliverable.**
>
> - The vocabulary table's last column (the translation and its note) wraps
>   inside its own column, filling the width the other columns leave. A long
>   gloss or note no longer takes a row out of the columns. The other columns'
>   widths are measured by LaTeX itself, not estimated.
> - A row is an exception only when its *word* is too wide (Sprint 6 M6's 12em
>   cap, kept for German compounds), or when its word and reading together
>   would leave the translation column too narrow.
> - The pinyin keeps the word's punctuation and symbols: a new guess keeps them
>   (`xiao3/zhong1/da4hao4`), and an entry already on disk without them gets
>   them from its word when rendered, in the PDF and in Browse.
> - `design.md` restates the exception rule and the punctuation rule.
>
> **Done when.** The dev's screenshot rows, compiled, sit in three aligned
> columns with long notes wrapping inside the translation column; 小/中/大號
> prints `xiǎo/zhōng/dàhào` from both a fresh entry and an existing one; German
> long compounds are still exceptions; the full test suite passes.

The source is the dev's request of 2026-10-30, with two screenshots (a
*Plástico* category, and three clothing rows: 小/中/大號, 件, 條). There is no
backlog entry. The notes
([`../../guidelines/notes-sprint-8.md`](../../guidelines/notes-sprint-8.md),
*M5 and M6 added after the dev's hand-testing*) record why the milestone exists
and which earlier decisions it revisits.

**The bugs in one line each.** (1) `compile._exception_rows` takes a row out of
the `longtable`'s columns whenever the estimated table is wider than the text,
and a long gloss is the usual reason, so its pinyin and gloss start where the
neighbours' don't. (2) `pinyin.guess` keeps only hanzi runs, and
`to_tone_marks` keeps only `letters+digit` matches, so `/` never reaches the
reading, and would be dropped from it if it did.

## Decisions

The dev asked for as few questions as possible. Every decision below is the
agent's, for the dev to overrule in review.

| Decision | Rationale |
| --- | --- |
| **The last column is a `p` column whose width is computed in LaTeX** from the measured widths of the other columns (`\FitColumn`, below) | The column has to wrap, so it needs a width. Measuring with `\settowidth` uses the real fonts, so the table is exactly as wide as the text, and the estimate (`_width_em`) is no longer what decides where a gloss breaks. The `tabularx`-for-`longtable` packages (`ltablex`, `xltabular`) are not in BasicTeX, and M2's package check would have to grow. |
| **Wrapped gloss lines start at the column's left edge**, ragged right, with no hanging indent | The column itself shows which entry the line belongs to. A hanging indent was needed only for exception rows, which have no column. |
| **Exceptions: a word wider than `WORD_CAP_EM` (12em) as before, or word + reading leaving less than `MIN_GLOSS_EM` (12em) for the translation** | The cap is still needed: one long German compound widens the word column for every row. A very long reading (an idiom's pinyin) can do the same to the gloss column, and the same greedy removal as Sprint 6 M6 handles it, now over the word and reading columns only. 12em is as wide as the word cap: about 24 Latin letters a line. |
| **Exception rows render as before** (`\multicolumn`, full width, 1.5em hanging indent) | Only which rows qualify changes. |
| **"Punctuation and symbols" means Unicode general categories `P*` and `S*`** | Covers `/ - … ~ + （ ）， 、` and the like, with no list to maintain. Letters and digits stay out (Sprint 6 M3's #19: `T恤` is `xu4`). |
| **`guess` keeps the word's punctuation and symbols in place, and still drops letters, digits and spaces** | `guess("小/中/大號")` is `xiao3/zhong1/da4hao4`, and the Entry field shows the slashes before Create. Spaces were never part of a guess, and a hanzi word has none worth keeping. |
| **A stored reading keeps every character that is not a letter or a digit when it is tone-marked** (`to_tone_marks`): punctuation, symbols and spaces | What is in the file is printed. Stray letters and digits (a reading written before #19, `Txu4`) are still dropped, as before. `to_tone_mark_syllables`, used by the grammar triads, is unchanged. |
| **A reading with no punctuation of its own takes the word's** when displayed (`pinyin.display_reading(word, reading)`) | Fixes entries already on disk (the dev's 小/中/大號 is stored as `xiao3zhong1da4hao4`) with no rewrite of anyone's files. A reading that has its own punctuation is printed as it is, so a hand edit (M6) is never second-guessed. |
| **Browse's content-mode rows use the same `display_reading`** | One rule for every place a reading is shown. |
| **The displayed reading is curled like the prose fields** (`_curl_quotes`) | A `"` in a word now reaches the reading, and TeX would print it as `”`. |
| **Grammar files are not changed** | Their triads pair each character with its own syllable, and a `/` in the word already prints in the hanzi line with nothing under it. |

## 1. The table layout

### 1.1 Columns

A kind with a reading (Chinese):

```
\begin{longtable}{l@{\hspace{2em}}l@{\hspace{2em}}>{\raggedright\arraybackslash}p{\GlossColumn}}
```

A kind without (German): the same minus the middle `l`. Every ordinary row is
`word & reading & translation \\` as before.

### 1.2 Measuring

The template (`templates/xecjk.tex`) declares four lengths, `\WordColumn`,
`\ReadingColumn`, `\GlossColumn` and `\CellWidth`, and one macro:

```
\newcommand{\FitColumn}[2]{%
  \settowidth{\CellWidth}{#2}%
  \ifdim\CellWidth>#1\setlength{#1}{\CellWidth}\fi}
```

Each table's raw block starts, before `\begin{longtable}`, by zeroing
`\WordColumn` and `\ReadingColumn`, then calls `\FitColumn` once per ordinary
(non-exception) row and column with exactly the LaTeX of that cell
(`{\Large 塑膠}`, `sùjiāo`), then sets

```
\setlength{\GlossColumn}{\dimexpr\linewidth-2\tabcolsep-\WordColumn-\ReadingColumn-4em\relax}
```

(`-2em` and no `\ReadingColumn` for a kind without a reading). Exception rows
are not measured: they don't sit in the columns.

### 1.3 Exceptions

`_exception_rows(widths)` keeps its signature (each row's estimated cell widths,
word first). It returns:

- every row whose word is wider than `WORD_CAP_EM`, as before; then
- while the estimated widest word plus the widest reading (over the rows not yet
  taken) leave the translation column less than `MIN_GLOSS_EM`, the row holding
  the widest word or reading cell whose removal narrows those columns most. The
  translation's width plays no part.

The budget is `TEXT_WIDTH_EM − TABLE_PADDING_EM − COLUMN_GAP_EM × (columns − 1)
− MIN_GLOSS_EM`. For a two-column kind only the word cap can make an exception
(24em of budget, above the 12em cap).

## 2. Punctuation in the pinyin

### 2.1 `guess`

`pinyin.guess(word)` walks the word: each run of hanzi goes to pypinyin whole
(so 银行 is still `yin2hang2`), each character of category `P*` or `S*` is kept
as it is, and anything else (Latin letters, digits, spaces) contributes
nothing.

| Word | Guess |
| --- | --- |
| 小/中/大號 | `xiao3/zhong1/da4hao4` |
| T恤 | `xu4` (unchanged) |
| 3D打印 | `da3yin4` (unchanged) |
| ...了 | `...le5` |
| 你好！ | `ni3hao3！` |

### 2.2 `to_tone_marks`

`to_tone_marks(numbered)` tone-marks each syllable as now and keeps, in place,
every character between syllables that is neither a letter nor a digit.
`xiao3/zhong1/da4hao4` → `xiǎo/zhōng/dàhào`; `ni3 hao3` → `nǐ hǎo`;
`Txu4` → `xù` (unchanged).

### 2.3 `display_reading`

`pinyin.display_reading(word, reading, *, unsupported=None)` is what every
vocabulary surface prints:

- If `reading` has at least one character, outside its syllables, that is
  neither a letter nor a digit, it is `to_tone_marks(reading)`.
- Otherwise the word's punctuation is woven in: walking the word, a hanzi
  takes the next tone-marked syllable, a `P*`/`S*` character is itself, and
  anything else is nothing; syllables left over after the word ends are
  appended. 小/中/大號 with `xiao3zhong1da4hao4` → `xiǎo/zhōng/dàhào`.
- `unsupported` collects unmarkable syllables as `to_tone_marks` does (#4).

Callers: `compile._render_table` (then `_curl_quotes`, then `_escape`) and
`browse.hit_fields`.

## 3. `design.md`

- The bullet *A vocabulary row too long for the aligned columns is an
  exception* is rewritten for §1: the translation column wraps, only a long word
  (or a reading that crowds the translation) is an exception.
- A new bullet under *The compiled notebook*: the pinyin keeps the word's
  punctuation and symbols (§2).

## 4. Consequences

- The template and the renderer's output change, so every notebook's stamp
  changes and the next Compile rebuilds all of them once.
- Nothing on disk is rewritten. An existing reading without punctuation is
  shown with the word's (§2.3).

## 5. Tests

- `tests/test_pinyin.py`: `guess` on the §2.1 table; `to_tone_marks` keeping
  `/`, spaces and `…`, and still dropping `T`; `display_reading` for an own
  punctuation, a woven one, leftover syllables, an empty reading, a word with
  Latin letters.
- `tests/test_compile.py`: `_exception_rows` with a long gloss (no exception), a
  long word (exception), a long reading (exception); the column spec with
  `\GlossColumn` for both kinds; `\FitColumn` lines for ordinary rows only; the
  dev's *Plástico* rows with no `multicolumn`; 小/中/大號 rendering
  `xiǎo/zhōng/dàhào` from both readings; existing tests updated to the new
  column spec and rule.
- Integration (real `xelatex`, `pdftotext -bbox`): the *Plástico* rows compile
  inside the margins, and every row's pinyin starts at the same x, and every
  gloss at the same x.
- `tests/test_tui_browse_screen.py`: a content hit on 小/中/大號 with
  `xiao3zhong1da4hao4` shows `xiǎo/zhōng/dàhào`.
- `tests/test_tui_entry_screen.py`: typing 小/中/大號 fills the reading with
  `xiao3/zhong1/da4hao4`.
