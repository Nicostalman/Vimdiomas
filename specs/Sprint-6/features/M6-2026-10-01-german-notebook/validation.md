# M6 · The German notebook — validation

The acceptance bar for merging `2026-10-01-m6-german-notebook`. It is the
roadmap's done-when, made checkable.

## Automated

*Run 2026-10-01 on the branch, re-run after the hand-test changes (§7, §8): `pytest` 1027 passed (including the real-pandoc
tier); the two greps below return nothing.*

- [x] `pytest` passes in full. No existing test is deleted except M5's
      `NotImplementedError` pin, which is replaced by tests of the real
      renderer. A test changed only to pass `kind=` asserts exactly what it
      did before.
- [x] **German round-trip:** both German fixtures (`Essen.md`,
      `Grammar/Konjunktionen.md`) parse with `ALPHABETICAL` and re-write
      byte-identically, and `parse(write(deck)) == deck` holds for them.
- [x] **Chinese round-trip unchanged:** every existing fixture still parses
      and re-writes byte-identically with `CHARACTER_PHONETIC`.
- [x] **The two-column row:** `Haus<TAB>house` parses as word and
      translation, `Haus<TAB>` as an empty translation, and a tab-indented
      `*note*` as a note. The writer emits `Haus<TAB>house` and refuses an
      alphabetical entry with a reading.
- [x] **The kind decides:** the German vocabulary fixture parsed as
      `CHARACTER_PHONETIC` yields no entries, and as `ALPHABETICAL` yields
      them all.
- [x] **Uncategorized in the tree:** `walk` on a German tree marks a file of
      uncategorized two-column rows as `has_uncategorized`.
- [x] **Renderer:**
      - German vocabulary renders a two-column `longtable`, and German
        grammar renders `\GrammarWord` head lines.
      - Neither German markdown contains `\HanziPinyin` or a reading.
      - German's pandoc argv has no `cjkfont`, and Chinese's still does.
- [x] **Folders and long rows (§7, §8):** `ensure_tree` creates both
      folders, completes a tree with one, never makes a second `grammar/`;
      the wizard and notebook menu call it. A table that fits has no
      exception row, in either kind; a long word and a row that overruns each
      become one wrapped, indented exception row, for two columns and for
      three; real-toolchain PDFs, German and Chinese, end every word inside
      the margin.
- [x] **Compile is per notebook:** with two languages configured, the
      notebook menu's Compile compiles only that language's tree.
- [x] **Real toolchain:** both German fixtures compile to PDF with real
      pandoc and xelatex. One of them has a grammar phrase long enough to
      wrap.
- [x] **No hardcoded escape hatch left:**
      `grep -n "NotImplementedError" src/idiomas/compile.py` and
      `grep -n "functional=False" src/idiomas/languages.py` return nothing.

## No Chinese regression, against the dev's real tree

Run by the agent with M5's `check_equivalence.py` (`plan.md` groups 1 and 7)
on a **copy** of `~/Documents/Idiomas/tree-Chinese`, with a scratch cache. The
dev's real files and cache are never touched.

- [x] For every `.md` file, the markdown sent to pandoc and the pandoc argv
      are identical before and after. *(6 of 6 files in the dev's
      `tree-Chinese`.)*
- [x] The stamps differ for every file, and only because of the template
      edit (`requirements.md` §4). This is expected, not a failure. *(All 6
      differ.)*
- [x] Every page of every PDF rasterises (`pdftoppm -r 100`) to a
      byte-identical PNG before and after. *(6 of 6 pages `cmp`-identical.)*

## By hand (the dev)

*Hand-tested and approved by the dev on 2026-10-01, in two rounds: the first produced §7 and §8 of `requirements.md`; the second confirmed them, including the Chinese grammar wrap.*

- [x] **German opens.** The landing menu's German notebook reads "Add words,
      explore and compile your German notes." and opens the notebook menu.
- [x] **Entry, vocabulary.** In an empty `tree-German`, create a file in
      Inspect Tree (for example `Vocabulary/Essen`), then in Enter vocabulary:
      - there's no Hanzi or Pinyin field, the first field reads "Word", and
        nothing is guessed;
      - `tab` goes Word → Translation → Note;
      - the input source switches on entering and leaving Word;
      - create a category and a few entries, one with a note and one
        uncategorized, and each create clears the form.
- [x] **Entry, grammar.** Create `Grammar/Konjunktionen`. Its category form
      shows the Subtitle field, and `(new subtitle)` creates one with an
      entry under it. Include a phrase long enough to wrap in the PDF.
- [x] **On disk.** Open the files in Neovim (Inspect Tree's MD mode `Enter`).
      Each row is `word<TAB>translation`, and a note is the indented `*…*`
      line below it. Add a row by hand, with one tab, and it shows up in the
      app.
- [x] **Compile.** The notebook menu's Compile builds both PDFs, and Inspect
      Tree's PDF mode previews them.
- [x] **PDFs approved by eye:**
      - vocabulary: the word large, the translation, an italic note in
        parentheses, Latin Modern throughout;
      - grammar: the stacked phrase / translation / note units, the
        subtitle's en dash heading, and a wrapped phrase that doesn't
        overlap;
      - no stray CJK spacing around quotes.
- [x] **Browse** fuzzy-finds the German PDFs, and filters by a tag added in
      Neovim.
- [x] **Chinese untouched.** The first Compile of the Chinese notebook
      rebuilds every file once (the template changed), and the PDFs look as
      before. Chinese Entry still guesses pinyin, and the second Compile
      reports everything up to date.
- [x] `idiomas compile` from the shell compiles both notebooks.
- [x] **Folders (§7).** Opening the German notebook creates `Grammar/` in
      `tree-German`, which had only `Vocabulary/`. A fresh wizard run's trees
      have both.
- [x] **A long word (§8).** A word like
      `Donaudampfschifffahrtsgesellschaftskapitänsmütze` in a vocabulary file:
      the other rows' translations stay where they were, the long row sits in
      the margins, and a translation long enough to wrap continues on an
      indented line. The same in the Chinese notebook, with a very long gloss
      and with a very long grammar phrase.
