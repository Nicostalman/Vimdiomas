# M2 · Pinyin — Requirements

## Roadmap anchor

**Deliverable.** `pinyin.py` with three pure functions: `to_tone_marks("ni3hao3") → "nǐhǎo"`, its inverse, and `guess("牛肉") → "niu2rou4"` via pypinyin. Accepts `v` and `u:` for `ü`; tone 5 and 0 are neutral and unmarked.

**Done when.** A conversion table of ~40 cases — every tone, `ü`, `ou`, `iu`, `ui`, neutral tones, multi-syllable words — passes in both directions.

## Scope

In scope for this phase:

- `src/idiomas/pinyin.py` with three pure functions:
  - `to_tone_marks(numbered: str) -> str` — numbered pinyin (e.g. `"ni3hao3"`) to tone-marked (`"nǐhǎo"`). Operates on whole multi-syllable strings, splitting into syllables internally.
  - `from_tone_marks(marked: str) -> str` — the inverse: tone-marked pinyin back to numbered.
  - `guess(hanzi: str) -> str` — hanzi to numbered pinyin via `pypinyin`, e.g. `guess("牛肉") -> "niu2rou4"`.
- Add `pypinyin` to `[project.dependencies]` in `pyproject.toml`.
- A ~40-case conversion table (fixture) covering every tone (1-4, plus neutral as 5/0), `ü` (both `v` and `u:` spellings), `ou`, `iu`, `ui`, neutral tones, and multi-syllable words, asserting round-trip correctness in both directions.

Explicitly deferred:

- Any validation or error handling for malformed numbered-pinyin input. The pinyin field is expected to be populated by `guess()` output (autocompleted from hanzi) rather than typed freely, so `to_tone_marks`/`from_tone_marks` are not required to handle garbage gracefully in this phase. No `try/except` or input-sanity checks are added on this basis.
- Wiring `pinyin.py` into the parser/writer (M1) or the TUI's autofill behavior (M5) — this phase delivers the pure conversion functions only.
- Any language other than Mandarin/hanzi (see roadmap's "Later" section).

## Decisions

- **pypinyin is a main dependency**, not optional — `pinyin.py` is core functionality (used directly by `guess`), not a dev/test-only concern.
- **Whole-string API.** `to_tone_marks`/`from_tone_marks` take a full pinyin string (e.g. `"ni3hao3"`) and split/rejoin syllables internally, matching the roadmap's own example. Callers never need to pre-split into syllables.
- **`ü` input spelling.** `to_tone_marks` accepts both `v` and `u:` as the `ü` placeholder in numbered input (e.g. `nv3` and `nu:3` both parse). `from_tone_marks` needs a single canonical output spelling for `ü` when converting back to numbered form; `u:` is chosen as canonical (matches common numbered-pinyin convention and is unambiguous, unlike `v` which isn't a real pinyin letter but is still widely used for typing).
- **Neutral tone.** Tone `5` and tone `0` are both accepted as "neutral" in numbered input and render with no tone mark. Going the other direction (`from_tone_marks` on an unmarked syllable), the canonical numbered output for neutral is `5`.
- **No error handling for malformed input** — see deferred, above. Functions are pure and assume well-formed input; behavior on malformed input is unspecified/undefined for this phase.
