# M6 · Pinyin editable by hand — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Pinyin (§2)

- `pinyin.py`: `normalise` and `syllable_count`. `normalise` reuses
  `_valid_syllables`, `_strip_tones` and `_segment`. `from_tone_marks` is left
  as it is.
- `tests/test_pinyin.py`: tests 1–3 of §6.

## 2. The field (§1, §3)

- `entry.py`: `#reading` enabled and following `_apply_target_state`;
  `action_next_field` from Pinyin to the next field in the chain;
  `_last_guess` and the hand-edit test in `_on_word_changed`; reset in
  `_clear_form`. Update the `TAB_SKIP_IDS` comment ("read-only" no longer
  holds).
- `tests/test_tui_entry_screen.py`: tests 4–7 and 13 of §6.

## 3. Create (§4)

- `entry.py`: one helper that turns the field into the reading to store, or
  notifies and returns `None` (§4.2), called from `_create_entry` and from
  both entry-writing paths of `_create_grammar_entry` before anything is
  appended to the deck.
- `tests/test_tui_entry_screen.py`: tests 8–12 of §6.

## 4. Specs and the real thing (§5)

- `design.md`: the two bullets of §5.
- Run the app on a Chinese notebook: click Pinyin, hand-edit, Create, compile,
  and look at the PDF; the two refusals; a German notebook's Entry. Note what
  was seen in `validation.md` §2.
- `uv run --extra dev pytest` in full.
