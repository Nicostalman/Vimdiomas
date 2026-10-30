# M5 · Aligned rows and pinyin punctuation — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [x] `uv run --extra dev pytest` passes in full, integration tests included
      (they need `xelatex` and `pdftotext`): 1609 passed, 2026-10-30.
- [x] Pinyin tests: the §2.1 guesses; `to_tone_marks` keeps `/`, spaces and
      `…` and drops `T`; `display_reading` weaves the word's `/` into a reading
      without any, leaves a reading with its own alone, appends leftover
      syllables, and gives `""` for `""`.
- [x] Compile tests: no `multicolumn` for the *Plástico* rows; one for a German
      compound over the cap and one for a reading that leaves under 12em; the
      `\GlossColumn` column spec for both kinds; `\FitColumn` only for ordinary
      rows; 小/中/大號 renders `xiǎo/zhōng/dàhào` from `xiao3zhong1da4hao4`
      and from `xiao3/zhong1/da4hao4`.
- [x] Integration: the *Plástico* rows compile inside the margins, with one x
      for every row's pinyin and one for every gloss (`pdftotext -bbox`).
- [x] Browse shows `xiǎo/zhōng/dàhào` for the stored `xiao3zhong1da4hao4`;
      Entry guesses `xiao3/zhong1/da4hao4`.

## 2. By the agent, on the real PDF

- [x] The two screenshots' rows (*Plástico*, and 小/中/大號, 件, 條) compiled
      to PNG with `pdftoppm` and looked at: three aligned columns, notes
      wrapping inside the translation column, slashes in the pinyin. Also a German page: the long compound is still
      an exception, and a long translation wraps in its column.

## 3. By hand (the dev)

- [ ] Compile the notebook with the *Plástico* category (Compile rebuilds every
      notebook once, §4). Every row's pinyin and gloss start at the same place
      as their neighbours'; 瓶裝's note wraps under *embotellado*, not under the
      hanzi.
- [ ] The clothing notebook: 小/中/大號 prints `xiǎo/zhōng/dàhào`, with no
      change to its source file (`git diff` or a look at the `.md`).
- [ ] Entry: type 小/中/大號; the Pinyin field shows `xiao3/zhong1/da4hao4`.
- [ ] Browse, content mode: the 小/中/大號 row shows `xiǎo/zhōng/dàhào`.
- [ ] A German notebook with a long compound: still set across the full width.
- [ ] Nothing else looks different in a notebook whose glosses all fit.

## 4. Spec check

- [ ] `requirements.md`, `plan.md`, `design.md` and the code agree; anything
      that changed during implementation is recorded here.
