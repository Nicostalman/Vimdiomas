"""The two-field input-method form, shared by the installation wizard and
Settings (Sprint 4 M6).

Both surfaces ask the same question — which source types the language, which
types the translation — so they compose it from here rather than each
building their own and drifting apart.
"""

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static

from vimdiomas.languages import get_language
from vimdiomas.platform import (
    INPUT_SOURCES_SETTINGS,
    InputSource,
    is_keyboard_layout,
    list_input_sources,
)
from vimdiomas.tui.screens.panels import SelectField

LANGUAGE_FIELD_ID = "language-input-method"
TRANSLATION_FIELD_ID = "translation-input-method"

TRANSLATION_LABEL = "Translation input"

# The question both surfaces ask, in the same words (`design.md`'s *Settings*:
# a setting the wizard asks for is a setting Settings can change). The wizard's
# step, Settings' Input methods and Settings' Add a language all show it.
INPUT_METHOD_PROMPT = "Which keyboard do you type each side with? They may be the same."

# Substrings that mark a source as belonging to a language. Only ever used
# to decide which option starts highlighted — both fields always offer every
# enabled source, since a filter that hides a valid choice is worse than an
# ordering that merely guesses wrong (Sprint 4 M6 requirements · Preselection).
# Where sources are enabled comes from the platform layer (Sprint 5 M7) —
# System Settings on macOS, fcitx5's or ibus' settings on Linux.
NO_SOURCES_MESSAGE = (
    f"No input sources found. Add one in {INPUT_SOURCES_SETTINGS}; "
    "until then, Vimdiomas won't switch input for you."
)

ONE_SOURCE_MESSAGE = (
    "Only one input source is enabled, so both fields use it and nothing "
    f"will switch. Add another in {INPUT_SOURCES_SETTINGS}, "
    "then set it here from Settings › Input methods."
)


def available_sources() -> list[InputSource]:
    return list_input_sources()


def choices(sources: list[InputSource]) -> list[tuple[str, str]]:
    """`(id, label)` pairs for a `SelectField`'s list.

    The raw ID travels alongside the display name while choosing: names come
    from a small table (`platform.macos.DISPLAY_NAMES`) rather than the
    Carbon `TIS` API, so an unrecognised source must still be identifiable.
    """
    return [(source.id, f"{source.name}  ({source.id})") for source in sources]


def short_labels(sources: list[InputSource]) -> dict[str, str]:
    """Names alone, for the collapsed line — which already carries the
    field's own label in front of it and would overflow the panel's width
    with an ID on top of that."""
    return {source.id: source.name for source in sources}


def language_field_label(language: str) -> str:
    return f"{language} input"


def preselect_language(
    sources: list[InputSource], language: str, current: str = ""
) -> str:
    """Which source the language field starts on.

    An already-configured value always wins — revisiting a wizard step with
    `q`, or opening Settings, must show what's stored, not a fresh guess.
    """
    if current:
        return current
    registered = get_language(language)
    hints = registered.input_hints if registered else ()
    for source in sources:
        if any(hint.lower() in source.id.lower() for hint in hints):
            return source.id
    return sources[0].id if sources else ""


def preselect_translation(
    sources: list[InputSource], language_choice: str, current: str = ""
) -> str:
    """Which source the translation field starts on: the first plain keyboard
    layout the language field didn't already take, else the first source at
    all — which, with only one enabled, is the same one both fields get, the
    dev's stated fallback case."""
    if current:
        return current
    for source in sources:
        if source.id != language_choice and is_keyboard_layout(source.id):
            return source.id
    for source in sources:
        if source.id != language_choice:
            return source.id
    return sources[0].id if sources else ""


def compose_fields(
    language: str,
    sources: list[InputSource],
    input_method: str = "",
    translation_input_method: str = "",
) -> ComposeResult:
    """The two fields, plus an advisory line when there's less to choose from
    than the question really needs. The advisory never blocks: the dev's
    call is that a thin or empty list warns and lets the user carry on, since
    switching degrades to a no-op exactly as it already does without
    `macism`."""
    options = choices(sources)
    short = short_labels(sources)
    language_value = preselect_language(sources, language, input_method)
    translation_value = preselect_translation(
        sources, language_value, translation_input_method
    )

    yield SelectField(
        language_field_label(language),
        options,
        value=language_value,
        short_labels=short,
        id=LANGUAGE_FIELD_ID,
    )
    yield SelectField(
        TRANSLATION_LABEL,
        options,
        value=translation_value,
        short_labels=short,
        id=TRANSLATION_FIELD_ID,
    )
    if not sources:
        yield Static(NO_SOURCES_MESSAGE, classes="wizard-advisory")
    elif len(sources) == 1:
        yield Static(ONE_SOURCE_MESSAGE, classes="wizard-advisory")


def read_fields(container: Widget) -> tuple[str, str]:
    """The two chosen IDs, in `LanguageConfig` order."""
    return (
        container.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value,
        container.query_one(f"#{TRANSLATION_FIELD_ID}", SelectField).value,
    )
