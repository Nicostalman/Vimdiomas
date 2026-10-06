# M6 · The grammar renderer — validation

Grounded in the roadmap's done-when condition, made concrete.

## Automated

- `pytest` — full suite passes, including every new test in `plan.md` groups
  1–4, and every pre-existing test unmodified.
- Specifically covered:
  - `to_tone_mark_syllables` splits numbered pinyin into one tone-marked
    syllable per group, including a neutral tone and `u:`/`v`; every existing
    `to_tone_marks` test still passes.
  - `_pair_hanzi_pinyin` pairs each hanzi character with its syllable in
    order, pairs a non-hanzi character (and any character past the end of
    the syllable list) with `""`, and never raises.
  - `render_markdown(deck, grammar=True)` emits `\HanziPinyin` calls (not a
    `longtable`) for grammar entries, an italic parenthetical note on the
    own line below the translation, and both gap constants; a `hanzi="..."` entry
    produces three empty-pinyin `\HanziPinyin` calls.
  - `render_markdown(deck, grammar=False)` is byte-for-byte what it is
    before this milestone — the explicit regression test, not just existing
    tests continuing to pass.
  - `compile_file`/`compile_all` pass `grammar` to `render_markdown`.
  - A grammar deck shaped like the dev's real `Grammar/Conjunctions.md`
    compiles to a real PDF (integration, real pandoc/xelatex) whose
    extracted text contains the hanzi, tone-marked pinyin, and translation.

## Manual, by the dev

Against the real tree (`~/Documents/Idiomas/tree-Chinese`).

- [ ] From the app (Entry or Inspect Tree's *Compile all*), recompile
      `Grammar/Conjunctions.md`. No manual cache deletion needed.
- [ ] Open the resulting `Grammar/Conjunctions.pdf` and compare it against
      `specs/Sprint-5/guidelines/image-1.png`:
  - [ ] Each entry reads as stacked lines (hanzi, pinyin, translation, and
        the note when there is one), not columns, every line flush with the
        left margin.
  - [ ] Pinyin sits very close under its hanzi; the pinyin→translation gap
        is a little larger; the gap before the next entry's hanzi is
        considerable, so each entry reads as one unit.
  - [ ] The gap between hanzi/pinyin/translation within one triad is
        visibly tighter than the gap between one triad and the next.
  - [ ] Pinyin is smaller than the hanzi and translation, in a paler shade.
  - [ ] Each pinyin syllable sits under its own hanzi character — check this
        specifically on a multi-character entry (`好啦`) and the note-bearing
        entries.
  - [ ] `...` (the ellipsis entry) shows no pinyin underneath it.
  - [ ] `### new cat`, the file's subtitle, renders as a heading below the
        `## Conjunctions` category heading, visually distinct from it
        (body size, bold, prefixed with a dash).
  - [ ] The gap between a subtitle's last entry and the next subtitle is the
        same as the gap between two entries.
  - [ ] A note (e.g. `*test none*`, `*prueba new cat*`) shows as an italic
        parenthetical on its own line below its entry's translation.
- [ ] Open a vocabulary file's PDF (e.g. anything under `Vocabulary/`) and
      confirm it looks exactly as it did before this milestone — still the
      three-column table, still `\Large` hanzi, nothing shifted.
- [ ] Run *Compile all* a second time with nothing changed: nothing
      recompiles (M2's staleness cache still holds).
- [ ] The dev approves the grammar layout by eye against `image-1.png`, with
      any spacing/shade adjustments folded back into `compile.py`'s
      constants and this milestone's spec files before merging.

## Merge bar

All automated checks pass, and the dev confirms the manual list.
