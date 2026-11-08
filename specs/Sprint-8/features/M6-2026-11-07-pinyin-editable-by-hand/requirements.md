# M6 · Pinyin editable by hand — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M6 · Pinyin
editable by hand*, as written on 2026-10-30, before this spec conversation:

> **Deliverable.**
>
> - Entry's reading field (Pinyin, Chinese only) is no longer disabled. A mouse
>   click focuses it and its text can be edited like any other field.
> - `tab` still skips it, from every field. `tab` pressed *in* it moves on to
>   the field after it (Translation), as if it had been reached in order.
> - Editing the word re-guesses the reading, replacing a hand edit; the field
>   follows the word until it is edited after the word's last change.
> - On Create, a hand-typed reading is normalised to the stored numbered form:
>   numbered syllables as they are; tone-marked or toneless syllables converted
>   (`xiǎo` → `xiao3`, `ma` → `ma5`); punctuation, symbols and spaces kept;
>   letters lowercased. A reading that cannot be read as pinyin (`xyz3`, a
>   stray digit) is refused with an error notification, nothing written and
>   the form kept.
> - `design.md`: a field `tab` skips can still be reached with the mouse; this
>   is the one such field.
>
> **Done when.** On a Chinese notebook's Entry, a click on Pinyin focuses it, a
> hand edit is saved as numbered pinyin and printed tone-marked, `tab` never
> lands on the field, and an unreadable reading is refused without writing. A
> German notebook's Entry is unchanged. The full test suite passes.

The spec conversation changed two things, and the roadmap has been updated to
match. **A hand edit survives later edits of the word** (the third bullet is
reversed). **A hand edit whose syllable count does not match the word's hanzi
is refused**, like an unreadable one (new).

The source is the dev's request of 2026-10-30: "modifying pinyin by hand
during the input. the tab should continue skipping the field but it should be
accessible through clicking with the mouse." There is no backlog entry. The
notes ([`../../guidelines/notes-sprint-8.md`](../../guidelines/notes-sprint-8.md),
*M5 and M6 added after the dev's hand-testing*) record why it is in Sprint 8.

**Why it is needed.** The reading is guessed by `pinyin.guess` (pypinyin) and
the field is `disabled=True` (`entry.py`, `compose`), so a wrong guess, such as
a polyphone read the wrong way or a name, can only be fixed by editing the
`.md` file by hand afterwards.

## Decisions

Settled with the dev on 2026-11-07, unless marked as the agent's.

| Decision | Rationale |
| --- | --- |
| **A hand edit survives later edits of the word** | The dev's choice, over the roadmap's proposal that a word change re-guesses and replaces it. |
| **Emptying the field by hand hands it back to the word** (the agent's) | Otherwise, after a hand edit, the only way back to a guess would be clearing the whole form. An empty field is never something to keep: see §3.3. |
| **Only the mouse reaches the field**; no key does | The dev's choice, matching their request. The Keys table in `design.md` is unchanged. |
| **The refusal reads `"<text>" isn't pinyin.`** | The dev's choice, in the shape of the app's other refusals (`X already exists.`). |
| **A hand edit with a syllable count different from the word's hanzi count is refused** | The dev's choice, over saving with a warning or silently. Grammar files pair one syllable per hanzi (`compile._pair_hanzi_pinyin`), so a mismatch would misplace or drop syllables there. |
| **The count refusal reads `"<text>" has N syllable(s) for M hanzi.`** (the agent's) | Same shape as the dev's chosen wording; it names both counts, as the question proposed. |
| **The normalising and checking apply to hand edits only** (the agent's) | An untouched guess is saved exactly as today. pypinyin's guess is not re-checked against rules it did not have to follow before, so nothing that saves today stops saving. |

## 1. The field

### 1.1 Enabled, reached by the mouse

- `#reading` is composed without `disabled=True`.
- `_apply_target_state` sets its `disabled` exactly as it does for `word`,
  `translation` and `note`: disabled with no valid target, enabled with one.
  It stays hidden on `(new category)`, as today.
- A mouse click on it focuses it, and it edits like any other `TextField`: the
  control-character rule (Sprint 6 M1), `q` types, and `esc` climbs to the form
  panel.
- A click on it while the tree panel has focus moves focus into the form panel
  and onto the field. This is Textual's own click-to-focus, and the panel model
  follows focus wherever it lands.
- Moving from Word to Pinyin by click blurs `WordInput`, which switches to the
  translation input method (Sprint 2 M4, Sprint 4 M6). That is the right one
  for typing pinyin. Nothing changes in `WordInput`.

### 1.2 `tab` skips it, and leaves it forward

- `TAB_SKIP_IDS` keeps `"reading"`, so `_visible_field_ids` and the `tab` chain
  never include it, and `_focus_first_field` never lands on it.
- `action_next_field` with Pinyin focused (today it returns, since the field is
  not in the chain) moves to the first field after `reading` in `FIELD_ORDER`
  that is in the chain: Translation. With Translation and Note somehow not in
  the chain, it moves to the Create button.
- shift+hjkl and `enter` on the form panel land on the panel's first content as
  today, which is never Pinyin (Word, or Subtitle on a grammar category, comes
  first).

### 1.3 German is unchanged

A kind with `has_reading = False` composes no `#reading`. Every query above is
`self.query("#reading")` or guarded the same way, as today.

## 2. Normalising a hand edit (`pinyin.normalise`)

A new pure function, `pinyin.normalise(text: str) -> str`, returns the stored
numbered form, or raises `ValueError` when the text cannot be read as pinyin.

### 2.1 What it accepts

The text is read left to right as **runs** and the characters between runs.
A run is a maximal sequence of pinyin characters: the Latin letters `a`–`z`
in either case, the tone-marked vowels of `_TONE_MARKS` (and their capitals),
`ü`, a `:` directly after a `u`, and the digits `0`–`9`.

- **Between runs:** punctuation, symbols and spaces are kept exactly as typed.
  These are Unicode `P*`, `S*` and `Z*`, the same characters `to_tone_marks`
  keeps between syllables, plus spaces.
- **Inside a run**, after lowercasing, syllables are taken from the left:
  - a **numbered syllable**: letters with no tone marks, then one digit `0`–`5`,
    whose letters (with `v` and `u:` read as `ü`) are a valid syllable
    (`_valid_syllables()`, pypinyin's set). It is kept as typed, with `ü` and
    `v` written `u:`;
  - otherwise the **letters up to the next digit, or to the end of the run**,
    are segmented as tone-marked or toneless pinyin, as `from_tone_marks`
    does: each syllable takes the tone its mark gives, or `5` with no mark.
    `xiǎo` → `xiao3`, `ma` → `ma5`, `nǐhǎo` → `ni3hao3`.
- Runs may mix both: `ni3hǎo` → `ni3hao3`.

### 2.2 What it refuses

`ValueError` for any of these:

- a digit that does not end a numbered syllable: `3ni`, `ni33`, `ni6`;
- tone-marked letters followed by a digit: `xiǎo3`;
- letters that do not segment into valid syllables: `xyz`, `xyz3`;
- any other character between runs that is not punctuation, a symbol or a
  space: a hanzi typed into the field, another script's letter (`ß`, `я`),
  a letter with an accent pinyin does not use (`é` is fine as a tone mark,
  `ç` is not).

An empty text normalises to `""`.

### 2.3 Examples (each a test)

| Typed | Stored |
| --- | --- |
| `xiao3/zhong1/da4hao4` | `xiao3/zhong1/da4hao4` |
| `xiǎo/zhōng/dàhào` | `xiao3/zhong1/da4hao4` |
| `Xing2` | `xing2` |
| `ma` | `ma5` |
| `lv4`, `lü4`, `lǜ` | `lu:4` |
| `ni3 hǎo` | `ni3 hao3` |
| `yin2hang2` | `yin2hang2` |
| `xyz3`, `ni6`, `xiǎo3`, `3`, `你` | refused |

And the round trip: for every stored reading `r` in the test fixtures,
`normalise(to_tone_marks(r))` gives back the same syllables as `r`, for the
fixtures' tone 1–4 syllables and neutral `5`. A stored `0` comes back as `5`.

### 2.4 Counting

`pinyin.syllable_count(numbered: str) -> int` is the number of numbered
syllables (`_SYLLABLE_RE` matches) in a stored reading. The word's hanzi count
is the number of its characters for which `is_hanzi` is true, the same
definition `guess` and the grammar pairing use.

## 3. Following the word, and hand edits

### 3.1 When the field is a hand edit

The screen keeps `_last_guess`, the last value `_on_word_changed` wrote into
the field (`""` initially and after every `_clear_form`). The field is a
**hand edit** when its value is not empty and differs from `_last_guess`.
This test reads the values, so it does not depend on the order in which
`Input.Changed` events arrive.

### 3.2 A word change

`_on_word_changed` guesses as today and stores the guess in `_last_guess`. It
writes the guess into the field only if the field is **not** a hand edit (its
value is empty or equal to the previous `_last_guess`). A hand edit stays as
it is, however many times the word changes afterwards.

### 3.3 Back to following the word

The field follows the word again when:

- it is emptied by hand (an empty field is never a hand edit; the next word
  change fills it);
- the form is cleared: after a successful Create, or on a change of tree
  target (`_clear_form`);
- it is edited back to exactly the current guess.

## 4. Create

### 4.1 An untouched guess

Saved exactly as today, with no normalising and no checks.

### 4.2 A hand edit

On Create, in `_create_entry` and `_create_grammar_entry` (every path that
writes an `Entry`, including a grammar entry added together with a new
subtitle), before anything is written or added to the deck:

1. `normalise(value)`. On `ValueError`: error notification `"<value>" isn't
   pinyin.`, with the field's value as typed. Nothing is written, the form
   keeps every value, and focus goes to Pinyin.
2. Compare `syllable_count(normalised)` with the word's hanzi count. If they
   differ: error notification `"<value>" has N syllable(s) for M hanzi.`
   (`1 syllable`, `2 syllables`; `hanzi` for any count). Same outcome as 1.
3. Otherwise the entry is saved with the normalised reading.

Both notifications use `markup=False` (Sprint 6 M2: shown exactly as typed).
A `(new subtitle)` Create with no word writes no entry, so it does not check
the reading. The subtitle alone is created as today.

### 4.3 Printed

The PDF and Browse print the stored reading through `display_reading`
(Sprint 8 M5). A hand edit with punctuation of its own prints as it was typed,
tone-marked. Nothing changes in `compile.py` or `browse.py`.

## 5. `design.md`

- In *Keys* (or the Entry form section): **a field `tab` skips can still be
  reached with the mouse.** Entry's Pinyin is the one such field. `tab` from
  it moves on to Translation.
- In the Entry section: the Pinyin field follows the word until it is edited
  by hand. A hand edit is kept until the field is emptied or the form is
  cleared. On Create, a hand edit is stored as numbered pinyin, and refused,
  with the two wordings above, when it isn't pinyin or its syllables don't
  match the word's hanzi.

## 6. Tests

`tests/test_pinyin.py`:

1. §2.3's table, row by row; the refusals raise `ValueError`.
2. The round trip in §2.3.
3. `syllable_count`: `xiao3/zhong1/da4hao4` → 4, `""` → 0, `T` → 0.

`tests/test_tui_entry_screen.py` (Chinese config unless stated):

4. Pinyin is enabled with a valid target and disabled without one; a click
   (`pilot.click("#reading")`) focuses it.
5. `tab` from Word goes to Translation, never to Pinyin (existing test kept).
   `tab` with Pinyin focused goes to Translation.
6. Typing a word fills Pinyin. Editing Pinyin, then changing the word, leaves
   the hand edit. Emptying Pinyin, then changing the word, guesses again.
7. After Create, and after moving to another target, the next word is guessed
   again (the hand-edit state is gone).
8. Create with a hand edit `xiǎo/zhōng/dàhào` on 小/中/大號 saves
   `xiao3/zhong1/da4hao4` (the file is read back).
9. Create with `xyz3` → error notification `"xyz3" isn't pinyin.`, the file
   is unchanged, every field keeps its value, and Pinyin has focus.
10. Create with `ni3` on 你好 → `"ni3" has 1 syllable for 2 hanzi.`, the file
    is unchanged.
11. An untouched guess is saved as today (existing tests kept).
12. A grammar category, both with an existing subtitle and with
    `(new subtitle)`: the hand edit is normalised, and refused the same way.
13. German: no `#reading`, `tab` order unchanged (existing tests kept).

## 7. Found during implementation

- **A numbered `m` is accepted** (§2.1). pypinyin's set holds that syllable
  only tone-marked (`ḿ`), so its bare form is missing, and §2.1 as written
  refused `m2`, which is what `guess` itself gives 呣. A numbered syllable's
  letters are valid if they are in the set or in `_SYLLABIC_CONSONANTS`.
- **One existing test had to change.** `validation.md` §1 says the existing
  Entry tests pass unchanged, but `test_pinyin_field_is_disabled_and_skipped_by_tab`
  asserted the `disabled` this milestone removes. It is now
  `test_pinyin_field_is_skipped_by_tab`, without that assertion.

## Out of scope

- **Editing an entry already saved.** Still in the Postponed table.
- **A key that reaches Pinyin.** Mouse only, by decision.
- **Checking readings in files edited by hand** (Inspect Tree's warnings).
  `normalise` could serve that later. It is not wired there now.
- **Erhua written into a syllable** (`huar4`). pypinyin's set has no such
  syllables, so it is refused. 兒 has a hanzi of its own (`er2`), which counts.
