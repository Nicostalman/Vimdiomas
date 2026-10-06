"""What a language is: the one place its behaviour is described (Sprint 6 M5).

A language belongs to a *kind*, which decides what an entry looks like — how
many word fields it has, whether a phonetic reading exists and is guessed from
the word, and which CJK face the renderer sets. Kinds are data, not classes:
code that differs by kind branches on the kind's fields (`has_reading` above
all). Adding a language of an existing kind is one entry in `LANGUAGES`.

The kind is not stored in the config: it is looked up here by the language's
name, so a config written before kinds existed reads exactly as it did.
"""

from collections.abc import Callable
from dataclasses import dataclass

from vimdiomas import pinyin
from vimdiomas.platform import CJK_FONT_NAME


@dataclass(frozen=True)
class LanguageKind:
    """How an entry is shaped and rendered, for every language of the kind.

    `reading_label` is `None` when the kind has no reading. When `guess_reading`
    is set, the reading field is read-only and filled in as the user types.
    """

    name: str
    word_label: str
    reading_label: str | None
    guess_reading: Callable[[str], str] | None
    cjk_font: str | None

    @property
    def has_reading(self) -> bool:
        return self.reading_label is not None


CHARACTER_PHONETIC = LanguageKind(
    name="character and phonetic",
    word_label="Hanzi",
    reading_label="Pinyin",
    guess_reading=pinyin.guess,
    cjk_font=CJK_FONT_NAME,
)

# No CJK face, and so no xeCJK in the PDF: an alphabetical kind is set in the
# template's own Latin face, Latin Modern (Sprint 6 M6).
ALPHABETICAL = LanguageKind(
    name="alphabetical",
    word_label="Word",
    reading_label=None,
    guess_reading=None,
    cjk_font=None,
)


@dataclass(frozen=True)
class Language:
    """One language the app knows about.

    `input_hints` are the substrings that mark an input source as this
    language's. `functional` is whether its notebook opens; `False` shows the
    placeholder instead.
    """

    name: str
    kind: LanguageKind
    input_hints: tuple[str, ...] = ()
    functional: bool = True


# In the order the wizard offers them, and Settings' *Add a language* lists
# them (Sprint 6 M7). Adding a language of an existing kind is one entry here.
#
# Hints are matched case-insensitively as substrings of a source ID, on both
# platforms' ID formats, and only ever preselect an option. English avoids a
# bare `US`, which would match `Russian`; `tests/test_languages.py` asserts no
# hint of one language matches another's source IDs.
LANGUAGES = (
    Language(
        "Chinese",
        CHARACTER_PHONETIC,
        input_hints=("SCIM", "TCIM", "Pinyin", "Zhuyin", "Cangjie", "Wubi", "Shuangpin"),
    ),
    Language("German", ALPHABETICAL, input_hints=("German", "keyboard-de", "xkb:de")),
    Language("Italian", ALPHABETICAL, input_hints=("Italian", "keyboard-it", "xkb:it")),
    Language("French", ALPHABETICAL, input_hints=("French", "keyboard-fr", "xkb:fr")),
    Language(
        "English",
        ALPHABETICAL,
        input_hints=(
            "keylayout.US",
            "keylayout.ABC",
            "keylayout.British",
            "keyboard-us",
            "keyboard-gb",
            "xkb:us",
            "xkb:gb",
        ),
    ),
    Language(
        "Spanish",
        ALPHABETICAL,
        input_hints=(
            "Spanish",
            "LatinAmerican",
            "keyboard-es",
            "keyboard-latam",
            "xkb:es",
            "xkb:latam",
        ),
    ),
)


def get_language(name: str) -> Language | None:
    """The registry entry for `name`, or `None` for a name not in it — which a
    hand-edited config can hold, and which is treated as a language that isn't
    functional, never as an error."""
    for language in LANGUAGES:
        if language.name == name:
            return language
    return None


def is_functional(name: str) -> bool:
    language = get_language(name)
    return language is not None and language.functional
