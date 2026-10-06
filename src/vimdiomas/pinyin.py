"""Pure conversion between numbered and tone-marked pinyin, plus hanzi -> pinyin guessing.

Numbered pinyin looks like "ni3hao3" (tone digits 1-4, with 5 or 0 for neutral).
Tone-marked pinyin looks like "nǐhǎo". `v` and `u:` are both accepted as `ü` on
input; `u:` is the canonical spelling produced on output.
"""

import re
import unicodedata
from functools import lru_cache

from pypinyin import Style, pinyin as _pypinyin

# Tone-marked vowel forms, indexed [tone1, tone2, tone3, tone4] for each bare vowel.
_TONE_MARKS = {
    "a": "āáǎà",
    "e": "ēéěè",
    "i": "īíǐì",
    "o": "ōóǒò",
    "u": "ūúǔù",
    "ü": "ǖǘǚǜ",
}

# toned character -> (bare vowel, tone digit 1-4)
_CHAR_TO_TONE = {
    mark: (base, str(i + 1))
    for base, marks in _TONE_MARKS.items()
    for i, mark in enumerate(marks)
}

# Lowercase only (Sprint 6 M3, #19): a stored value like "Txu4" — written by
# `guess()` before it dropped non-hanzi segments — renders as "xù", exactly as
# a freshly guessed one, rather than as "Txù".
_SYLLABLE_RE = re.compile(r"([a-zü:]+)([0-5])")

# What pypinyin produces with no vowel (嗯 n2, 呣 m2, 噷 hm5, 哼 hng4), and
# the letter that carries the tone: the `n` of ng/hng, the `m` of hm (#4).
_SYLLABIC_CONSONANTS = {"n": 0, "m": 0, "ng": 0, "hm": 1, "hng": 1}

# Combining marks for tones 1-4. Unicode has precomposed ń ň ǹ and ḿ but no
# m̄, m̌, m̀, so a syllabic consonant is marked with these and NFC-normalised:
# the precomposed glyph wherever one exists, the combining form otherwise.
_COMBINING = {"1": "\u0304", "2": "\u0301", "3": "\u030c", "4": "\u0300"}

# CJK Unified Ideographs (common) and Extension A: what counts as hanzi both
# for `guess()` (which syllables it emits) and for the grammar renderer's
# pairing (which characters get one) — one definition for both (#19).
_HANZI_RANGES = ((0x4E00, 0x9FFF), (0x3400, 0x4DBF))


_HANZI_RUN_RE = re.compile(
    "[" + "".join(f"{chr(low)}-{chr(high)}" for low, high in _HANZI_RANGES) + "]+"
)


def is_hanzi(ch: str) -> bool:
    codepoint = ord(ch)
    return any(low <= codepoint <= high for low, high in _HANZI_RANGES)


def _mark_vowel_index(letters: str) -> int | None:
    if "a" in letters:
        return letters.index("a")
    if "e" in letters:
        return letters.index("e")
    if "ou" in letters:
        return letters.index("ou")
    for i in range(len(letters) - 1, -1, -1):
        if letters[i] in "iouü":
            return i
    return _SYLLABIC_CONSONANTS.get(letters)


def to_tone_mark_syllables(numbered: str, *, unsupported: list[str] | None = None) -> list[str]:
    """Numbered pinyin ("ni3hao3") to a list of tone-marked syllables
    (["nǐ", "hǎo"]) — the per-syllable half of `to_tone_marks`.

    Never raises (Sprint 6 M3, #4): a syllable with nothing to carry its tone
    comes out as its bare letters, and — when `unsupported` is given — its
    numbered form is appended there so a caller can report it."""
    out = []
    for letters, digit in _SYLLABLE_RE.findall(numbered):
        letters = letters.replace("u:", "ü").replace("v", "ü")
        if digit in ("0", "5"):
            out.append(letters)
            continue
        i = _mark_vowel_index(letters)
        if i is None:
            out.append(letters)
            if unsupported is not None:
                unsupported.append(letters + digit)
        elif letters[i] in _TONE_MARKS:
            toned_char = _TONE_MARKS[letters[i]][int(digit) - 1]
            out.append(letters[:i] + toned_char + letters[i + 1 :])
        else:
            marked = letters[: i + 1] + _COMBINING[digit] + letters[i + 1 :]
            out.append(unicodedata.normalize("NFC", marked))
    return out


def to_tone_marks(numbered: str, *, unsupported: list[str] | None = None) -> str:
    """Numbered pinyin ("ni3hao3") to tone-marked pinyin ("nǐhǎo")."""
    return "".join(to_tone_mark_syllables(numbered, unsupported=unsupported))


@lru_cache(maxsize=1)
def _valid_syllables() -> frozenset[str]:
    from pypinyin import pinyin_dict

    syllables = set()
    for readings in pinyin_dict.pinyin_dict.values():
        for reading in readings.split(","):
            syllables.add(_strip_tones(reading)[0])
    return frozenset(syllables)


def _strip_tones(marked: str) -> tuple[str, list[str | None]]:
    """Bare letters (ü kept as ü) plus a parallel per-character tone list."""
    bare_chars = []
    tones: list[str | None] = []
    for ch in marked:
        if ch in _CHAR_TO_TONE:
            base, tone = _CHAR_TO_TONE[ch]
            bare_chars.append(base)
            tones.append(tone)
        else:
            bare_chars.append(ch)
            tones.append(None)
    return "".join(bare_chars), tones


def _segment(bare: str) -> list[str]:
    valid = _valid_syllables()
    n = len(bare)

    @lru_cache(maxsize=None)
    def rec(i: int) -> list[str] | None:
        if i == n:
            return []
        for j in range(min(n, i + 6), i, -1):
            piece = bare[i:j]
            if piece in valid:
                rest = rec(j)
                if rest is not None:
                    return [piece] + rest
        return None

    result = rec(0)
    if result is None:
        raise ValueError(f"cannot segment pinyin: {bare!r}")
    return result


def from_tone_marks(marked: str) -> str:
    """Tone-marked pinyin ("nǐhǎo") to numbered pinyin ("ni3hao3")."""
    bare, tones = _strip_tones(marked)
    syllables = _segment(bare)

    out = []
    pos = 0
    for syllable in syllables:
        syllable_tones = tones[pos : pos + len(syllable)]
        pos += len(syllable)
        tone = next((t for t in syllable_tones if t is not None), "5")
        out.append(syllable.replace("ü", "u:") + tone)
    return "".join(out)


def guess(hanzi: str) -> str:
    """Hanzi to numbered pinyin via pypinyin, e.g. guess("牛肉") -> "niu2rou4".

    Only hanzi contribute syllables (Sprint 6 M3, #19): guess("T恤") is
    "xu4", not "Txu4". Each run of consecutive hanzi goes to pypinyin whole,
    so a word's reading still comes from its context (银行 is yin2hang2)."""
    return "".join(
        group[0]
        for run in _HANZI_RUN_RE.findall(hanzi)
        for group in _pypinyin(run, style=Style.TONE3, neutral_tone_with_five=True)
    )
