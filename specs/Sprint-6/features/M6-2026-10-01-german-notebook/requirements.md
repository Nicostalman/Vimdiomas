# M6 · The German notebook — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-6.md`](../../roadmap-sprint-6.md), *M6 · The German
notebook*:

> **Deliverable.**
>
> - **German is functional.** Choosing it on the landing menu opens the
>   notebook menu, not `PlaceholderScreen`. `FUNCTIONAL_LANGUAGES` — or
>   whatever M5 leaves in its place — includes it.
> - **Entry shows the right fields.** The character field does not appear,
>   nothing is auto-guessed, and there is no read-only phonetic field to tab
>   past. Field order, tab behaviour, the create-and-clear loop, the tree of
>   categories/uncategorized/new-category, and the grammar panel's subtitle
>   field all behave exactly as Chinese's do.
> - **The renderer renders German.** A vocabulary deck and a grammar deck both
>   compile, with a layout derived from Chinese's but without the pinyin row:
>   the grammar renderer's stacked hanzi-over-pinyin unit has nothing to
>   stack, so the block is redesigned rather than left with an empty row.
>   Typography is German's own.
> - **Input-method switching keeps working.** German's config already stores
>   both sources and has since Sprint 4 M6; they stop being stored-and-unused.
> - **No Chinese regression.** Every Chinese behaviour and PDF is unchanged,
>   on the dev's real tree.
>
> **Done when.** The dev creates German vocabulary and grammar entries by hand
> in the real app, compiles both, and approves the PDFs by eye; no Chinese PDF
> changes; and the full test suite passes.

Source: [`backlog.md`](../../guidelines/backlog.md)'s *Implement german*:
"keeping the same ideas from chinese … there's no equivalent to hanzi, so the
text field should not appear and the rendering will be different", and "You
should recycle elements from chinese and not repeat code. If necessary you can
create new classes only if they add more functionality than complexity."

What M5 left for this milestone (sprint notes, *Settled after M5's
implementation*): `Entry` is `word`/`reading`/`translation` and an
alphabetical language's `reading` is `""`; German is `functional=False`;
`render_markdown` (and so autocompile) raises `NotImplementedError` naming M6
for a kind with no reading; `ALPHABETICAL.cjk_font` is `None`, provisionally.

## Settled with the dev (2026-10-01)

The roadmap's open questions. The dev took the recommended option on each.

| Question | Decision |
| --- | --- |
| **What a German entry's row looks like on disk** | **Two columns: `word<TAB>translation`**, then any extra fields, as Chinese's extras follow its third column. This is what a person types by hand in nvim, which M9 cares about. The parser and writer become **kind-aware**: they take the kind, which every caller already has since M5. Chinese files are read and written exactly as today. |
| **The German vocabulary table** | **Chinese's table minus the pinyin column**: the word in `\Large`, then the translation with the note as an italic parenthetical. The column gap, alignment, row spacing and absence of rules are the same. |
| **The German grammar block** | **Chinese's stacked unit minus the pinyin row**: the phrase in `\Large` on its own line, the small gap, the translation, the note as an italic line if there is one, then the large gap before the next entry. |
| **Typeface** | **Latin Modern Roman**, already the face of all Latin text in Chinese PDFs and shipped with TeX Live, so there's no new dependency. **A German PDF does not load xeCJK at all**: one template, with xeCJK and the CJK main font behind a pandoc conditional on the `cjkfont` variable. |

## Scope

### 1. German is functional

- `languages.LANGUAGES`: German's entry drops `functional=False`.
- `languages.ALPHABETICAL.cjk_font` stays `None`, and is now final rather than
  provisional. Its comment says so: an alphabetical kind sets no CJK face, and
  its Latin face is the template's own (Latin Modern).
- The landing menu's German option now reads "Add words, explore and compile
  your German notes." and opens the notebook menu. Both already follow from
  `is_functional`, so nothing in `landing.py` changes.
- `idiomas compile` compiles German's tree, because it is functional.
- Settings › Input methods is unchanged. It already lists German and stores
  its two sources.

### 2. Storage: the parser and writer take the kind

**On disk, an alphabetical row is `word<TAB>translation[<TAB>extra…]`.** A
note is the indented `*…*` line below its row, exactly as for Chinese. Tags,
headings, the `# Title` header, subtitles in grammar files and blank-line
rules are all unchanged and kind-independent.

- **`parser.parse(text, filename_stem, *, kind, grammar=False)`**. `kind` is
  **required**, with no default, following M5's rule for the compiler: a
  silent Chinese default is exactly the hardcoding M5 removed.
  - A line is an entry row when it has **at least as many tabs as the kind
    has columns minus one**: 2 for a kind with a reading (today's rule,
    unchanged) and 1 for a kind without.
  - For a kind with a reading, the fields unpack as today: `word, reading,
    translation, *extra`.
  - For a kind without one, they unpack as `word, translation, *extra`, and
    `reading` is `""`.
  - The M1 fix (#2) carries over: the split uses the line with only its
    terminator removed, and each field is stripped of spaces only. So
    `Haus<TAB>` is a row with an empty translation, and round-trips.
  - The indented-note check still runs **before** the row check, so a
    tab-indented note (`<TAB>*…*`, one tab) is still a note in a German file
    and is never misread as a one-tab row.
  - A German line with two or more tabs (for example a Chinese-style
    `Haus<TAB><TAB>house`) reads as `word="Haus"`, `translation=""`,
    `extra_fields=["house"]`, by the general rule. It is not special-cased.
    Whether such a line deserves a warning is M9's question.
- **`writer.write(deck, *, kind)`** and **`writer.save(deck, path, *,
  kind)`**, `kind` required.
  - For a kind with a reading, the row is unchanged:
    `word, reading, translation, *extra`.
  - For a kind without one, the row is `word, translation, *extra`.
  - The writer's backstop gains one check. For a kind without a reading, an
    entry whose `reading` is not `""` raises `ValueError` naming the entry,
    rather than silently dropping the reading. Nothing in the app can produce
    one, since Entry has no reading field for such a kind.
- **Every caller passes the kind it already has:**
  - `compile.render_source` passes its `kind=`.
  - Entry's `_read_deck` and its `save` calls pass `self.config.kind`.
  - **`store.walk(root, *, kind)`** and **`store.tag_index(root, cache=None,
    *, kind)`** pass it to `parse`. `walk` needs the kind for a correct
    answer: `FileNode.has_uncategorized` depends on rows being recognised, so
    without it a German file's uncategorized entries would vanish from
    Entry's tree. `tag_index` only reads tags, which don't depend on the kind,
    but it takes the kind for one uniform `parse` signature, and so that M9's
    warnings from Browse aren't bogus "unrecognized line"s for every German
    row.
  - Entry and Inspect Tree pass their kind to `walk`.
  - **`BrowseScreen(tree_root, *, kind)`** gains a required `kind=`, the same
    way M5 gave Inspect Tree one, and passes it through
    `paths_with_tag(tree_root, tag, *, kind)` to `tag_index`.
    `MainMenuScreen` fills it from `NotebookConfig.kind`.

### 3. Entry

Nothing in `entry.py` branches on the language. M5 already built the form
from `config.kind`, so for German:

- There's no reading field. The word field's placeholder is "Word", nothing
  is guessed as the user types, and `tab` goes Word → Translation → Note.
- The category tree (categories, `(uncategorized)`, `(new category)`), the
  create-and-clear loop, the "`<word>` added successfully!" notification, and
  the grammar panel's Subtitle field (`(none)`, existing subtitles,
  `(new subtitle)`, and the name field it reveals) behave exactly as
  Chinese's do.
- The Word field switches to German's `input_method` on focus and to its
  `translation_input_method` on blur, from the config, as `WordInput` already
  does for any language.
- Saving writes the two-column row (§2), and on leaving the screen,
  autocompile compiles the edited files with the alphabetical renderer (§4).
  M5's Entry test, which cleared the dirty-file set to avoid
  `NotImplementedError`, stops needing to.

**The grammar folder convention applies to German unchanged.** A file under
`tree-German`'s top-level `Grammar/` is a grammar file (`store.is_grammar`),
with subtitles in the form and the stacked block in the PDF. The roadmap's
deliverable already requires the grammar panel's Subtitle field for German,
and `is_grammar` is kind-independent.

### 4. The renderer

The backlog asks to recycle Chinese's renderer rather than duplicate it, so
each of the two existing render functions gains a kind and branches **only
where the kinds actually differ**. There is no second set of functions for
alphabetical languages, and no new class.

- **`render_markdown`** loses its `NotImplementedError`. It passes `kind` on
  to the render functions. Title, headings, uncategorized handling and
  subtitles are already kind-independent and stay as they are.
- **Vocabulary, `_render_table(entries, kind, unsupported)`:**
  - The column spec has one `l` per column, joined with the same
    `@{\hspace{2em}}`: three for a kind with a reading, two for one without.
  - The row is `{\Large word}`, then the tone-marked reading **only if the
    kind has one**, then the translation (with the italic note in parentheses
    when there is one).
  - For Chinese, the output is byte-identical to today's.
- **Grammar, `_render_grammar_table(entries, kind, unsupported)`:**
  - The entry's head line is the run of `\HanziPinyin` units for a kind with a
    reading, as today. For a kind without one, it is the word set in `\Large`.
  - Everything after the head line is shared, unchanged code: the
    `GRAMMAR_PINYIN_GAP` gap, the translation, the italic note line, the
    `GRAMMAR_ENTRY_GAP` gap, and the block's last-entry `\par\vspace` rule.
    The constant keeps its name: for German it is the gap after the word
    line, which plays the role the pinyin line plays for Chinese.
  - **A phrase longer than one line wraps without overlapping.** A `\Large`
    run inside a body-size paragraph takes the paragraph's body-size
    `\baselineskip`, so a wrapped German phrase's lines would collide. The
    head line therefore goes through a template macro, `\GrammarWord{…}`,
    which sets the word `\Large` with its own line spacing. **Settled in
    implementation:** `\GrammarWord` is `\parbox[t]{\linewidth}{\raggedright
    \Large #1\par}`. The box is its own paragraph, so a phrase that wraps is
    spaced by `\Large`'s `\baselineskip`, and `[t]` keeps the box's baseline on
    its first line so the gap that follows it is the same as for a one-line
    word. Checked by eye on a three-line-wrapping phrase: no overlap. The case
    is checked in `validation.md`.
  - For Chinese, the output is byte-identical to today's.
- **`_run_pandoc`** passes `-V cjkfont=<font>` only when `kind.cjk_font` is
  set. For Chinese the argv is byte-identical to today's.
- **`_stamp_for`** hashes `kind.cjk_font or ""`. For Chinese the bytes are
  identical to today's, and for German it no longer crashes on `None`.
- **The template, `templates/xecjk.tex`:**
  - `\usepackage{xeCJK}` and `\setCJKmainfont{$cjkfont$}` move inside
    `$if(cjkfont)$ … $endif$`. A German PDF is plain fontspec + Latin Modern.
    This also means German never meets the xeCJK closing-quote spacing bug
    postponed from M3, which stays postponed for Chinese.
  - It gains `\GrammarWord`, next to `\HanziPinyin`.
  - Its filename stays `xecjk.tex` (renaming it is churn), and its header
    comment states that xeCJK is conditional.
- **A one-time rebuild of every Chinese file.** The stamp hashes the
  template's bytes, so editing the template changes every Chinese stamp, and
  the dev's first Compile after this milestone rebuilds each Chinese PDF once.
  This is the same mechanism that has always made a template edit count as a
  renderer change. The PDFs it produces are pixel-identical to today's (see
  *No Chinese regression* below), so nothing the user sees changes. It is
  stated here so it isn't mistaken for a regression.

### 5. No Chinese regression

This is checked the way M5 checked it, with M5's
[`check_equivalence.py`](../M5-2026-10-01-language-kinds/check_equivalence.py),
run against a copy of `~/Documents/Idiomas/tree-Chinese` before and after.

- **The markdown handed to pandoc and pandoc's argv are identical** for
  every Chinese file.
- **Every page rasterises pixel-identically** (`pdftoppm -r 100`).
- **The stamps are expected to differ**, because of the template edit
  (§4). That is the one difference from M5's bar, and it is the only one
  allowed.
- Every existing Chinese parser and writer round-trip test passes unchanged,
  with `kind=CHARACTER_PHONETIC` added.

### 6. Docs

- **`stack.md`**:
  - The *Storage* section says that an alphabetical row is
    `word<TAB>translation`, and that the parser and writer take the kind.
  - *Languages and kinds* drops "the template's unconditional `xeCJK`" from
    its "Still Chinese by design" list, says `xeCJK` is loaded only for a kind
    with a CJK font, and notes that `walk`, `tag_index` and Browse now take
    the kind.
- **`design.md`**:
  - *The compiled notebook* gains the alphabetical look: Latin Modern only,
    no CJK face, the two-column vocabulary table with the word in `\Large`,
    and the stacked grammar unit without a pinyin row.
  - *Entry's grammar panel*'s two mentions of "Hanzi" become "the word field
    (Hanzi, for Chinese)", since the panel now serves both kinds.

## Changes after hand-testing (2026-10-01)

Two requests from the dev's first manual pass, both applied to the same
milestone.

### 7. A notebook's two folders are created for the user

A notebook's tree gets its **`Vocabulary/` and `Grammar/`** folders without the
user making them by hand. `tree-German` had only `Vocabulary/`, because nothing
ever created the other.

- One helper, `store.ensure_tree(tree_root)`, creates the tree folder if it is
  missing and each of the two folders inside it that is not already there. It
  never touches an existing file or folder.
- A folder counts as already there **whatever its case**: `is_grammar` matches
  `Grammar` in any case, and on a case-sensitive filesystem creating `Grammar/`
  beside an existing `grammar/` would split one notebook's grammar in two.
- It is called in the two places a tree comes into use: the **wizard** when it
  creates a language's tree, and the **notebook menu** when it opens, so a tree
  that already exists, such as the dev's `tree-German`, is completed the next
  time it is opened. Every language gets this, not only German, since a
  Chinese tree is the same shape. M7's *Add a language* will call the same
  helper.
- An empty folder is an ordinary directory in Inspect Tree.

### 8. A long row is an exception, and wraps — for every language

The vocabulary table's first column is as wide as its longest word, so one very
long word (German compounds) pushed every translation to the right, and a row
too long for the page ran out past the margin. **The fix is in the shared
table renderer, not per kind** (the dev's follow-up: "for every language, at
class level"): Chinese's three columns and German's two go through the same
rule, so a language added later gets it too.

- **Widths are estimated in `em`**, by a small function every kind shares:
  a character is 1em if it is East Asian wide or fullwidth, 0.5em otherwise,
  and the word, set in `\Large`, counts 1.2 times that. A cell is measured
  as it prints: the reading after its tone marks, the translation with its
  note's parenthetical.
- **A row is an *exception* in two cases:**
  1. **Compactness.** Its word is wider than `WORD_CAP_EM` (12em: ten hanzi,
     or twenty Latin letters, in `\Large`). A word that wide would drag every
     other row's second column to the right, so it is set apart even though
     it would fit.
  2. **No overrun.** While the table's natural width, the sum of each
     column's widest aligned cell plus the gaps and padding, exceeds the
     6.5in text width, the aligned row that contributes most to it is made an
     exception, and the width is re-measured. A table that fits loses no row,
     so **an existing Chinese table that fits is byte-identical to before**.
- **An exception row is set outside the columns**: one cell spanning all of
  them, the full text width, holding the word in `\Large` and then each
  non-empty remaining cell after the usual 2em gap, as one paragraph. If it
  does not fit on one line it **wraps, and every continuation line is
  indented** (a hanging indent of `LONG_ROW_INDENT`, 1.5em) so it reads as the
  same entry's continuation, not a new one. The paragraph is `\raggedright`,
  like the rest of the table.
- **Every other row is exactly what it was**, and the aligned columns are
  sized by the aligned rows alone, so one exception no longer moves the other
  translations.
- **The grammar block** already wraps a long German phrase (`\GrammarWord`)
  and any translation inside its one paragraph. A long **Chinese** phrase was
  a run of `\HanziPinyin` boxes with nowhere to break, so it ran past the
  margin: the macro now allows a line break after each unit. It adds nothing
  to the Chinese markdown. There is **no hanging indent** in a grammar block,
  which is a single paragraph across all its entries.
- The on-disk row is unchanged: one tab, however long the word.
- The constants, `WORD_CAP_EM`, `LONG_ROW_INDENT` and the em widths, are
  first-pass values, tuned by eye like the grammar gaps.

## Out of scope

- **`doctor`'s xeCJK and CJK-font checks stay required.** A German-only
  install still needs them to pass `doctor`, though it never uses them. The
  wizard already allows a German-only install, but `doctor` has no notion of
  the configured languages, and M7 is the milestone that makes
  alphabetical-only installs ordinary. This goes to the sprint's Postponed
  table at merge.
- **The four other alphabetical languages, and the wizard offering them.**
  That is M7, and the point of M6 is that it needs no further code.
- **Any German-specific typography beyond the face:** German quotation marks
  („…“), `polyglossia`/`babel` hyphenation, and noun capitalisation or
  article handling. Vocabulary columns don't wrap, so hyphenation has nothing
  to act on there. If the dev wants any of these after seeing the PDFs, it is
  a spec change at that point.
- **Warnings for a German file's odd rows** (§2's three-tab case, a Chinese
  file moved into `tree-German`). That is M9.
- **Renaming `xecjk.tex`, `_pair_hanzi_pinyin`, `\HanziPinyin` or
  `GRAMMAR_PINYIN_GAP`.**

## Context

- **The dev's German tree exists and is empty**:
  `~/Documents/Idiomas/tree-German`, registered since Sprint 4 with input
  method `com.apple.keylayout.USInternational-PC` for both the word and the
  translation. So there are no existing German files whose format could
  break, and the hand-test starts from an empty tree.
- **Where the kind is now needed and wasn't before:** `parser.parse`,
  `writer.write`/`save`, `store.walk`/`tag_index`, `browse.paths_with_tag`
  and `BrowseScreen`. Everything else got it in M5.
- **Tests.** Every call to `parse`, `write`, `save`, `walk` and `tag_index`
  in the tests gains `kind=CHARACTER_PHONETIC`. These are mechanical changes:
  no test is dropped and no assertion weakened. M5's test that pinned
  `NotImplementedError` for the alphabetical renderer is replaced by tests of
  the real renderer.
