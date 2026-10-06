import os
import time
from pathlib import Path

import pytest

from vimdiomas.languages import ALPHABETICAL, CHARACTER_PHONETIC
from vimdiomas.store import (
    ContentIndex,
    TagCache,
    ensure_tree,
    fold,
    fuzzy,
    is_grammar,
    pinyin_key,
    search_content,
    tag_index,
    walk,
)

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "store_tree"


def test_walk_builds_directory_file_category_tree():
    tree = walk(FIXTURE_ROOT, kind=CHARACTER_PHONETIC)

    assert {d.path.name for d in tree.dirs} == {"Vocabulary", "Grammar"}

    vocab = next(d for d in tree.dirs if d.path.name == "Vocabulary")
    grammar = next(d for d in tree.dirs if d.path.name == "Grammar")

    food = next(f for f in vocab.files if f.path.name == "Food.md")
    assert food.categories == ["Vegetables", "Fruits"]
    assert food.has_uncategorized is True

    numbers = next(f for f in vocab.files if f.path.name == "Numbers.md")
    assert numbers.categories == []
    assert numbers.has_uncategorized is True

    directions = next(f for f in grammar.files if f.path.name == "Asking for directions.md")
    assert directions.categories == []
    assert directions.has_uncategorized is True


def test_tag_index_finds_file_by_multi_word_tag():
    cache = tag_index(FIXTURE_ROOT, kind=CHARACTER_PHONETIC)
    files = cache.files_for("C1 exam")
    assert {p.name for p in files} == {"Food.md", "Asking for directions.md"}


def test_tag_index_single_word_tag_across_files():
    cache = tag_index(FIXTURE_ROOT, kind=CHARACTER_PHONETIC)
    files = cache.files_for("travel")
    assert {p.name for p in files} == {"Food.md", "Numbers.md", "Asking for directions.md"}


def test_tag_index_reuses_cache_for_unchanged_files(tmp_path, monkeypatch):
    (tmp_path / "One.md").write_text("# One\n\nA\tpi1\ta\n\n## Tags\n\n#x\n", encoding="utf-8")

    parse_calls = []
    import vimdiomas.store as store_module

    original_parse = store_module.parse

    def counting_parse(text, stem, **kwargs):
        parse_calls.append(stem)
        return original_parse(text, stem, **kwargs)

    monkeypatch.setattr(store_module, "parse", counting_parse)

    cache = tag_index(tmp_path, kind=CHARACTER_PHONETIC)
    assert parse_calls == ["One"]

    cache = tag_index(tmp_path, cache, kind=CHARACTER_PHONETIC)
    assert parse_calls == ["One"]  # no re-parse: mtime unchanged


def test_tag_index_updates_after_mtime_change(tmp_path):
    path = tmp_path / "One.md"
    path.write_text("# One\n\nA\tpi1\ta\n\n## Tags\n\n#x\n", encoding="utf-8")

    cache = tag_index(tmp_path, kind=CHARACTER_PHONETIC)
    assert cache.files_for("x") == {path}
    assert cache.files_for("y") == set()

    time.sleep(0.01)
    path.write_text("# One\n\nA\tpi1\ta\n\n## Tags\n\n#y\n", encoding="utf-8")
    new_mtime = time.time() + 1
    os.utime(path, (new_mtime, new_mtime))

    cache = tag_index(tmp_path, cache, kind=CHARACTER_PHONETIC)
    assert cache.files_for("x") == set()
    assert cache.files_for("y") == {path}


def test_fuzzy_ranks_food_above_fried_noodles():
    assert fuzzy("fd", ["Fried noodles", "Food"]) == ["Food", "Fried noodles"]
    assert fuzzy("fd", ["Food", "Fried noodles"]) == ["Food", "Fried noodles"]


def test_fuzzy_drops_non_matches():
    assert fuzzy("xyz", ["Food", "Fried noodles"]) == []


def test_is_grammar_top_level_folder_any_case():
    root = Path("/tree")
    assert is_grammar(root / "Grammar" / "x.md", root) is True
    assert is_grammar(root / "grammar" / "x.md", root) is True
    assert is_grammar(root / "GRAMMAR" / "sub" / "x.md", root) is True


def test_is_grammar_false_for_vocabulary_and_edge_cases():
    root = Path("/tree")
    assert is_grammar(root / "Vocabulary" / "x.md", root) is False
    assert is_grammar(root / "Vocabulary" / "Grammar" / "x.md", root) is False
    assert is_grammar(root / "Grammar.md", root) is False
    assert is_grammar(Path("/other") / "Grammar" / "x.md", root) is False


def test_fuzzy_word_start_bonus():
    # "o" starts a word in "Ox" but sits mid-word in "Toy" - isolates the
    # word-start bonus since a single-character query has no gap penalty.
    assert fuzzy("o", ["Toy", "Ox"]) == ["Ox", "Toy"]


# -- Sprint 6 M1 · #2/#3: one bad line can't lock the whole tree -----------


def test_walk_survives_every_bad_line_in_the_data_integrity_tier(tmp_path):
    """Both tree screens parse every file to build themselves, so a row the
    parser choked on locked the user out of the entire tree — not just the
    one file. Every bad input this milestone covers has to come back as a
    tree, not an exception."""
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "EmptyField.md").write_text("# EmptyField\n\n你\tni3\t\n", encoding="utf-8")
    (vocab / "BadTags.md").write_text(
        "# BadTags\n\n## Food\n\n米\tmi3\trice\n\n## Tags\n\n#don't\n", encoding="utf-8"
    )
    (vocab / "Good.md").write_text("# Good\n\n字\tzi4\tcharacter\n", encoding="utf-8")

    tree = walk(tmp_path, kind=CHARACTER_PHONETIC)

    vocab_node = next(d for d in tree.dirs if d.path.name == "Vocabulary")
    assert sorted(f.path.stem for f in vocab_node.files) == ["BadTags", "EmptyField", "Good"]
    empty_field = next(f for f in vocab_node.files if f.path.stem == "EmptyField")
    assert empty_field.has_uncategorized is True
    bad_tags = next(f for f in vocab_node.files if f.path.stem == "BadTags")
    assert bad_tags.categories == ["Food"]


# -- Sprint 6 M2 · #14: a name prompt cannot write outside the tree --------


@pytest.mark.parametrize("name", ["Food", "Asking for directions", "[b]x", "Café", "a.b", "..x"])
def test_validate_name_accepts_ordinary_names(name):
    from vimdiomas.store import validate_name

    assert validate_name(name) is None


@pytest.mark.parametrize(
    "name", ["", "  ", " x", "x ", "a/b", "a\\b", ".", "..", "../x", "a\x00b", "a\tb", "a\x7fb"]
)
def test_validate_name_refuses_what_is_not_a_plain_child(name):
    from vimdiomas.store import validate_name

    message = validate_name(name)
    assert isinstance(message, str) and message


def test_walk_of_a_german_tree_sees_uncategorized_two_column_rows(tmp_path):
    """`has_uncategorized` depends on rows being recognised, so `walk` needs
    the kind for a correct answer (Sprint 6 M6)."""
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Loose.md").write_text("# Loose\n\nHaus\thouse\n", encoding="utf-8")

    german = walk(tmp_path, kind=ALPHABETICAL)
    chinese = walk(tmp_path, kind=CHARACTER_PHONETIC)

    assert german.dirs[0].files[0].has_uncategorized is True
    assert chinese.dirs[0].files[0].has_uncategorized is False


# -- Sprint 6 M6: a notebook's folders are created ---------------------------


def test_ensure_tree_creates_the_tree_and_both_folders(tmp_path):
    root = tmp_path / "tree-German"
    ensure_tree(root)
    assert sorted(p.name for p in root.iterdir()) == ["Grammar", "Vocabulary"]


def test_ensure_tree_completes_a_tree_without_touching_what_is_there(tmp_path):
    (tmp_path / "Vocabulary").mkdir()
    (tmp_path / "Vocabulary" / "Essen.md").write_text("# Essen\n", encoding="utf-8")
    (tmp_path / "Other").mkdir()

    ensure_tree(tmp_path)

    assert (tmp_path / "Grammar").is_dir()
    assert (tmp_path / "Vocabulary" / "Essen.md").read_text(encoding="utf-8") == "# Essen\n"
    assert (tmp_path / "Other").is_dir()
    assert not any(tmp_path.glob("**/*.tmp"))


def test_ensure_tree_treats_a_folder_of_any_case_as_present(tmp_path):
    (tmp_path / "grammar").mkdir()
    (tmp_path / "VOCABULARY").mkdir()
    ensure_tree(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["VOCABULARY", "grammar"]


def test_ensure_tree_is_idempotent(tmp_path):
    ensure_tree(tmp_path)
    ensure_tree(tmp_path)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["Grammar", "Vocabulary"]


# -- Sprint 6 M9: a file's warnings travel on its tree node -----------------


def _file(tree, dirname, stem):
    node = next(d for d in tree.dirs if d.path.name == dirname)
    return next(f for f in node.files if f.path.stem == stem)


def test_a_grammar_file_is_walked_as_a_grammar_file(tmp_path):
    """`walk` parses with `grammar=` for a file under `Grammar/` (Sprint 6
    M9). Without it every `### ` subtitle line is an "unrecognized line" —
    which was invisible only while these warnings were discarded."""
    grammar = tmp_path / "Grammar"
    grammar.mkdir()
    (grammar / "Cases.md").write_text(
        "# Cases\n\n## Dative\n\n### After mit\n\n我\two3\tme\n", encoding="utf-8"
    )
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Same.md").write_text(
        "# Same\n\n## Dative\n\n### After mit\n\n我\two3\tme\n", encoding="utf-8"
    )

    tree = walk(tmp_path, kind=CHARACTER_PHONETIC)

    assert _file(tree, "Grammar", "Cases").warnings == []
    # The same line in a vocabulary file has no subtitle level to be.
    assert [w.message for w in _file(tree, "Vocabulary", "Same").warnings] == [
        "unrecognized line"
    ]


def test_the_real_fixture_tree_walks_without_warnings():
    """The fixtures are files the app could have written, so nothing in them
    is reported — the guard against a check that cries wolf."""
    tree = walk(FIXTURE_ROOT, kind=CHARACTER_PHONETIC)

    def _all(node):
        for file_node in node.files:
            yield file_node
        for child in node.dirs:
            yield from _all(child)

    warned = {
        f.path.stem: [w.message for w in f.warnings] for f in _all(tree) if f.warnings
    }
    assert warned == {}


def test_a_warned_file_is_still_a_node_with_its_categories(tmp_path):
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Food.md").write_text(
        "# Food\n\n## Fruits\n\n苹果\tping2guo3\tapple\n\n| a | b |\n", encoding="utf-8"
    )

    node = _file(walk(tmp_path, kind=CHARACTER_PHONETIC), "Vocabulary", "Food")

    assert node.categories == ["Fruits"]
    assert [w.line_number for w in node.warnings] == [7]


def test_a_file_that_cannot_be_decoded_is_still_in_the_tree(tmp_path):
    """M1's rule: one bad file never locks the user out of the whole tree."""
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Bad.md").write_bytes(b"\xff\xfe\x00not utf-8")
    (vocab / "Good.md").write_text("# Good\n\n字\tzi4\tcharacter\n", encoding="utf-8")

    tree = walk(tmp_path, kind=CHARACTER_PHONETIC)

    assert sorted(f.path.stem for f in tree.dirs[0].files) == ["Bad", "Good"]
    bad = _file(tree, "Vocabulary", "Bad")
    assert bad.warnings[0].line_number == 0
    assert "could not be read" in bad.warnings[0].message
    assert _file(tree, "Vocabulary", "Good").warnings == []


# -- M3 · Search by content: fold() / pinyin_key() --------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Über", "uber"),
        ("Straße", "strasse"),
        ("nǐ hǎo", "ni hao"),
        ("ESSEN", "essen"),
        ("café", "cafe"),
        ("番茄", "番茄"),
        ("[b]x", "[b]x"),
    ],
)
def test_fold(text, expected):
    assert fold(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("ni3hao3", "nihao"),
        ("nǐ hǎo", "nihao"),
        ("NI3", "ni"),
        ("lu:4", "lu"),
        ("lv4", "lu"),
        ("Xi'an", "xian"),
        ("3", ""),
    ],
)
def test_pinyin_key(text, expected):
    assert pinyin_key(text) == expected


# -- M3 · Search by content: search_content() / ContentIndex ----------------


def _chinese_tree(root: Path) -> Path:
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Saludos.md").write_text(
        "# Saludos\n\n"
        "你\tni3\tyou\n\n"
        "## Saludos\n\n"
        "你好\tni3hao3\thola\n"
        "番茄\tfan1qie2\ttomate\n\n"
        "## Tags\n\n#greeting\n",
        encoding="utf-8",
    )
    grammar = root / "Grammar"
    grammar.mkdir(parents=True)
    (grammar / "Conjunctions.md").write_text(
        "# Conjunctions\n\n"
        "## Linking words\n\n"
        "### copulative conjunction\n\n"
        "和\the2\tand\n",
        encoding="utf-8",
    )
    return root


def _german_tree(root: Path) -> Path:
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Essen.md").write_text(
        "# Essen\n\n"
        "Über\tabout\n\n"
        "## Essen\n\n"
        "Haus\thouse\n",
        encoding="utf-8",
    )
    return root


def _search(root, query, *, kind, tagged=None):
    index = ContentIndex()
    index.refresh(root, kind=kind)
    return search_content(index, query, tree_root=root, kind=kind, tagged=tagged)


def test_search_content_hanzi_finds_only_that_entry(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "你好", kind=CHARACTER_PHONETIC)
    assert [h.word for h in hits] == ["你好"]


def test_search_content_partial_hanzi(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "番", kind=CHARACTER_PHONETIC)
    assert [h.word for h in hits] == ["番茄"]


@pytest.mark.parametrize(
    "query", ["ni", "ni3", "nǐ", "NI", "nihao", "ni hao", "ni3hao3", "nǐhǎo"]
)
def test_search_content_pinyin_variants_find_the_reading(tmp_path, query):
    hits = _search(_chinese_tree(tmp_path), query, kind=CHARACTER_PHONETIC)
    assert any(h.word == "你好" for h in hits)


def test_search_content_translation_finds_entry(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "hola", kind=CHARACTER_PHONETIC)
    assert [h.word for h in hits] == ["你好"]


def test_search_content_category_name(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "salu", kind=CHARACTER_PHONETIC)
    assert [(h.kind, h.name) for h in hits] == [("category", "Saludos")]


def test_search_content_subtitle_name(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "copulative", kind=CHARACTER_PHONETIC)
    assert [(h.kind, h.name) for h in hits] == [("subtitle", "copulative conjunction")]


def test_search_content_bare_digit_finds_no_reading(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "3", kind=CHARACTER_PHONETIC)
    assert hits == []


def test_search_content_note_only_is_not_a_hit(tmp_path):
    root = tmp_path
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Notes.md").write_text(
        "# Notes\n\n字\tzi4\tcharacter\n    *a secret note*\n", encoding="utf-8"
    )
    hits = _search(root, "secret", kind=CHARACTER_PHONETIC)
    assert hits == []


def test_search_content_tag_only_is_not_a_hit(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "greeting", kind=CHARACTER_PHONETIC)
    assert hits == []


def test_search_content_whitespace_query_returns_no_hits(tmp_path):
    hits = _search(_chinese_tree(tmp_path), "   ", kind=CHARACTER_PHONETIC)
    assert hits == []


def test_search_content_entry_matching_two_fields_appears_once(tmp_path):
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir(parents=True)
    # "echo" the query word deliberately into both word and translation.
    (vocab / "Both.md").write_text("# Both\n\necho\tni3\techo\n", encoding="utf-8")
    hits = _search(tmp_path, "echo", kind=CHARACTER_PHONETIC)
    assert len(hits) == 1


def test_search_content_order_is_tree_order(tmp_path):
    root = _chinese_tree(tmp_path)
    hits = _search(root, "e", kind=CHARACTER_PHONETIC)
    # Grammar/ sorts before Vocabulary/, so the subtitle's "and" entry (which
    # the query "e" matches via its pinyin "he2") must come first, followed
    # by whatever "e" matches in Vocabulary/Saludos.md.
    assert hits[0].source == root / "Grammar" / "Conjunctions.md"


def test_search_content_tagged_limits_to_those_files(tmp_path):
    root = _chinese_tree(tmp_path)
    tagged = {root / "Vocabulary" / "Saludos.md"}
    hits = _search(root, "he2", kind=CHARACTER_PHONETIC, tagged=tagged)
    assert hits == []

    tagged = {root / "Grammar" / "Conjunctions.md"}
    hits = _search(root, "he2", kind=CHARACTER_PHONETIC, tagged=tagged)
    assert any(h.word == "和" for h in hits)


def test_search_content_german_word_and_translation(tmp_path):
    root = _german_tree(tmp_path)
    for query in ("uber", "über", "about"):
        hits = _search(root, query, kind=ALPHABETICAL)
        assert [h.word for h in hits] == ["Über"], query


def test_search_content_german_category(tmp_path):
    hits = _search(_german_tree(tmp_path), "essen", kind=ALPHABETICAL)
    assert [(h.kind, h.name) for h in hits] == [("category", "Essen")]


def test_content_index_reparses_only_changed_mtime(tmp_path, monkeypatch):
    root = _chinese_tree(tmp_path)
    import vimdiomas.store as store_module

    original_parse = store_module.parse
    parse_calls = []

    def counting_parse(text, stem, **kwargs):
        parse_calls.append(stem)
        return original_parse(text, stem, **kwargs)

    monkeypatch.setattr(store_module, "parse", counting_parse)

    index = ContentIndex()
    index.refresh(root, kind=CHARACTER_PHONETIC)
    assert sorted(parse_calls) == ["Conjunctions", "Saludos"]

    parse_calls.clear()
    index.refresh(root, kind=CHARACTER_PHONETIC)
    assert parse_calls == []


def test_content_index_drops_a_deleted_file(tmp_path):
    root = _chinese_tree(tmp_path)
    index = ContentIndex()
    index.refresh(root, kind=CHARACTER_PHONETIC)
    assert len(index.entries) == 2

    (root / "Grammar" / "Conjunctions.md").unlink()
    index.refresh(root, kind=CHARACTER_PHONETIC)
    assert {p.stem for p in index.entries} == {"Saludos"}


def test_content_index_skips_an_unreadable_file(tmp_path):
    root = tmp_path
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Bad.md").write_bytes(b"\xff\xfe\x00not utf-8")
    (vocab / "Good.md").write_text("# Good\n\n字\tzi4\tcharacter\n", encoding="utf-8")

    index = ContentIndex()
    index.refresh(root, kind=CHARACTER_PHONETIC)
    assert {p.stem for p in index.entries} == {"Good"}
