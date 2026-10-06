"""Every alphabetical language works on arrival (Sprint 6 M7): nothing is
written for Italian, French, English or Spanish beyond their registry entry, so
each one's Entry screen and PDFs come out as German's do.

Every language here is looked up in the registry for its kind, exactly as the
app does — nothing in this file names a kind per language.
"""

from pathlib import Path

import pytest
from textual.app import App

from vimdiomas.compile import compile_file, render_markdown
from vimdiomas.config import NotebookConfig
from vimdiomas.languages import ALPHABETICAL, LANGUAGES, get_language
from vimdiomas.parser import parse
from vimdiomas.store import ensure_tree
from vimdiomas.tui.screens.entry import NEW_SUBTITLE, EntryScreen, EntryTree
from vimdiomas.tui.screens.panels import SelectField

# A word with an accent the language is known for, and its translation.
WORDS = {
    "Italian": ("perché", "because"),
    "French": ("garçon", "boy"),
    "English": ("naïve", "innocent"),
    "Spanish": ("niño", "child"),
    "German": ("Straße", "street"),
}

NEW_LANGUAGES = ["Italian", "French", "English", "Spanish"]


class _Host(App):
    def __init__(self, config: NotebookConfig) -> None:
        super().__init__()
        self._config = config

    def on_mount(self) -> None:
        self.push_screen(EntryScreen(self._config))


def _notebook(tmp_path, language) -> NotebookConfig:
    ensure_tree(tmp_path)
    (tmp_path / "Vocabulary" / "Cibo.md").write_text("# Cibo\n\n## Generale\n\n", encoding="utf-8")
    (tmp_path / "Grammar" / "Frasi.md").write_text(
        "# Frasi\n\n## Base\n\n", encoding="utf-8"
    )
    return NotebookConfig(
        tree_root=tmp_path, language=language, kind=get_language(language).kind
    )


def _find(node, kind, file_name, category_name=None):
    for child in node.children:
        found = _find(child, kind, file_name, category_name)
        if found is not None:
            return found
    data = node.data
    if (
        data is not None
        and data.kind == kind
        and data.file_path.name == file_name
        and (category_name is None or data.category_name == category_name)
    ):
        return node
    return None


def _select(tree, node):
    ancestor = node.parent
    while ancestor is not None:
        ancestor.expand()
        ancestor = ancestor.parent
    # `expand()` only invalidates the tree's cached lines; force a rebuild so
    # the node has a line to move the cursor to.
    tree._invalidate()
    _ = tree._tree_lines
    tree.move_cursor(node)


@pytest.mark.parametrize("language", NEW_LANGUAGES)
def test_the_new_languages_are_alphabetical_registry_entries(language):
    assert get_language(language).kind is ALPHABETICAL
    assert language in [entry.name for entry in LANGUAGES]


@pytest.mark.parametrize("language", NEW_LANGUAGES)
async def test_entry_adds_a_word_with_no_reading_and_it_parses_back(tmp_path, language):
    word, translation = WORDS[language]
    app = _Host(_notebook(tmp_path, language))
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        tree = screen.query_one("#entry-tree", EntryTree)
        # Entry for an alphabetical language has no reading field to tab past.
        category = _find(tree.root, "category", "Cibo.md", "Generale")
        _select(tree, category)
        await pilot.pause()
        assert list(screen.query("#reading")) == []

        screen.query_one("#word").value = word
        screen.query_one("#translation").value = translation
        screen._create_entry()
        await pilot.pause()

    path = tmp_path / "Vocabulary" / "Cibo.md"
    deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=ALPHABETICAL)
    assert warnings == []
    entries = [entry for category in deck.categories for entry in category.entries]
    assert [(e.word, e.reading, e.translation) for e in entries] == [(word, "", translation)]


@pytest.mark.parametrize("language", NEW_LANGUAGES)
async def test_entry_adds_a_grammar_point_under_a_subtitle(tmp_path, language):
    word, translation = WORDS[language]
    app = _Host(_notebook(tmp_path, language))
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        tree = screen.query_one("#entry-tree", EntryTree)
        category = _find(tree.root, "category", "Frasi.md", "Base")
        _select(tree, category)
        await pilot.pause()

        screen.query_one("#word").value = word
        screen.query_one("#translation").value = translation
        screen.query_one("#subtitle", SelectField).value = NEW_SUBTITLE
        screen.query_one("#subtitle-name").value = "Uno"
        screen._create_entry()
        await pilot.pause()

    path = tmp_path / "Grammar" / "Frasi.md"
    deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=ALPHABETICAL, grammar=True)
    assert warnings == []
    entries = [e for category in deck.categories for s in category.subtitles for e in s.entries]
    assert [(e.word, e.translation) for e in entries] == [(word, translation)]


@pytest.mark.parametrize("language", NEW_LANGUAGES)
def test_a_vocabulary_and_a_grammar_deck_render_with_no_reading_column(tmp_path, language):
    word, translation = WORDS[language]
    kind = get_language(language).kind
    vocabulary = tmp_path / "Cibo.md"
    vocabulary.write_text(f"# Cibo\n\n## Generale\n\n{word}\t{translation}\n", encoding="utf-8")
    grammar = tmp_path / "Frasi.md"
    grammar.write_text(
        f"# Frasi\n\n## Base\n\n### Uno\n\n{word}\t{translation}\n", encoding="utf-8"
    )

    for path, is_grammar in ((vocabulary, False), (grammar, True)):
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=kind, grammar=is_grammar)
        assert warnings == []
        markdown = render_markdown(deck, kind=kind, grammar=is_grammar)
        assert word in markdown and translation in markdown


@pytest.mark.integration
@pytest.mark.parametrize("language", NEW_LANGUAGES)
def test_a_vocabulary_deck_compiles_for_real_and_prints_the_accent(tmp_path, language):
    word, translation = WORDS[language]
    source = tmp_path / "Cibo.md"
    source.write_text(f"# Cibo\n\n## Generale\n\n{word}\t{translation}\n", encoding="utf-8")
    pdf = tmp_path / "Cibo.pdf"

    compile_file(source, pdf, kind=get_language(language).kind)

    text = _pdf_text(pdf)
    assert word in text and translation in text


@pytest.mark.integration
@pytest.mark.parametrize("language", NEW_LANGUAGES)
def test_a_grammar_deck_compiles_for_real_and_prints_the_accent(tmp_path, language):
    word, translation = WORDS[language]
    source = tmp_path / "Frasi.md"
    source.write_text(
        f"# Frasi\n\n## Base\n\n### Uno\n\n{word}\t{translation}\n", encoding="utf-8"
    )
    pdf = tmp_path / "Frasi.pdf"

    compile_file(source, pdf, kind=get_language(language).kind, grammar=True)

    text = _pdf_text(pdf)
    assert word in text and translation in text


def _pdf_text(pdf_path: Path) -> str:
    pypdf = pytest.importorskip("pypdf")
    return "\n".join(page.extract_text() for page in pypdf.PdfReader(str(pdf_path)).pages)
