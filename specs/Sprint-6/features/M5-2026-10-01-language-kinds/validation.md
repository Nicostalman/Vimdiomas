# M5 · Language kinds — validation

The acceptance bar for merging `2026-10-01-m5-language-kinds`. It is the
roadmap's done-when, made checkable, with the byte-identity clause replaced as
explained in `requirements.md` (*A correction to the roadmap's done-when*).

## Automated

- [x] `pytest` passes in full (965 passed, 2026-10-01). No existing test is deleted. A test changed by
      the rename asserts the same behaviour under the new names.
- [x] **No hardcoded Chinese left outside the registry.** These commands
      return nothing:
      - `grep -rn "FUNCTIONAL_LANGUAGES\|LANGUAGE_HINTS" src`
      - `grep -rnE "entry\.(hanzi|pinyin|gloss)|\b(hanzi|pinyin|gloss)=" src`
        (`idiomas.pinyin` imports and the `pinyin_dict` library name are not
        matches, which is why this is not a bare `\.pinyin`)
      - `grep -n "CJK_FONT_NAME" src/idiomas/compile.py`

      `pinyin.py`, `_pair_hanzi_pinyin`, `\HanziPinyin` and `is_hanzi` stay,
      by design (`requirements.md` §4).
- [x] **Round-trip unchanged:** every fixture parses and re-writes
      byte-identically, as before the rename.
- [x] **Stamps unchanged:** the literal-digest test in `test_compile.py`
      passes. Its digest was computed on `main`.
- [x] **A table entry, not a code change:** the "Testonese" test passes. A
      character-and-phonetic language added only to `LANGUAGES` is functional
      on the landing menu, guesses pinyin in Entry, writes Chinese-shaped rows
      and compiles with the CJK font.
- [x] **Unknown language:** a config naming a language that isn't in the
      registry shows "Not available yet.", opens the placeholder, and is
      skipped by `idiomas compile`, with no exception.
- [x] **Routing for a kind without a reading:** an Entry given
      `ALPHABETICAL` has no reading field, a "Word" placeholder, and tabs from
      Word to Translation. `render_markdown` with `ALPHABETICAL` raises
      `NotImplementedError`.

## Equivalence against the dev's real tree

Run by the agent with `check_equivalence.py` (`plan.md` groups 1 and 7) on a
**copy** of `~/Documents/Idiomas/tree-Chinese`, with a scratch cache. The
dev's real files and cache are never touched.

- [x] For every `.md` file (6 today: 5 vocabulary and 1 grammar), the
      markdown sent to pandoc, the pandoc argv, and the stamp are identical
      before and after. *Run 2026-10-01: 6 files, `calls.json` identical.*
- [x] Every page of every PDF rasterises (`pdftoppm -r 100`) to a
      byte-identical PNG before and after. *Run 2026-10-01: 6 PDFs, 6 pages,
      all `cmp`-identical.*

## By hand (the dev)

- [ ] `idiomas compile` on the real tree, run once on `main` (to bring the
      cache up to date) and then on this branch, reports "Chinese: everything
      is up to date." The stamps didn't move, so nothing rebuilds.
- [ ] Chinese Entry looks and behaves as before: the Hanzi and Pinyin
      placeholders, pinyin guessed as you type, `tab` skipping Pinyin, input
      source switching, create-and-clear, and the grammar subtitle flow.
- [ ] Inspect Tree, Browse and the notebook menu's Compile work as before on
      the real tree, including autocompile after adding an entry.
- [ ] German on the landing menu still says "Not available yet." and opens the
      placeholder.
- [ ] The wizard (run against a scratch config) still offers Chinese and
      German.

## Docs

- [x] `stack.md` has *Languages and kinds* and the field-name note.
- [x] The roadmap's M5 section carries the dated done-when correction.
- [x] `notes-sprint-6.md` has *Settled while speccing M5*.
- [x] `design.md` is unchanged.
