from vimdiomas import platform
from vimdiomas.languages import (
    ALPHABETICAL,
    CHARACTER_PHONETIC,
    LANGUAGES,
    get_language,
    is_functional,
)


def test_chinese_is_character_phonetic_and_functional():
    chinese = get_language("Chinese")
    assert chinese.kind is CHARACTER_PHONETIC
    assert chinese.functional
    assert is_functional("Chinese")


def test_german_is_alphabetical_and_functional():
    german = get_language("German")
    assert german.kind is ALPHABETICAL
    assert german.functional
    assert is_functional("German")


def test_character_phonetic_has_a_reading_guessed_from_the_word():
    assert CHARACTER_PHONETIC.has_reading
    assert CHARACTER_PHONETIC.word_label == "Hanzi"
    assert CHARACTER_PHONETIC.reading_label == "Pinyin"
    assert CHARACTER_PHONETIC.guess_reading("你好") == "ni3hao3"


def test_alphabetical_has_no_reading():
    assert not ALPHABETICAL.has_reading
    assert ALPHABETICAL.word_label == "Word"
    assert ALPHABETICAL.reading_label is None
    assert ALPHABETICAL.guess_reading is None


def test_character_phonetic_uses_the_platform_cjk_font():
    assert CHARACTER_PHONETIC.cjk_font == platform.CJK_FONT_NAME


def test_an_unregistered_language_is_unknown_and_not_functional():
    assert get_language("Klingon") is None
    assert not is_functional("Klingon")


def test_registry_names_are_unique():
    names = [language.name for language in LANGUAGES]
    assert len(names) == len(set(names))


def test_registry_is_the_six_languages_in_the_order_they_are_offered():
    assert [language.name for language in LANGUAGES] == [
        "Chinese",
        "German",
        "Italian",
        "French",
        "English",
        "Spanish",
    ]


def test_every_language_but_chinese_is_alphabetical_and_all_are_functional():
    for language in LANGUAGES:
        expected = CHARACTER_PHONETIC if language.name == "Chinese" else ALPHABETICAL
        assert language.kind is expected, language.name
        assert is_functional(language.name), language.name


def _source_ids():
    from vimdiomas.platform import linux, macos

    return [*macos.DISPLAY_NAMES, *linux.DISPLAY_NAMES]


def test_no_language_hint_matches_another_languages_source():
    for source_id in _source_ids():
        owners = [
            language.name
            for language in LANGUAGES
            if any(hint.lower() in source_id.lower() for hint in language.input_hints)
        ]
        assert len(owners) <= 1, f"{source_id} matches {owners}"


def test_every_alphabetical_languages_layout_is_claimed_by_it():
    claimed = {
        "com.apple.keylayout.Italian": "Italian",
        "com.apple.keylayout.Italian-Pro": "Italian",
        "com.apple.keylayout.French": "French",
        "com.apple.keylayout.French-PC": "French",
        "com.apple.keylayout.Spanish-ISO": "Spanish",
        "com.apple.keylayout.LatinAmerican": "Spanish",
        "com.apple.keylayout.British": "English",
        "com.apple.keylayout.ABC": "English",
        "keyboard-it": "Italian",
        "xkb:fr::fra": "French",
        "keyboard-latam": "Spanish",
        "xkb:gb:extd:eng": "English",
        "keyboard-de": "German",
        "xkb:de::ger": "German",
    }
    for source_id, name in claimed.items():
        owners = [
            language.name
            for language in LANGUAGES
            if any(hint.lower() in source_id.lower() for hint in language.input_hints)
        ]
        assert owners == [name], source_id


def test_preselect_language_picks_the_layout_of_the_language():
    from vimdiomas.platform import InputSource
    from vimdiomas.tui.screens.input_methods import preselect_language

    sources = [
        InputSource("com.apple.keylayout.US", "U.S."),
        InputSource("com.apple.keylayout.German", "German"),
        InputSource("com.apple.keylayout.Italian", "Italian"),
        InputSource("com.apple.keylayout.French", "French"),
    ]
    assert preselect_language(sources, "Italian") == "com.apple.keylayout.Italian"
    assert preselect_language(sources, "French") == "com.apple.keylayout.French"
    assert preselect_language(sources, "English") == "com.apple.keylayout.US"
    # No Spanish layout enabled: the first source, as for any language.
    assert preselect_language(sources, "Spanish") == "com.apple.keylayout.US"


def test_no_code_names_a_language_beyond_the_registry_and_the_platform_tables():
    """Adding Italian is a registry entry (Sprint 6 M7): no executable string
    elsewhere in the package names Italian, French, English or Spanish."""
    import ast
    from pathlib import Path

    import vimdiomas

    package = Path(vimdiomas.__file__).parent
    allowed = {package / "languages.py"}
    names = ("Italian", "French", "English", "Spanish")
    offenders = []
    for path in sorted(package.rglob("*.py")):
        if path in allowed or (package / "platform") in path.parents:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        docstrings = {
            id(node.body[0].value)
            for node in ast.walk(tree)
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
        }
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and id(node) not in docstrings
                and any(name in node.value for name in names)
            ):
                offenders.append(f"{path.name}:{node.lineno}: {node.value!r}")
    assert not offenders, "\n".join(offenders)
