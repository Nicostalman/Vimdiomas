# M2 · Pinyin — Validation

Roadmap's own "Done when": *A conversion table of ~40 cases — every tone, `ü`, `ou`, `iu`, `ui`, neutral tones, multi-syllable words — passes in both directions.*

## Checks

1. `pip install -e ".[dev]"` succeeds with `pypinyin` installed as a resolved dependency.
2. `pytest` passes, including a test module exercising the ~40-row conversion table:
   - Every row: `to_tone_marks(numbered) == marked`.
   - Every row: `from_tone_marks(marked)` produces the canonical numbered form (per the `v`/`u:` and neutral-tone canonicalization decisions in `requirements.md`) — i.e. `from_tone_marks(to_tone_marks(numbered))` round-trips to the canonical numbered spelling of `numbered`.
   - Table coverage, concretely: all of tones 1/2/3/4 appear; neutral tone appears via both `5` and `0` numbered input; `ü` appears via both `v` and `u:` input spellings; `ou`, `iu`, and `ui` each appear at least once with a non-neutral tone so mark placement is checked; at least 2-3 multi-syllable words (e.g. `ni3hao3`, `niu2rou4`) are included.
3. `guess()` spot-checks: `guess("牛肉") == "niu2rou4"`, `guess("你好") == "ni3hao3"`, and at least one word containing a neutral-tone syllable, asserting the expected numbered-pinyin string.
4. No regressions: existing M0/M1 tests (`pytest` full suite) still pass unchanged.

## Definition of done

- All of the above pass locally.
- `pinyin.py` exports exactly the three functions (`to_tone_marks`, `from_tone_marks`, `guess`) with no parser/writer/TUI wiring — that's out of scope per `requirements.md`.
