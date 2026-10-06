from pathlib import Path

import pytest

from vimdiomas.languages import ALPHABETICAL, CHARACTER_PHONETIC
from vimdiomas.models import Deck, Entry
from vimdiomas.parser import _split_tags_line, parse
from vimdiomas.writer import _render_tag, save, write

FIXTURES = Path(__file__).parent / "fixtures"

ROUND_TRIP_FIXTURES = [
    ("Food.md", "Food"),
    ("Drinks.md", "Drinks"),
    ("Numbers.md", "Numbers"),
    ("Mixed.md", "Mixed"),
]


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("filename,stem", ROUND_TRIP_FIXTURES)
def test_round_trip_property(filename, stem):
    text = _load(filename)
    deck, _ = parse(text, stem, kind=CHARACTER_PHONETIC)
    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, _ = parse(rewritten, stem, kind=CHARACTER_PHONETIC)
    assert deck_again == deck


def test_noop_rewrite_is_byte_identical():
    text = _load("Food.md")
    deck, _ = parse(text, "Food", kind=CHARACTER_PHONETIC)
    assert write(deck, kind=CHARACTER_PHONETIC) == text


def test_tags_omitted_when_empty():
    deck, _ = parse(_load("Drinks.md"), "Drinks", kind=CHARACTER_PHONETIC)
    assert "## Tags" not in write(deck, kind=CHARACTER_PHONETIC)


def test_category_with_no_entries_round_trips_unchanged():
    text = "# Empty\n\n## New Category\n"
    deck, _ = parse(text, "Empty", kind=CHARACTER_PHONETIC)
    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, _ = parse(rewritten, "Empty", kind=CHARACTER_PHONETIC)
    assert deck_again == deck
    assert deck_again.categories[0].entries == []


# -- grammar mode (Sprint 5 M5) ------------------------------------------


def test_grammar_round_trip_property():
    text = _load("Grammar.md")
    deck, _ = parse(text, "Grammar", kind=CHARACTER_PHONETIC, grammar=True)
    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, _ = parse(rewritten, "Grammar", kind=CHARACTER_PHONETIC, grammar=True)
    assert deck_again == deck


def test_grammar_noop_rewrite_is_byte_identical():
    text = _load("Grammar.md")
    deck, _ = parse(text, "Grammar", kind=CHARACTER_PHONETIC, grammar=True)
    assert write(deck, kind=CHARACTER_PHONETIC) == text


def test_grammar_deck_with_no_subtitles_round_trips():
    text = _load("Clasificadores.md")
    deck, _ = parse(text, "Clasificadores", kind=CHARACTER_PHONETIC, grammar=True)
    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, _ = parse(rewritten, "Clasificadores", kind=CHARACTER_PHONETIC, grammar=True)
    assert deck_again == deck
    assert all(category.subtitles == [] for category in deck.categories)


def test_subtitle_with_no_entries_round_trips():
    text = "# G\n\n## Cat\n\n你好\tni3hao3\thello\n\n### Empty Sub\n\n"
    deck, _ = parse(text, "G", kind=CHARACTER_PHONETIC, grammar=True)
    assert deck.categories[0].subtitles[0].entries == []
    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, _ = parse(rewritten, "G", kind=CHARACTER_PHONETIC, grammar=True)
    assert deck_again == deck


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    deck, _ = parse(_load("Food.md"), "Food", kind=CHARACTER_PHONETIC)
    target = tmp_path / "Food.md"
    save(deck, target, kind=CHARACTER_PHONETIC)
    assert target.read_text(encoding="utf-8") == write(deck, kind=CHARACTER_PHONETIC)
    leftover = [p for p in tmp_path.iterdir() if p != target]
    assert leftover == []


# -- Sprint 6 M1 · #3: tags survive a write -------------------------------

TAG_CORPUS = [
    "food",
    "travel",
    "C1 exam",
    "don't",
    '"quoted"',
    "a b",
    "back\\slash",
    "a'b\"c",
    'a\\"b',
    "a\tb",
    "it's a test",
    'say "hi" now',
    "trailing\\",
    "多音字",
]


@pytest.mark.parametrize("tag", TAG_CORPUS)
def test_rendered_tag_parses_back_to_itself(tag):
    """The property, not the exact output: a tag has to come back off the
    line `_render_tag` wrote it on, whichever of the three forms that is."""
    tokens = _split_tags_line(_render_tag(tag))
    assert tokens is not None
    assert [token.lstrip("#") for token in tokens] == [tag]
    # Every token the writer emits is a `#tag`; one without the `#` is what
    # M9 reports as "not a tag".
    assert all(token.startswith("#") for token in tokens)


def test_apostrophe_tag_round_trips_through_a_whole_file():
    """The report's #3 reproduction: `#"don't"` parsed, then rewrote to
    `#don't`, which `shlex.split` could no longer read — so adding an
    unrelated entry corrupted the file's whole tag block."""
    text = '# X\n\n你\tni3\tyou\n\n## Tags\n\n#"don\'t" #food\n'
    deck, warnings = parse(text, "X", kind=CHARACTER_PHONETIC)
    assert warnings == []
    assert deck.tags == ["don't", "food"]

    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, warnings_again = parse(rewritten, "X", kind=CHARACTER_PHONETIC)
    assert warnings_again == []
    assert deck_again == deck


@pytest.mark.parametrize("tag,expected", [("food", "#food"), ("C1 exam", '#"C1 exam"')])
def test_tags_already_in_the_tree_are_written_byte_identically(tag, expected):
    """A correctness fix that reformatted the tag block of every existing
    file would be a worse outcome than the bug, so the two forms this
    function already emitted are frozen."""
    assert _render_tag(tag) == expected


def test_tags_fixture_round_trips_byte_identically():
    text = _load("Food.md")
    deck, _ = parse(text, "Food", kind=CHARACTER_PHONETIC)
    assert "#food #travel #\"C1 exam\"" in write(deck, kind=CHARACTER_PHONETIC)


# -- Sprint 6 M1 · #15: the writer refuses a column-shifting field --------


@pytest.mark.parametrize("field", ["word", "reading", "translation"])
@pytest.mark.parametrize("char", ["\t", "\n", "\r"])
def test_writing_a_field_containing_a_tab_or_newline_raises(field, char):
    entry = Entry(word="苹果", reading="ping2guo3", translation="apple")
    setattr(entry, field, f"a{char}b")
    with pytest.raises(ValueError, match=field):
        write(Deck(title="X", uncategorized=[entry]), kind=CHARACTER_PHONETIC)


def test_writing_an_extra_field_containing_a_tab_raises():
    entry = Entry(word="苹果", reading="ping2guo3", translation="apple", extra_fields=["a\tb"])
    with pytest.raises(ValueError, match=r"extra_fields\[0\]"):
        write(Deck(title="X", uncategorized=[entry]), kind=CHARACTER_PHONETIC)


def test_writing_a_note_containing_a_newline_raises():
    entry = Entry(word="苹果", reading="ping2guo3", translation="apple", note="a\nb")
    with pytest.raises(ValueError, match="note"):
        write(Deck(title="X", uncategorized=[entry]), kind=CHARACTER_PHONETIC)


def test_a_note_may_contain_a_tab():
    """A note is written on its own line, so a tab in it shifts no columns."""
    entry = Entry(word="苹果", reading="ping2guo3", translation="apple", note="a\tb")
    assert "*a\tb*" in write(Deck(title="X", uncategorized=[entry]), kind=CHARACTER_PHONETIC)


# -- Sprint 6 M1 · #2: an empty field survives a round trip ---------------


@pytest.mark.parametrize(
    "fields,expected_warnings",
    [
        (("你", "ni3", ""), []),
        (("你", "", ""), []),
        (("你", "ni3", "you"), []),
        # A word is the one field Entry requires, so this deck is not one the
        # app can hold: it round-trips, and M9 reports the row.
        (("", "ni3", "you"), ["an entry with no word"]),
    ],
)
def test_entry_with_an_empty_field_round_trips(fields, expected_warnings):
    word, reading, translation = fields
    deck = Deck(title="X", uncategorized=[Entry(word=word, reading=reading, translation=translation)])
    deck_again, warnings = parse(write(deck, kind=CHARACTER_PHONETIC), "X", kind=CHARACTER_PHONETIC)
    assert [w.message for w in warnings] == expected_warnings
    assert deck_again == deck


# -- Sprint 6 M6: an alphabetical row is `word<TAB>translation` -------------

GERMAN_FIXTURES = [("german/Essen.md", "Essen", False), ("german/Grammar/Konjunktionen.md", "Konjunktionen", True)]


@pytest.mark.parametrize("filename,stem,grammar", GERMAN_FIXTURES)
def test_german_fixtures_rewrite_byte_identically(filename, stem, grammar):
    text = _load(filename)
    deck, warnings = parse(text, stem, kind=ALPHABETICAL, grammar=grammar)
    assert warnings == []
    assert write(deck, kind=ALPHABETICAL) == text


@pytest.mark.parametrize("filename,stem,grammar", GERMAN_FIXTURES)
def test_german_round_trip_property(filename, stem, grammar):
    deck, _ = parse(_load(filename), stem, kind=ALPHABETICAL, grammar=grammar)
    again, _ = parse(write(deck, kind=ALPHABETICAL), stem, kind=ALPHABETICAL, grammar=grammar)
    assert again == deck


def test_alphabetical_writer_emits_two_columns():
    deck = Deck(title="X", uncategorized=[Entry(word="Haus", reading="", translation="house")])
    assert write(deck, kind=ALPHABETICAL) == "# X\n\nHaus\thouse\n"


def test_alphabetical_entry_with_an_empty_translation_round_trips():
    deck = Deck(title="X", uncategorized=[Entry(word="Haus", reading="", translation="")])
    again, warnings = parse(write(deck, kind=ALPHABETICAL), "X", kind=ALPHABETICAL)
    assert warnings == []
    assert again == deck


def test_alphabetical_writer_refuses_an_entry_with_a_reading():
    deck = Deck(title="X", uncategorized=[Entry(word="Haus", reading="hau", translation="house")])
    with pytest.raises(ValueError, match="Haus"):
        write(deck, kind=ALPHABETICAL)


def test_alphabetical_writer_still_refuses_a_tab_in_a_field():
    deck = Deck(title="X", uncategorized=[Entry(word="Ha\tus", reading="", translation="house")])
    with pytest.raises(ValueError, match="tab|\\\\t"):
        write(deck, kind=ALPHABETICAL)


def test_alphabetical_save_writes_the_two_column_file(tmp_path):
    deck, _ = parse(_load("german/Essen.md"), "Essen", kind=ALPHABETICAL)
    target = tmp_path / "Essen.md"
    save(deck, target, kind=ALPHABETICAL)
    assert target.read_text(encoding="utf-8") == _load("german/Essen.md")


# -- Sprint 6 M9 · changes inside the format round-trip ---------------------
#
# A hand change that respects the format is read back as written and says
# nothing: the deck is what the file says, which is why the app needs no
# differ to pick one up (requirements.md §3). Trivial or non-trivial is about
# what the TUI shows, not about how the file parses.

TRIVIAL = [
    (
        "a translation edited",
        "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tcow meat\n",
    ),
    (
        "an entry moved to another category",
        "# Food\n\n## Meat\n\n## Fruits\n\n牛肉\tniu2rou4\tbeef\n",
    ),
    (
        "entries reordered inside a category",
        "# Food\n\n## Meat\n\n羊肉\tyang2rou4\tlamb\n牛肉\tniu2rou4\tbeef\n",
    ),
    (
        "categories reordered",
        "# Food\n\n## Fruits\n\n苹果\tping2guo3\tapple\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n",
    ),
    (
        "a note added",
        "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n    *from a cow*\n",
    ),
    (
        "a tag added",
        "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n\n## Tags\n\n#food #protein\n",
    ),
]

NON_TRIVIAL = [
    ("a category renamed", "# Food\n\n## Protein\n\n牛肉\tniu2rou4\tbeef\n"),
    (
        "a category added",
        "# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n\n## Snacks\n\n薯片\tshu3pian4\tchips\n",
    ),
    ("a category removed", "# Food\n\n牛肉\tniu2rou4\tbeef\n"),
    ("an uncategorized block appearing", "# Food\n\n字\tzi4\tchar\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n"),
]


@pytest.mark.parametrize(
    "text",
    [case[1] for case in TRIVIAL + NON_TRIVIAL],
    ids=[case[0] for case in TRIVIAL + NON_TRIVIAL],
)
def test_a_change_inside_the_format_round_trips_silently(text):
    deck, warnings = parse(text, "Food", kind=CHARACTER_PHONETIC)
    assert warnings == []
    # The deck survives a rewrite, so everything the hand edit says is
    # something the app holds and writes back. The text itself may be tidied
    # — an empty category gains a blank line — which is the lossless half of
    # §2 and deliberately not a warning.
    rewritten = write(deck, kind=CHARACTER_PHONETIC)
    deck_again, warnings_again = parse(rewritten, "Food", kind=CHARACTER_PHONETIC)
    assert deck_again == deck
    assert warnings_again == []


@pytest.mark.parametrize(
    "text", [case[1] for case in NON_TRIVIAL], ids=[case[0] for case in NON_TRIVIAL]
)
def test_a_non_trivial_change_is_what_the_tui_reads(text):
    """What the TUI shows of a file is its category names and whether it has
    uncategorized entries — the two things a non-trivial change moves."""
    deck, _ = parse(text, "Food", kind=CHARACTER_PHONETIC)
    shape = ([c.name for c in deck.categories], bool(deck.uncategorized))
    before, _ = parse("# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n", "Food", kind=CHARACTER_PHONETIC)
    assert shape != ([c.name for c in before.categories], bool(before.uncategorized))
