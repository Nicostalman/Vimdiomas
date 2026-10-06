from pathlib import Path

import pytest

from vimdiomas.languages import ALPHABETICAL, CHARACTER_PHONETIC
from vimdiomas.parser import parse

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_note_attaches_to_preceding_entry():
    deck, warnings = parse(_load("Food.md"), "Food", kind=CHARACTER_PHONETIC)
    tomato = deck.categories[0].entries[0]
    assert tomato.word == "番茄"
    assert tomato.note == "sometimes called 西红柿 in the north"
    carrot = deck.categories[0].entries[1]
    assert carrot.note is None
    assert warnings == []


def test_tags_parsed_including_multiword():
    deck, _ = parse(_load("Food.md"), "Food", kind=CHARACTER_PHONETIC)
    assert deck.tags == ["food", "travel", "C1 exam"]


def test_no_tags_section_leaves_tags_empty():
    deck, warnings = parse(_load("Drinks.md"), "Drinks", kind=CHARACTER_PHONETIC)
    assert deck.tags == []
    assert warnings == []
    assert [c.name for c in deck.categories] == ["Hot", "Cold"]


def test_no_categories_all_entries_uncategorized():
    deck, warnings = parse(_load("Numbers.md"), "Numbers", kind=CHARACTER_PHONETIC)
    assert deck.categories == []
    assert [e.word for e in deck.uncategorized] == ["一", "二"]
    assert warnings == []


def test_uncategorized_entries_before_first_category():
    deck, warnings = parse(_load("Mixed.md"), "Mixed", kind=CHARACTER_PHONETIC)
    assert [e.word for e in deck.uncategorized] == ["你好"]
    assert deck.categories[0].name == "Colors"
    assert warnings == []


def test_mismatched_header_filename_wins():
    deck, warnings = parse(_load("Mismatched.md"), "Mismatched", kind=CHARACTER_PHONETIC)
    assert deck.title == "Mismatched"
    assert len(warnings) == 1
    assert "Wrong Title" in warnings[0].message


def test_stray_line_produces_warning_and_is_preserved():
    deck, warnings = parse(_load("Stray.md"), "Stray", kind=CHARACTER_PHONETIC)
    assert [e.word for e in deck.uncategorized] == ["狗", "鸟"]
    assert len(warnings) == 1
    assert warnings[0].raw_line == "this line is not valid and should not be dropped"


def test_category_with_no_entries_parses_empty():
    deck, warnings = parse("# Empty\n\n## New Category\n", "Empty", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert len(deck.categories) == 1
    assert deck.categories[0].name == "New Category"
    assert deck.categories[0].entries == []


# -- grammar mode (Sprint 5 M5) ------------------------------------------


def test_grammar_fixture_parses_subtitles():
    deck, warnings = parse(_load("Grammar.md"), "Grammar", kind=CHARACTER_PHONETIC, grammar=True)
    assert warnings == []

    conjunctions = deck.categories[0]
    assert conjunctions.name == "Conjunctions"
    assert [e.word for e in conjunctions.entries] == ["..."]

    copulative, disjunctive = conjunctions.subtitles
    assert copulative.name == "copulative conjunction"
    assert [e.word for e in copulative.entries] == ["和", "也"]
    assert copulative.entries[0].note == "also 跟 in speech"
    assert disjunctive.name == "disjunctive conjunction"
    assert disjunctive.entries == []

    plain = deck.categories[1]
    assert plain.name == "Plain category"
    assert plain.subtitles == []


def test_grammar_fixture_without_flag_treats_subtitles_as_stray_lines():
    deck, warnings = parse(_load("Grammar.md"), "Grammar", kind=CHARACTER_PHONETIC, grammar=False)
    conjunctions = deck.categories[0]
    assert conjunctions.subtitles == []
    # Every entry that was under a subtitle stays in the category instead.
    assert [e.word for e in conjunctions.entries] == ["...", "和", "也"]
    stray_messages = [w.message for w in warnings]
    assert stray_messages.count("unrecognized line") == 2  # the two "### " lines


def test_subtitle_before_any_category_is_a_warning():
    deck, warnings = parse("# X\n\n### stray subtitle\n\n你好\tni3hao3\thello\n", "X", kind=CHARACTER_PHONETIC, grammar=True)
    assert deck.categories == []
    assert [e.word for e in deck.uncategorized] == ["你好"]
    assert len(warnings) == 1
    assert warnings[0].message == "unrecognized line"


def test_subtitle_inside_tags_section_is_a_warning():
    text = "# X\n\n## Tags\n\n### not a tag\n\n#real\n"
    deck, warnings = parse(text, "X", kind=CHARACTER_PHONETIC, grammar=True)
    assert deck.tags == ["real"]
    assert len(warnings) == 1
    assert warnings[0].message == "unrecognized line"


def test_real_grammar_files_parse_identically_with_flag_on_and_off():
    for filename, stem in [
        ("Asking for directions.md", "Asking for directions"),
        ("Clasificadores.md", "Clasificadores"),
    ]:
        text = _load(filename)
        deck_off, warnings_off = parse(text, stem, kind=CHARACTER_PHONETIC, grammar=False)
        deck_on, warnings_on = parse(text, stem, kind=CHARACTER_PHONETIC, grammar=True)
        assert deck_off == deck_on
        assert warnings_off == warnings_on == []


# -- Sprint 6 M1 · #2: a row with an empty boundary field -----------------


def test_entry_with_empty_translation_parses():
    """The bug report's own P1 reproduction: `strip()` treated the trailing
    tab as whitespace, so the empty third field vanished before `split` ran
    and unpacking raised `ValueError: not enough values to unpack`."""
    deck, warnings = parse("# X\n\n你\tni3\t\n", "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert [(e.word, e.reading, e.translation) for e in deck.uncategorized] == [("你", "ni3", "")]


def test_entry_with_empty_leading_field_parses():
    deck, warnings = parse("# X\n\n\tni3\tyou\n", "X", kind=CHARACTER_PHONETIC)
    assert [(e.word, e.reading, e.translation) for e in deck.uncategorized] == [("", "ni3", "you")]
    # It parses, which is M1's point. M9 reports it: Entry cannot write a row
    # with no word, and it renders a blank first column.
    assert [w.message for w in warnings] == ["an entry with no word"]


def test_entry_with_both_trailing_fields_empty_parses():
    deck, warnings = parse("# X\n\n你\t\t\n", "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert [(e.word, e.reading, e.translation) for e in deck.uncategorized] == [("你", "", "")]


def test_whitespace_only_translation_parses_as_empty():
    deck, warnings = parse("# X\n\n你\tni3\t   \n", "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert deck.uncategorized[0].translation == ""


def test_space_indented_entry_row_parses_unchanged():
    deck, warnings = parse("# X\n\n    你\tni3\tyou\n", "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert [(e.word, e.reading, e.translation) for e in deck.uncategorized] == [("你", "ni3", "you")]


def test_space_padded_fields_are_stripped_individually():
    """`strip()` used to clean only the two outer edges of the row; each field
    is stripped of spaces on its own now that the row itself is not (#2)."""
    deck, warnings = parse("# X\n\n  你 \t ni3 \t you  \n", "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert [(e.word, e.reading, e.translation) for e in deck.uncategorized] == [("你", "ni3", "you")]


def test_tab_indented_entry_row_reads_as_an_empty_first_field():
    """The one case where a leading tab is ambiguous: it is either indentation
    or an empty `hanzi`, and it cannot be both. Read as the empty field, which
    is what `writer.write` emits for one — a tab-indented triad is not
    something the writer produces, and it raised outright before this fix."""
    deck, warnings = parse("# X\n\n\t你\tni3\tyou\n", "X", kind=CHARACTER_PHONETIC)
    entry = deck.uncategorized[0]
    assert (entry.word, entry.reading, entry.translation) == ("", "你", "ni3")
    assert entry.extra_fields == ["you"]
    # The deck is M1's, unchanged. M9 reports it: the row has no word, and
    # `you` is on disk but never rendered.
    assert [w.message for w in warnings] == [
        "extra column(s) never rendered: you",
        "an entry with no word",
    ]


def test_extra_fields_beyond_three_still_collected():
    """Still collected — M9 warns about them without changing the deck."""
    deck, warnings = parse("# X\n\n你\tni3\tyou\tfourth\tfifth\n", "X", kind=CHARACTER_PHONETIC)
    assert deck.uncategorized[0].extra_fields == ["fourth", "fifth"]
    assert [w.message for w in warnings] == ["extra column(s) never rendered: fourth, fifth"]


def test_extra_fields_may_be_empty():
    deck, warnings = parse("# X\n\n你\tni3\tyou\t\n", "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert deck.uncategorized[0].extra_fields == [""]


# -- Sprint 6 M1 · #3: unparseable tag syntax is a warning, not a crash ----


def test_unclosed_quote_in_tags_line_warns_instead_of_raising():
    deck, warnings = parse('# X\n\n## Tags\n\n#don\'t #other\n', "X", kind=CHARACTER_PHONETIC)
    assert deck.tags == []
    assert [w.message for w in warnings] == ["unparseable tag syntax"]


def test_quoted_apostrophe_tag_parses():
    """The report's #3 reproduction, as it sits in the file."""
    deck, warnings = parse('# X\n\n## Tags\n\n#"don\'t"\n', "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert deck.tags == ["don't"]


# -- Sprint 6 M6: an alphabetical row is `word<TAB>translation` -------------


def test_alphabetical_vocabulary_parses_with_no_reading():
    deck, warnings = parse(_load("german/Essen.md"), "Essen", kind=ALPHABETICAL)
    assert warnings == []
    assert [(e.word, e.translation) for e in deck.uncategorized] == [("Haus", "house")]
    obst = deck.categories[0]
    assert obst.name == "Obst"
    assert [(e.word, e.translation, e.note) for e in obst.entries] == [
        ("der Apfel", "the apple", "masculine, nominative"),
        ("Birne", "pear", None),
    ]
    assert deck.tags == ["food", "german"]
    every_entry = deck.uncategorized + [e for c in deck.categories for e in c.entries]
    assert all(e.reading == "" for e in every_entry)


def test_alphabetical_row_with_an_empty_translation_is_a_row():
    deck, warnings = parse("# X\n\nHaus\t\n", "X", kind=ALPHABETICAL)
    assert warnings == []
    assert [(e.word, e.translation) for e in deck.uncategorized] == [("Haus", "")]


def test_alphabetical_line_with_no_tab_is_unrecognized():
    deck, warnings = parse("# X\n\nHaus house\n", "X", kind=ALPHABETICAL)
    assert deck.uncategorized == []
    assert [w.message for w in warnings] == ["unrecognized line"]


def test_alphabetical_extra_fields_follow_the_translation():
    deck, _ = parse("# X\n\nHaus\thouse\tn.\tdas\n", "X", kind=ALPHABETICAL)
    entry = deck.uncategorized[0]
    assert (entry.word, entry.translation, entry.extra_fields) == ("Haus", "house", ["n.", "das"])


def test_alphabetical_chinese_style_three_column_row_is_read_by_the_general_rule():
    """Not special-cased: read by the general rule, and M9 warns that the
    third column is on disk and absent from the PDF."""
    deck, warnings = parse("# X\n\nHaus\t\thouse\n", "X", kind=ALPHABETICAL)
    entry = deck.uncategorized[0]
    assert (entry.word, entry.translation, entry.extra_fields) == ("Haus", "", ["house"])
    assert [w.message for w in warnings] == ["extra column(s) never rendered: house"]


def test_alphabetical_tab_indented_note_is_a_note_not_a_one_tab_row():
    deck, warnings = parse("# X\n\nHaus\thouse\n\t*a note*\n", "X", kind=ALPHABETICAL)
    assert warnings == []
    assert len(deck.uncategorized) == 1
    assert deck.uncategorized[0].note == "a note"


def test_alphabetical_grammar_fixture_parses_subtitles():
    deck, warnings = parse(
        _load("german/Grammar/Konjunktionen.md"), "Konjunktionen", kind=ALPHABETICAL, grammar=True
    )
    assert warnings == []
    category = deck.categories[0]
    assert [s.name for s in category.subtitles] == ["Kausal", "Konzessiv"]
    assert [e.word for e in category.subtitles[0].entries][0] == "weil"
    assert category.subtitles[0].entries[0].note == "verb goes to the end of the clause"


def test_the_kind_decides_what_a_row_is():
    text = _load("german/Essen.md")
    chinese_deck, chinese_warnings = parse(text, "Essen", kind=CHARACTER_PHONETIC)
    assert chinese_deck.uncategorized == []
    assert all(c.entries == [] for c in chinese_deck.categories)
    assert chinese_warnings  # the two-column rows are unrecognized lines
    german_deck, _ = parse(text, "Essen", kind=ALPHABETICAL)
    assert len(german_deck.uncategorized) == 1
    assert len(german_deck.categories[0].entries) == 2


# -- Sprint 6 M9: every deviation from the autogenerated format -------------
#
# The format is `writer.write`'s, written down in the milestone's
# requirements.md §1. A deviation is *reported* when it is lossy — the text
# does not reach the PDF as itself, or is read back as something other than
# what it says — and silent when the next in-app write simply tidies it away
# (§2). The two parametrized tests below are those two tables.


REPORTED = [
    # (label, text, kind, grammar, expected messages)
    (
        "markdown table",
        "# Food\n\n## Fruits\n\n| word | gloss |\n| --- | --- |\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line", "unrecognized line"],
    ),
    (
        "a line of prose",
        "# Food\n\n## Fruits\n\nI should learn these.\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"],
    ),
    (
        "yaml front matter",
        "---\ntitle: Food\n---\n\n# Food\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"] * 3,
    ),
    (
        "a #### heading",
        "# Food\n\n#### Deep\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"],
    ),
    (
        "a ## heading with no name",
        "# Food\n\n## \n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"],
    ),
    (
        "a ### line in a vocabulary file",
        "# Food\n\n## Fruits\n\n### Oops\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"],
    ),
    (
        "a stray note line",
        "# Food\n\n## Fruits\n\n    *orphan*\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"],
    ),
    (
        "a row with too few fields",
        "# Food\n\n## Fruits\n\n你好\n",
        CHARACTER_PHONETIC,
        False,
        ["unrecognized line"],
    ),
    (
        "a row with a non-empty extra field",
        "# Food\n\n## Fruits\n\n你\tni3\tyou\tjunk\n",
        CHARACTER_PHONETIC,
        False,
        ["extra column(s) never rendered: junk"],
    ),
    (
        "a German row with a third column",
        "# Essen\n\n## Obst\n\nApfel\tapple\tjunk\n",
        ALPHABETICAL,
        False,
        ["extra column(s) never rendered: junk"],
    ),
    (
        "a row with no word",
        "# Food\n\n## Fruits\n\n\tni3\tyou\n",
        CHARACTER_PHONETIC,
        False,
        ["an entry with no word"],
    ),
    (
        "prose in the tag block",
        "# Food\n\n## Tags\n\nthese are my notes\n",
        CHARACTER_PHONETIC,
        False,
        ["not a tag: these, are, my, notes"],
    ),
    (
        "an unquoted multi-word tag",
        '# Food\n\n## Tags\n\n#C1 exam\n',
        CHARACTER_PHONETIC,
        False,
        ["not a tag: exam"],
    ),
    (
        "a second tag block",
        "# Food\n\n## Tags\n\n#fruit\n\n## Tags\n\n你\tni3\tyou\n",
        CHARACTER_PHONETIC,
        False,
        ["the tag block appears more than once", "not a tag: 你, ni3, you"],
    ),
    (
        "unparseable tag quoting",
        "# Food\n\n## Tags\n\n#\"don't\n",
        CHARACTER_PHONETIC,
        False,
        ["unparseable tag syntax"],
    ),
    (
        "a header that is not the filename",
        "# Fruit\n\n## Fruits\n",
        CHARACTER_PHONETIC,
        False,
        ["header 'Fruit' does not match filename 'Food'"],
    ),
    (
        "no header at all",
        "## Fruits\n\n你\tni3\tyou\n",
        CHARACTER_PHONETIC,
        False,
        ["no '# Food' header line"],
    ),
    (
        "a duplicate category name",
        "# Food\n\n## Fruits\n\n## Fruits\n",
        CHARACTER_PHONETIC,
        False,
        ["category 'Fruits' appears more than once"],
    ),
    (
        "a duplicate subtitle name",
        "# Food\n\n## Fruits\n\n### Use\n\n### Use\n",
        CHARACTER_PHONETIC,
        True,
        ["subtitle 'Use' appears more than once"],
    ),
    (
        "a subtitle outside any category",
        "# Food\n\n### Use\n",
        CHARACTER_PHONETIC,
        True,
        ["unrecognized line"],
    ),
]


@pytest.mark.parametrize(
    "text,kind,grammar,expected",
    [case[1:] for case in REPORTED],
    ids=[case[0] for case in REPORTED],
)
def test_a_lossy_deviation_is_reported(text, kind, grammar, expected):
    _, warnings = parse(text, "Food" if kind is CHARACTER_PHONETIC else "Essen",
                        kind=kind, grammar=grammar)
    assert [w.message for w in warnings] == expected


@pytest.mark.parametrize(
    "text,kind,grammar",
    [case[1:4] for case in REPORTED],
    ids=[case[0] for case in REPORTED],
)
def test_a_reported_warning_carries_its_line_and_raw_text(text, kind, grammar):
    """Every warning can be shown as `line N: message` over the raw line. A
    file-level one (a missing header) has no line to blame: line 0, no raw
    line, and it is listed first."""
    lines = text.splitlines()
    _, warnings = parse(text, "Food" if kind is CHARACTER_PHONETIC else "Essen",
                        kind=kind, grammar=grammar)
    for warning in warnings:
        if warning.line_number == 0:
            assert warning.raw_line == ""
            assert warnings[0] is warning
        else:
            assert warning.raw_line == lines[warning.line_number - 1]


LOSSLESS = [
    ("blank-line runs", "# Food\n\n\n## Fruits\n\n\n你\tni3\tyou\n"),
    ("no trailing newline", "# Food\n\n## Fruits\n\n你\tni3\tyou"),
    ("a note indented two spaces", "# Food\n\n你\tni3\tyou\n  *a note*\n"),
    ("a note indented with a tab", "# Food\n\n你\tni3\tyou\n\t*a note*\n"),
    ("the tag block before the categories",
     "# Food\n\n## Tags\n\n#fruit\n\n## Fruits\n\n你\tni3\tyou\n"),
    ("an empty tag block", "# Food\n\n你\tni3\tyou\n\n## Tags\n"),
    ("a tag quoted where the writer would not", '# Food\n\n## Tags\n\n#"fruit"\n'),
    ("a header that matches but is not first", "## Fruits\n\n# Food\n\n你\tni3\tyou\n"),
    ("a trailing tab, so one empty extra field", "# Food\n\n你\tni3\tyou\t\n"),
    ("an empty translation", "# Food\n\n你\tni3\t\n"),
    ("an empty reading", "# Food\n\n你\t\tyou\n"),
    ("the same word twice", "# Food\n\n你\tni3\tyou\n你\tni3\tyou\n"),
]


@pytest.mark.parametrize("text", [case[1] for case in LOSSLESS], ids=[case[0] for case in LOSSLESS])
def test_a_lossless_deviation_is_silent(text):
    _, warnings = parse(text, "Food", kind=CHARACTER_PHONETIC)
    assert warnings == []


def test_the_checks_do_not_change_what_is_parsed():
    """Every M9 warning is additive: the deck, its tags and its extra fields
    are what they were before the checks existed (requirements.md, *Out of
    scope*). This is what keeps every existing PDF byte-identical."""
    text = (
        "## Fruits\n\n你\tni3\tyou\tjunk\n\tni3\tyou\n\n## Fruits\n\n"
        "## Tags\n\n#fruit prose\n\n## Tags\n\n#more\n"
    )
    deck, warnings = parse(text, "Food", kind=CHARACTER_PHONETIC)

    assert warnings  # all of the above is reported
    assert [c.name for c in deck.categories] == ["Fruits", "Fruits"]
    first, second = deck.categories[0].entries
    assert (first.word, first.reading, first.translation) == ("你", "ni3", "you")
    assert first.extra_fields == ["junk"]
    assert (second.word, second.reading, second.translation) == ("", "ni3", "you")
    assert deck.tags == ["fruit", "prose", "more"]
