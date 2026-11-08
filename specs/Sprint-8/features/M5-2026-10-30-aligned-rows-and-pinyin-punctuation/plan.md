# M5 · Aligned rows and pinyin punctuation — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Pinyin (§2)

- `pinyin.py`: `guess` keeps `P*`/`S*` characters; `to_tone_marks` keeps the
  non-letter, non-digit characters between syllables; new `display_reading`.
- `tests/test_pinyin.py` as §5 lists. The existing `guess` and
  `to_tone_marks` tests pass unchanged.

## 2. The table (§1, §2.3)

- `templates/xecjk.tex`: the four lengths and `\FitColumn`.
- `compile.py`: `MIN_GLOSS_EM`; `_exception_rows` over the word and reading
  columns only; `_render_table` emits the measuring block and the `p` column,
  and builds the reading with `display_reading` and `_curl_quotes`.
- `tests/test_compile.py` as §5 lists, existing tests updated to the new column
  spec and exception rule.

## 3. Browse (§2.3)

- `browse.hit_fields` through `display_reading`.
- `store.pinyin_key` drops `P*`/`S*` characters (§2.4), with its tests in
  `tests/test_store.py`.
- `tests/test_tui_browse_screen.py`, and the Entry guess test in
  `tests/test_tui_entry_screen.py`.

## 4. Specs and the real thing (§3)

- `design.md`: the two bullets.
- Compile the dev's screenshot rows for real and look at the PDF.
- `uv run pytest` in full.
