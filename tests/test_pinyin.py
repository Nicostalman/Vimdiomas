import pytest

from vimdiomas.pinyin import from_tone_marks, guess, is_hanzi, to_tone_mark_syllables, to_tone_marks

# (numbered input, expected tone-marked output, canonical numbered form)
# `canonical` differs from the input when the input used a non-canonical
# spelling that to_tone_marks/from_tone_marks still normalize (0 -> 5 for
# neutral tone, v -> u: for ü).
CONVERSION_TABLE = [
    # every tone, plain syllables
    ("ma1", "mā", "ma1"),
    ("ma2", "má", "ma2"),
    ("ma3", "mǎ", "ma3"),
    ("ma4", "mà", "ma4"),
    ("ma5", "ma", "ma5"),
    ("ma0", "ma", "ma5"),  # tone 0 is also neutral
    ("e1", "ē", "e1"),
    ("e2", "é", "e2"),
    ("e3", "ě", "e3"),
    ("e4", "è", "e4"),
    ("bo1", "bō", "bo1"),
    ("mo4", "mò", "mo4"),
    ("yi1", "yī", "yi1"),
    ("wu3", "wǔ", "wu3"),
    ("yu2", "yú", "yu2"),
    # simple multi-letter syllables
    ("ni3", "nǐ", "ni3"),
    ("hao3", "hǎo", "hao3"),
    ("wo3", "wǒ", "wo3"),
    ("ta1", "tā", "ta1"),
    # ou
    ("gou3", "gǒu", "gou3"),
    ("dou4", "dòu", "dou4"),
    ("tou2", "tóu", "tou2"),
    # iu (marks the u)
    ("liu2", "liú", "liu2"),
    ("jiu3", "jiǔ", "jiu3"),
    ("niu2", "niú", "niu2"),
    # ui (marks the i)
    ("gui4", "guì", "gui4"),
    ("hui2", "huí", "hui2"),
    ("sui4", "suì", "sui4"),
    # ü, both input spellings, canonicalized to u:
    ("nu:3", "nǚ", "nu:3"),
    ("nv3", "nǚ", "nu:3"),
    ("lu:4", "lǜ", "lu:4"),
    ("lv4", "lǜ", "lu:4"),
    ("lu:2", "lǘ", "lu:2"),
    ("lve4", "lüè", "lu:e4"),
    ("nve4", "nüè", "nu:e4"),
    # multi-syllable words
    ("ni3hao3", "nǐhǎo", "ni3hao3"),
    ("niu2rou4", "niúròu", "niu2rou4"),
    ("xi1hong2shi4", "xīhóngshì", "xi1hong2shi4"),
    ("pi2jiu3", "píjiǔ", "pi2jiu3"),
    ("zhong1guo2", "zhōngguó", "zhong1guo2"),
    ("ke3le4", "kělè", "ke3le4"),
    # multi-syllable words with a neutral-tone syllable
    ("ge1ge5", "gēge", "ge1ge5"),
    ("hai2zi5", "háizi", "hai2zi5"),
    ("tai4tai5", "tàitai", "tai4tai5"),
]


@pytest.mark.parametrize("numbered,marked,canonical", CONVERSION_TABLE)
def test_to_tone_marks(numbered, marked, canonical):
    assert to_tone_marks(numbered) == marked


@pytest.mark.parametrize("numbered,marked,canonical", CONVERSION_TABLE)
def test_from_tone_marks(numbered, marked, canonical):
    assert from_tone_marks(marked) == canonical


@pytest.mark.parametrize("numbered,marked,canonical", CONVERSION_TABLE)
def test_round_trip(numbered, marked, canonical):
    assert from_tone_marks(to_tone_marks(numbered)) == canonical


@pytest.mark.parametrize(
    "hanzi,expected",
    [
        ("牛肉", "niu2rou4"),
        ("你好", "ni3hao3"),
        ("的", "de5"),
    ],
)
def test_guess(hanzi, expected):
    assert guess(hanzi) == expected


# -- to_tone_mark_syllables (Sprint 5 M6) --------------------------------


def test_to_tone_mark_syllables_splits_into_one_per_syllable():
    assert to_tone_mark_syllables("tian1qi4") == ["tiān", "qì"]


def test_to_tone_mark_syllables_neutral_tone_stays_unmarked():
    assert to_tone_mark_syllables("ge1ge5") == ["gē", "ge"]
    assert to_tone_mark_syllables("ge1ge0") == ["gē", "ge"]


def test_to_tone_mark_syllables_normalizes_u_colon_and_v():
    assert to_tone_mark_syllables("nu:3") == ["nǚ"]
    assert to_tone_mark_syllables("nv3") == ["nǚ"]


def test_to_tone_mark_syllables_empty_string_returns_empty_list():
    assert to_tone_mark_syllables("") == []


@pytest.mark.parametrize("numbered,marked,canonical", CONVERSION_TABLE)
def test_to_tone_mark_syllables_joins_back_to_to_tone_marks(numbered, marked, canonical):
    assert "".join(to_tone_mark_syllables(numbered)) == to_tone_marks(numbered)


def test_is_hanzi():
    assert is_hanzi("天")
    assert is_hanzi("气")
    assert not is_hanzi(".")
    assert not is_hanzi("a")
    assert not is_hanzi("5")


# -- Sprint 6 M3 · #4: syllabic consonants ---------------------------------


@pytest.mark.parametrize(
    "numbered, marked",
    [
        ("n2", "ń"),
        ("n3", "ň"),
        ("n4", "ǹ"),
        ("n1", "n̄"),
        ("m2", "ḿ"),
        ("m1", "m̄"),
        ("m3", "m̌"),
        ("m4", "m̀"),
        ("ng2", "ńg"),
        ("ng3", "ňg"),
        ("hm2", "hḿ"),
        ("hng4", "hǹg"),
        ("hm5", "hm"),
    ],
)
def test_syllabic_consonants_are_marked(numbered, marked):
    unsupported = []
    assert to_tone_marks(numbered, unsupported=unsupported) == marked
    assert unsupported == []


@pytest.mark.parametrize("hanzi", ["嗯", "呣"])
def test_guessed_syllabic_consonant_renders(hanzi):
    """The report's two-line reproduction: this raised ValueError."""
    assert to_tone_marks(guess(hanzi)) in ("ń", "ḿ")


def test_an_unmarkable_syllable_prints_its_letters_and_is_reported():
    unsupported = []
    assert to_tone_marks("x4ni3", unsupported=unsupported) == "xnǐ"
    assert unsupported == ["x4"]


def test_an_unmarkable_syllable_without_a_report_list_still_does_not_raise():
    assert to_tone_mark_syllables("x4") == ["x"]


def test_nothing_pypinyin_guesses_makes_tone_marking_raise():
    """Every character in CJK Unified Ideographs, through guess and back out
    as tone marks: no exception, and nothing reported unsupported."""
    unsupported = []
    for codepoint in range(0x4E00, 0x9FFF + 1, 3):
        to_tone_marks(guess(chr(codepoint)), unsupported=unsupported)
    assert unsupported == []


# -- Sprint 6 M3 · #19: only hanzi contribute syllables --------------------


@pytest.mark.parametrize(
    "hanzi, numbered, marked",
    [
        ("T恤", "xu4", "xù"),
        ("3D打印", "da3yin4", "dǎyìn"),
        ("X光", "guang1", "guāng"),
        ("卡拉OK", "ka3la1", "kǎlā"),
        ("牛肉", "niu2rou4", "niúròu"),
    ],
)
def test_guess_skips_non_hanzi_segments(hanzi, numbered, marked):
    assert guess(hanzi) == numbered
    assert to_tone_marks(guess(hanzi)) == marked


def test_guess_keeps_word_context_within_a_run_of_hanzi():
    assert guess("银行") == "yin2hang2"


@pytest.mark.parametrize(
    "stored, marked", [("Txu4", "xù"), ("3Dda3yin4", "dǎyìn"), ("Xguang1", "guāng")]
)
def test_a_value_already_on_disk_renders_as_if_freshly_guessed(stored, marked):
    assert to_tone_marks(stored) == marked
