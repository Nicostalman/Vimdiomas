from pathlib import Path

import pytest

from vimdiomas.config import NotebookConfig
from vimdiomas.languages import ALPHABETICAL, CHARACTER_PHONETIC, LanguageKind
from vimdiomas.parser import parse
from vimdiomas.tui.screens.entry import NEW_SUBTITLE, EntryScreen, EntryTree
from vimdiomas.tui.screens.panels import Backpanel, Panel, SelectField
from textual import events
from textual.app import App
from textual.widgets import Button, Input


HANZI_SOURCE = "com.apple.inputmethod.SCIM.ITABC"
TRANSLATION_SOURCE = "com.apple.keylayout.USInternational-PC"


class _HostApp(App):
    def __init__(
        self,
        tree_root: Path,
        language: str = "Chinese",
        input_method: str = HANZI_SOURCE,
        translation_input_method: str = TRANSLATION_SOURCE,
        kind: LanguageKind = CHARACTER_PHONETIC,
    ) -> None:
        super().__init__()
        self._config = NotebookConfig(
            tree_root=tree_root,
            language=language,
            kind=kind,
            input_method=input_method,
            translation_input_method=translation_input_method,
        )

    def on_mount(self) -> None:
        self.push_screen(EntryScreen(self._config))


class _Calls:
    """A view onto the recorded `switch_to` arguments, counting only the
    ones for a given source — the switch used to be two separate functions
    (Sprint 2) and is one config-driven call since Sprint 4 M6, so the tests
    that predate it keep asserting per-source with no rewrite."""

    def __init__(self, recorded: list[str], source_id: str) -> None:
        self._recorded = recorded
        self._source_id = source_id

    def __eq__(self, other) -> bool:
        return [1 for call in self._recorded if call == self._source_id] == other

    def __repr__(self) -> str:
        return repr([1 for call in self._recorded if call == self._source_id])


def _find_all(node, kind):
    results = []
    if node.data is not None and node.data.kind == kind:
        results.append(node)
    for child in node.children:
        results.extend(_find_all(child, kind))
    return results


def _find_one(node, kind, file_name=None, category_name=None):
    matches = _find_all(node, kind)
    if file_name is not None:
        matches = [n for n in matches if n.data.file_path.name == file_name]
    if category_name is not None:
        matches = [n for n in matches if n.data.category_name == category_name]
    return matches[0]


def _select(tree, node):
    """Move the cursor to `node`, expanding its ancestors first.

    File nodes start collapsed (M3), so a node under one isn't in the tree's
    rendered lines until its parent is expanded — `Tree.move_cursor` on a
    hidden node silently resets the cursor instead of moving it.
    """
    ancestor = node.parent
    while ancestor is not None:
        ancestor.expand()
        ancestor = ancestor.parent
    # `expand()` only invalidates Tree's cached lines; `move_cursor` reads
    # `node._line` directly rather than forcing a rebuild, so force one here
    # or the node's line is still the stale -1 from before it was visible.
    tree._invalidate()
    _ = tree._tree_lines
    tree.move_cursor(node)


@pytest.fixture
def source_tree(tmp_path):
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Food.md").write_text(
        "# Food\n\n苹果\tping2guo3\tapple\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n\n"
        "## Tags\n\n#food\n",
        encoding="utf-8",
    )
    (vocab / "NoUncat.md").write_text(
        "# NoUncat\n\n## OnlyCat\n\n字\tzi4\tcharacter\n", encoding="utf-8"
    )
    return tmp_path


@pytest.fixture
def grammar_tree(tmp_path):
    """A tree with both a `Vocabulary/` and a `Grammar/` file, for M5's
    subtitle-field tests. `Conjunctions` mixes a loose entry with one
    existing subtitle, matching requirements.md's "category mixing loose
    entries with subtitled ones"."""
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "V.md").write_text(
        "# V\n\n再见\tzai4jian4\tbye\n\n## Greetings\n\n你好\tni3hao3\thello\n",
        encoding="utf-8",
    )

    grammar = tmp_path / "Grammar"
    grammar.mkdir()
    (grammar / "G.md").write_text(
        "# G\n\n"
        "## Conjunctions\n\n"
        "...\t\tellipsis\n\n"
        "### existing subtitle\n\n"
        "和\the2\tand\n\n"
        "## Empty Category\n",
        encoding="utf-8",
    )
    return tmp_path


async def test_tree_structure(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)

        food_uncat = _find_one(tree.root, "uncategorized", file_name="Food.md")
        assert food_uncat is not None

        food_categories = [
            n.data.category_name for n in _find_all(tree.root, "category") if n.data.file_path.name == "Food.md"
        ]
        assert food_categories == ["Meat"]

        # (uncategorized) is offered for every file, even one with no loose entries
        no_uncat_file = _find_one(tree.root, "uncategorized", file_name="NoUncat.md")
        assert no_uncat_file is not None

        # (new category) always present, last, for every file
        food_node = next(
            n for n in _find_all(tree.root, "file") if n.data.file_path.name == "Food.md"
        )
        labels = [str(c.label) for c in food_node.children]
        assert labels == ["(uncategorized)", "Meat", "(new category)"]


async def test_file_nodes_start_collapsed_and_expand_on_enter(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        food_node = next(
            n for n in _find_all(tree.root, "file") if n.data.file_path.name == "Food.md"
        )
        assert food_node.is_expanded is False

        tree.move_cursor(food_node)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert food_node.is_expanded is True
        # the cursor stays on the file node, it doesn't jump to a child
        assert tree.cursor_node is food_node


async def test_tree_root_reads_language_notebook(source_tree):
    app = _HostApp(source_tree, language="German")
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert str(tree.root.label) == "German notebook"


async def test_directory_and_file_are_not_targets(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        file_node = next(n for n in _find_all(tree.root, "file") if n.data.file_path.name == "Food.md")
        _select(tree, file_node)
        await pilot.pause()
        assert pilot.app.screen._active_target is None


async def test_off_target_disables_form_and_shows_warning(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        file_node = next(n for n in _find_all(tree.root, "file") if n.data.file_path.name == "Food.md")
        _select(tree, file_node)
        await pilot.pause()

        screen = pilot.app.screen
        assert screen.query_one("#target-warning").display is True
        assert screen.query_one("#category-name", Input).display is False
        for field_id in ("word", "translation", "note"):
            assert screen.query_one(f"#{field_id}", Input).disabled is True
        assert screen.query_one("#create-button", Button).disabled is True


async def test_valid_target_hides_warning_and_enables_form(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        screen = pilot.app.screen
        assert screen.query_one("#target-warning").display is False
        for field_id in ("word", "translation", "note"):
            assert screen.query_one(f"#{field_id}", Input).disabled is False
        assert screen.query_one("#create-button", Button).disabled is False


async def test_enter_on_category_focuses_form(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"
        assert pilot.app.screen.query_one("#category-name").display is False


async def test_new_category_shows_category_name_field(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()
        assert pilot.app.screen.query_one("#category-name").display is True
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "category-name"


async def test_capital_l_from_tree_panel_lands_in_form(source_tree):
    # H/L only switch panels when focus starts on the panel itself - a
    # focused Input intercepts every printable character (H and L included)
    # for itself, so the letter keys can only ever move focus *into* the
    # form, never back out of it, and only work from the tree *panel*, not
    # the tree's own content (see test_capital_h_from_tree_panel_does_nothing
    # and test_shift_right_from_tree_content_does_nothing).
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#tree-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("L")
        await pilot.pause()
        assert pilot.app.focused.id == "word"


async def test_capital_h_from_tree_panel_does_nothing(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#tree-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("H")
        await pilot.pause()
        assert pilot.app.focused is panel


async def test_shift_left_from_form_input_does_not_switch_panel(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"
        await pilot.press("shift+left")
        await pilot.pause()
        assert pilot.app.focused.id == "word"


async def test_shift_right_from_tree_panel_lands_in_form(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#tree-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused.id == "word"


async def test_shift_right_from_tree_content_does_nothing(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        tree.focus()
        await pilot.pause()
        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused is tree


async def test_shift_arrows_on_tree_content_do_not_move_the_cursor(source_tree):
    # Dev feedback, hands-on: shift-arrows used to fall back to Tree's own
    # defaults here (jump to parent/sibling) while the letter keys (H/J/K/L)
    # did nothing — inconsistent. Both are now equally inert on content.
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        tree.focus()
        await pilot.pause()

        for key in ("shift+left", "shift+right", "shift+up", "shift+down"):
            await pilot.press(key)
            await pilot.pause()
            assert pilot.app.focused is tree
            assert tree.cursor_node is meat


async def test_escape_defocuses_field_to_the_panel(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"

        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#entry-form", Panel)
        assert pilot.app.focused is panel


async def test_q_from_defocused_panel_pops_the_screen(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        screens_before = len(pilot.app.screen_stack)
        await pilot.press("q")
        await pilot.pause()
        assert len(pilot.app.screen_stack) == screens_before - 1


async def test_shift_left_from_defocused_panel_focuses_tree(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("shift+left")
        await pilot.pause()
        assert pilot.app.focused is tree


async def test_tab_from_defocused_panel_focuses_first_field(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("tab")  # move off hanzi first, to prove tab-from-panel resets to it
        await pilot.pause()
        assert pilot.app.focused.id == "translation"

        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "word"


async def test_tab_from_tree_panel_focuses_the_tree(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#tree-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("tab")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert pilot.app.focused is tree


async def test_opening_focuses_the_tree(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert pilot.app.focused is tree


async def test_escape_climbs_tree_panel_then_backpanel_then_stays(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert pilot.app.focused is tree

        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#tree-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is backpanel


async def test_enter_on_backpanel_lands_in_tree(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel

        await pilot.press("enter")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert pilot.app.focused is tree


async def test_enter_on_form_panel_lands_in_first_field(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#entry-form", Panel)
        assert pilot.app.focused is panel

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"


async def test_shift_right_with_no_target_rests_on_form_panel(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        file_node = next(n for n in _find_all(tree.root, "file") if n.data.file_path.name == "Food.md")
        _select(tree, file_node)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        tree_panel = pilot.app.screen.query_one("#tree-panel", Panel)
        assert pilot.app.focused is tree_panel

        await pilot.press("shift+right")
        await pilot.pause()
        form_panel = pilot.app.screen.query_one("#entry-form", Panel)
        assert pilot.app.focused is form_panel


async def test_capital_h_typed_into_field_is_text(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "translation"

        await pilot.press("H")
        await pilot.pause()
        assert pilot.app.screen.query_one("#translation").value == "H"
        assert pilot.app.focused.id == "translation"


async def test_escape_from_hanzi_switches_input_method_back(source_tree, monkeypatch):
    switched = []
    monkeypatch.setattr("vimdiomas.tui.screens.entry.switch_to", switched.append)
    pinyin_calls = _Calls(switched, HANZI_SOURCE)
    english_calls = _Calls(switched, TRANSLATION_SOURCE)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        assert pilot.app.focused.id == "word"
        assert pinyin_calls == [1]
        assert english_calls == []

        await pilot.press("escape")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        panel = pilot.app.screen.query_one("#entry-form", Panel)
        assert pilot.app.focused is panel
        assert english_calls == [1]


async def test_q_types_into_a_focused_input(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"
        await pilot.press("q")
        await pilot.pause()
        assert pilot.app.screen.query_one("#word").value == "q"
        assert pilot.app.focused.id == "word"


async def test_q_from_tree_pops_the_screen(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        tree.focus()
        await pilot.pause()
        screens_before = len(pilot.app.screen_stack)
        await pilot.press("q")
        await pilot.pause()
        assert len(pilot.app.screen_stack) == screens_before - 1


async def test_jk_move_tree_cursor(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        tree.focus()
        await pilot.pause()
        line_before = tree.cursor_line
        await pilot.press("j")
        await pilot.pause()
        assert tree.cursor_line == line_before + 1
        await pilot.press("k")
        await pilot.pause()
        assert tree.cursor_line == line_before


async def test_tab_cycles_and_wraps_without_category_field(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        expected = ["word", "translation", "note", "create-button", "word"]
        for expected_id in expected:
            assert pilot.app.focused.id == expected_id
            await pilot.press("tab")
            await pilot.pause()


async def test_new_category_hides_word_fields(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        screen = pilot.app.screen
        assert screen.query_one("#category-name", Input).display is True
        for field_id in ("word", "reading", "translation", "note"):
            assert screen.query_one(f"#{field_id}", Input).display is False


async def test_tab_cycles_with_only_category_field(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        expected = ["category-name", "create-button", "category-name"]
        for expected_id in expected:
            assert pilot.app.focused.id == expected_id
            await pilot.press("tab")
            await pilot.pause()


async def test_hanzi_prefills_pinyin(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        hanzi = pilot.app.screen.query_one("#word")
        pinyin = pilot.app.screen.query_one("#reading")

        hanzi.value = "牛"
        await pilot.pause()
        assert pinyin.value == "niu2"

        hanzi.value = "牛肉"
        await pilot.pause()
        assert pinyin.value == "niu2rou4"


async def test_pinyin_field_is_disabled_and_skipped_by_tab(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert pilot.app.screen.query_one("#reading", Input).disabled is True

        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "translation"


async def test_create_appends_entry_to_existing_category(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#reading").value = "zhu1rou4"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        meat_category = next(c for c in deck.categories if c.name == "Meat")
        assert [e.word for e in meat_category.entries] == ["牛肉", "猪肉"]

        # form cleared, selection kept
        assert pilot.app.screen.query_one("#word").value == ""
        assert tree.cursor_node.label == "Meat" or str(tree.cursor_node.label) == "Meat"


async def test_create_with_new_category_name_moves_cursor_and_accepts_followup(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        pilot.app.screen.query_one("#category-name").value = "Vegetables"
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert pilot.app.screen._active_target.kind == "category"
        assert pilot.app.screen._active_target.category_name == "Vegetables"
        assert str(tree.cursor_node.label) == "Vegetables"
        assert pilot.app.screen.query_one("#category-name").display is False
        # focus moves into the now-visible form's first field, not left on
        # the Create button that was just pressed
        assert pilot.app.focused.id == "word"

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        vegetables = next(c for c in deck.categories if c.name == "Vegetables")
        assert vegetables.entries == []

        # the normal add-word form takes over for a follow-up entry
        pilot.app.screen.query_one("#word").value = "番茄"
        pilot.app.screen.query_one("#reading").value = "fan1qie2"
        pilot.app.screen.query_one("#translation").value = "tomato"
        pilot.app.screen._create_entry()
        await pilot.pause()

        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        vegetables = next(c for c in deck.categories if c.name == "Vegetables")
        assert [e.word for e in vegetables.entries] == ["番茄"]


async def test_create_with_empty_category_name_is_a_no_op(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="NoUncat.md")
        _select(tree, new_cat)
        await pilot.pause()

        path = source_tree / "Vocabulary" / "NoUncat.md"
        before = path.read_text(encoding="utf-8")

        for blank_name in ("", "   "):
            pilot.app.screen.query_one("#category-name").value = blank_name
            pilot.app.screen._create_entry()
            await pilot.pause()

            assert path.read_text(encoding="utf-8") == before
            assert pilot.app.screen._active_target.kind == "new_category"
            assert str(tree.cursor_node.label) == "(new category)"


async def test_note_field_is_written(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "鸡肉"
        pilot.app.screen.query_one("#reading").value = "ji1rou4"
        pilot.app.screen.query_one("#translation").value = "chicken"
        pilot.app.screen.query_one("#note").value = "a note"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, _ = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        meat_category = next(c for c in deck.categories if c.name == "Meat")
        chicken = next(e for e in meat_category.entries if e.word == "鸡肉")
        assert chicken.note == "a note"


async def test_twenty_consecutive_creates_without_tree_navigation(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        for i in range(20):
            pilot.app.screen.query_one("#word").value = f"字{i}"
            pilot.app.screen.query_one("#reading").value = f"zi{i % 4 + 1}"
            pilot.app.screen.query_one("#translation").value = f"word {i}"
            pilot.app.screen._create_entry()
            await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        meat_category = next(c for c in deck.categories if c.name == "Meat")
        # original 牛肉 plus 20 new entries
        assert len(meat_category.entries) == 21


async def test_create_marks_file_dirty(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#reading").value = "zhu1rou4"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        assert path in pilot.app.screen._dirty_files


async def test_leaving_screen_compiles_dirty_files(source_tree, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: calls.append((src, dst)),
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#reading").value = "zhu1rou4"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        source_path = source_tree / "Vocabulary" / "Food.md"
        notebook_path = source_tree / "Vocabulary" / "Food.pdf"
        assert calls == [(source_path, notebook_path)]


async def test_leaving_screen_with_no_dirty_files_compiles_nothing(source_tree, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: calls.append((src, dst)),
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert calls == []


async def test_leaving_screen_compiles_multiple_dirty_files(source_tree, monkeypatch):
    calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: calls.append((src, dst)),
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)

        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#reading").value = "zhu1rou4"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

        only_cat = _find_one(tree.root, "category", file_name="NoUncat.md", category_name="OnlyCat")
        _select(tree, only_cat)
        await pilot.pause()
        pilot.app.screen.query_one("#word").value = "书"
        pilot.app.screen.query_one("#reading").value = "shu1"
        pilot.app.screen.query_one("#translation").value = "book"
        pilot.app.screen._create_entry()
        await pilot.pause()

        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        compiled_sources = {src for src, _ in calls}
        assert compiled_sources == {
            source_tree / "Vocabulary" / "Food.md",
            source_tree / "Vocabulary" / "NoUncat.md",
        }


async def test_autocompile_failure_notifies(source_tree, monkeypatch):
    import subprocess

    def _raise(src, dst, **kwargs):
        raise subprocess.CalledProcessError(1, ["pandoc"])

    monkeypatch.setattr("vimdiomas.tui.screens.base.compile_file", _raise)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        notifications = []
        monkeypatch.setattr(pilot.app, "notify", lambda *a, **k: notifications.append((a, k)))

        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#reading").value = "zhu1rou4"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        error_notifications = [(a, k) for a, k in notifications if k.get("severity") == "error"]
        assert len(error_notifications) == 1
        args, _ = error_notifications[0]
        assert "Food.md" in args[0]


async def test_hanzi_focus_and_blur_switch_input_method(source_tree, monkeypatch):
    switched = []
    monkeypatch.setattr("vimdiomas.tui.screens.entry.switch_to", switched.append)
    pinyin_calls = _Calls(switched, HANZI_SOURCE)
    english_calls = _Calls(switched, TRANSLATION_SOURCE)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        assert pilot.app.focused.id == "word"
        assert pinyin_calls == [1]
        assert english_calls == []

        pilot.app.screen.query_one("#translation").focus()
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        assert pinyin_calls == [1]
        assert english_calls == [1]


async def test_os_focus_roundtrip_does_not_reswitch_input_method(source_tree, monkeypatch):
    # Regression: switching the input source itself (via macism, which
    # simulates the OS hotkey) makes the terminal briefly lose and regain OS
    # focus. Textual reports that round trip as an AppBlur/AppFocus pair,
    # which unfocuses and refocuses whatever widget currently has focus —
    # without HanziInput's from_app_focus/app_focus guards, that would
    # re-trigger the switch and loop forever (only escaping the field broke
    # the loop by moving focus elsewhere).
    switched = []
    monkeypatch.setattr("vimdiomas.tui.screens.entry.switch_to", switched.append)
    pinyin_calls = _Calls(switched, HANZI_SOURCE)
    english_calls = _Calls(switched, TRANSLATION_SOURCE)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        assert pilot.app.focused.id == "word"
        assert pinyin_calls == [1]

        pilot.app.post_message(events.AppBlur())
        await pilot.pause()
        pilot.app.post_message(events.AppFocus())
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert pilot.app.focused.id == "word"
        assert pinyin_calls == [1]
        assert english_calls == []


async def test_unconfigured_language_switches_nothing(source_tree, monkeypatch):
    """With no input methods in the config — the only real case being a
    machine with none enabled — focusing hanzi must not reach the platform
    layer at all (Sprint 4 M6). Patched one level deeper than the other
    input-method tests, at `input_method`'s own call into the platform, so
    the no-op is verified end to end rather than at the screen's boundary.
    """
    switched = []
    monkeypatch.setattr("vimdiomas.input_method.switch_input_source", switched.append)

    app = _HostApp(source_tree, input_method="", translation_input_method="")
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        assert pilot.app.focused.id == "word"

        pilot.app.screen.query_one("#translation").focus()
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert switched == []


# -- grammar subtitle field (Sprint 5 M5) ---------------------------------


async def test_vocabulary_category_has_no_subtitle_field(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        greetings = _find_one(tree.root, "category", file_name="V.md", category_name="Greetings")
        _select(tree, greetings)
        await pilot.pause()
        assert pilot.app.screen.query_one("#subtitle", SelectField).display is False


async def test_grammar_category_shows_subtitle_field_with_choices(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        assert field.display is True
        assert field.value == ""
        assert field.choices == [("", "(none)"), ("existing subtitle", "existing subtitle"), (NEW_SUBTITLE, NEW_SUBTITLE)]


async def test_grammar_uncategorized_and_new_category_have_no_subtitle_field(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)

        uncat = _find_one(tree.root, "uncategorized", file_name="G.md")
        _select(tree, uncat)
        await pilot.pause()
        assert pilot.app.screen.query_one("#subtitle", SelectField).display is False

        new_category = _find_one(tree.root, "new_category", file_name="G.md")
        _select(tree, new_category)
        await pilot.pause()
        assert pilot.app.screen.query_one("#subtitle", SelectField).display is False


async def test_adding_with_none_puts_entry_in_category_entries(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "也"
        pilot.app.screen.query_one("#reading").value = "ye3"
        pilot.app.screen.query_one("#translation").value = "also"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        deck, _ = parse(path.read_text(encoding="utf-8"), "G", kind=CHARACTER_PHONETIC, grammar=True)
        category = deck.categories[0]
        assert [e.word for e in category.entries] == ["...", "也"]
        assert len(category.subtitles) == 1


async def test_adding_under_existing_subtitle(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.value = "existing subtitle"

        pilot.app.screen.query_one("#word").value = "也"
        pilot.app.screen.query_one("#reading").value = "ye3"
        pilot.app.screen.query_one("#translation").value = "also"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        deck, _ = parse(path.read_text(encoding="utf-8"), "G", kind=CHARACTER_PHONETIC, grammar=True)
        subtitle = deck.categories[0].subtitles[0]
        assert subtitle.name == "existing subtitle"
        assert [e.word for e in subtitle.entries] == ["和", "也"]


async def test_new_subtitle_with_name_and_hanzi_creates_subtitle_with_entry(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.value = NEW_SUBTITLE
        pilot.app.screen.query_one("#subtitle-name").value = "adversative conjunction"
        pilot.app.screen.query_one("#word").value = "但是"
        pilot.app.screen.query_one("#reading").value = "dan4shi4"
        pilot.app.screen.query_one("#translation").value = "but"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        deck, _ = parse(path.read_text(encoding="utf-8"), "G", kind=CHARACTER_PHONETIC, grammar=True)
        names = [s.name for s in deck.categories[0].subtitles]
        assert "adversative conjunction" in names
        new_subtitle = next(s for s in deck.categories[0].subtitles if s.name == "adversative conjunction")
        assert [e.word for e in new_subtitle.entries] == ["但是"]

        # The field now shows the new subtitle, ready for a second entry.
        assert field.value == "adversative conjunction"
        assert pilot.app.screen.query_one("#subtitle-name").display is False

        # A second add goes to the same subtitle without re-selecting it.
        pilot.app.screen.query_one("#word").value = "而"
        pilot.app.screen.query_one("#reading").value = "er2"
        pilot.app.screen.query_one("#translation").value = "yet"
        pilot.app.screen._create_entry()
        await pilot.pause()

        deck, _ = parse(path.read_text(encoding="utf-8"), "G", kind=CHARACTER_PHONETIC, grammar=True)
        new_subtitle = next(s for s in deck.categories[0].subtitles if s.name == "adversative conjunction")
        assert [e.word for e in new_subtitle.entries] == ["但是", "而"]


async def test_new_subtitle_with_name_no_hanzi_creates_empty_subtitle(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.value = NEW_SUBTITLE
        pilot.app.screen.query_one("#subtitle-name").value = "disjunctive conjunction"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        deck, _ = parse(path.read_text(encoding="utf-8"), "G", kind=CHARACTER_PHONETIC, grammar=True)
        new_subtitle = next(s for s in deck.categories[0].subtitles if s.name == "disjunctive conjunction")
        assert new_subtitle.entries == []


async def test_new_subtitle_with_no_name_is_noop(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        before = path.read_text(encoding="utf-8")

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.value = NEW_SUBTITLE
        pilot.app.screen.query_one("#word").value = "也"
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert path.read_text(encoding="utf-8") == before
        assert pilot.app.screen._dirty_files == set()


async def test_tab_cycles_through_subtitle_field(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert pilot.app.focused.id == "subtitle"
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "word"


async def test_selecting_none_or_existing_subtitle_focuses_hanzi(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j")  # (none) — the first option
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert field.value == ""
        assert pilot.app.focused.id == "word"


async def test_selecting_new_subtitle_focuses_subtitle_name_field(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(tree.root, "category", file_name="G.md", category_name="Conjunctions")
        _select(tree, conjunctions)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j", "j", "j")  # (new subtitle) — the third option
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert field.value == NEW_SUBTITLE
        assert pilot.app.focused.id == "subtitle-name"


# -- Sprint 6 M1 · #2: an entry with an empty translation round-trips -------


async def test_entry_with_an_empty_translation_saves_and_reloads(source_tree):
    """The report's P1 reproduction through the form: hanzi is the only
    required field, so this row was writable — and then unparseable, which
    locked the user out of the whole tree."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "羊肉"
        pilot.app.screen.query_one("#translation").value = ""
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        meat_category = next(c for c in deck.categories if c.name == "Meat")
        added = next(e for e in meat_category.entries if e.word == "羊肉")
        assert added.translation == ""


async def test_grammar_entry_with_an_empty_translation_saves_and_reloads(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(
            tree.root, "category", file_name="G.md", category_name="Conjunctions"
        )
        _select(tree, conjunctions)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "但是"
        pilot.app.screen.query_one("#translation").value = ""
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC, grammar=True)
        assert warnings == []
        category = next(c for c in deck.categories if c.name == "Conjunctions")
        added = next(e for e in category.entries if e.word == "但是")
        assert added.translation == ""


# -- Sprint 6 M1 · #15: a pasted tab can't shift the columns ---------------


async def test_pasted_tab_in_hanzi_keeps_the_row_three_columns(source_tree):
    """The report's reproduction: `苹果<TAB>apple` pasted from a spreadsheet
    wrote a five-column row and glued the guessed pinyin onto the wrong cell."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "苹果\tapple"
        await pilot.pause()
        assert pilot.app.screen.query_one("#word").value == "苹果 apple"
        assert "\t" not in pilot.app.screen.query_one("#reading").value

        pilot.app.screen.query_one("#translation").value = "apple"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        text = path.read_text(encoding="utf-8")
        row = next(line for line in text.splitlines() if line.startswith("苹果 apple"))
        assert row.count("\t") == 2

        deck, warnings = parse(text, path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        meat_category = next(c for c in deck.categories if c.name == "Meat")
        added = next(e for e in meat_category.entries if e.word == "苹果 apple")
        assert added.translation == "apple"


@pytest.mark.parametrize("field_id", ["word", "translation", "note"])
async def test_pasted_tab_in_any_word_field_becomes_a_space(source_tree, field_id):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "鸡肉"
        pilot.app.screen.query_one("#translation").value = "chicken"
        pilot.app.screen.query_one(f"#{field_id}").value = "a\tb"
        await pilot.pause()
        assert pilot.app.screen.query_one(f"#{field_id}").value == "a b"

        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []


async def test_pasted_tab_in_category_name_becomes_a_space(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        pilot.app.screen.query_one("#category-name").value = "Dairy\tstuff"
        await pilot.pause()
        assert pilot.app.screen.query_one("#category-name").value == "Dairy stuff"

        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        assert "Dairy stuff" in [c.name for c in deck.categories]


async def test_pasted_tab_in_subtitle_name_becomes_a_space(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        conjunctions = _find_one(
            tree.root, "category", file_name="G.md", category_name="Conjunctions"
        )
        _select(tree, conjunctions)
        await pilot.pause()

        pilot.app.screen.query_one("#subtitle", SelectField).value = NEW_SUBTITLE
        pilot.app.screen.query_one("#subtitle-name").value = "new\tsubtitle"
        await pilot.pause()
        assert pilot.app.screen.query_one("#subtitle-name").value == "new subtitle"

        pilot.app.screen._create_entry()
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC, grammar=True)
        assert warnings == []
        category = next(c for c in deck.categories if c.name == "Conjunctions")
        assert "new subtitle" in [s.name for s in category.subtitles]


# -- Sprint 6 M1 · #8: `Tags` is refused as a category name ----------------


@pytest.mark.parametrize("typed", ["Tags", "  Tags  "])
async def test_reserved_category_name_is_refused(source_tree, typed, monkeypatch):
    """`## Tags` is the heading `parser.py` reads as the file's tag block, so
    a category by that name produces a heading the parser never returns —
    and the report's follow-on `StopIteration` when an entry is added to it."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        before = path.read_text(encoding="utf-8")
        leaves_before = len(_find_all(tree.root, "category"))

        notifications = []
        monkeypatch.setattr(
            pilot.app.screen, "notify", lambda *a, **k: notifications.append((a, k))
        )

        pilot.app.screen.query_one("#category-name").value = typed
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert path.read_text(encoding="utf-8") == before
        assert len(_find_all(tree.root, "category")) == leaves_before
        assert pilot.app.screen._active_target.kind == "new_category"
        assert len(notifications) == 1
        args, kwargs = notifications[0]
        assert kwargs["severity"] == "error"
        assert "reserved" in args[0]


async def test_reserved_category_name_is_refused_in_a_grammar_file(
    grammar_tree, monkeypatch
):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="G.md")
        _select(tree, new_cat)
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        before = path.read_text(encoding="utf-8")

        notifications = []
        monkeypatch.setattr(
            pilot.app.screen, "notify", lambda *a, **k: notifications.append((a, k))
        )

        pilot.app.screen.query_one("#category-name").value = "Tags"
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert path.read_text(encoding="utf-8") == before
        assert [k.get("severity") for _, k in notifications] == ["error"]


async def test_lowercase_tags_is_an_ordinary_category_name(source_tree):
    """`parser.py` reserves the literal `## Tags` and nothing else, so `## tags`
    parses as an ordinary category and works. Refusing it would reject a name
    that isn't broken."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        pilot.app.screen.query_one("#category-name").value = "tags"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        assert "tags" in [c.name for c in deck.categories]
        assert deck.tags == ["food"]

        # and an entry added to it straight away lands there, rather than
        # raising the report's StopIteration
        pilot.app.screen.query_one("#word").value = "标签"
        pilot.app.screen.query_one("#translation").value = "tag"
        pilot.app.screen._create_entry()
        await pilot.pause()

        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        category = next(c for c in deck.categories if c.name == "tags")
        assert [e.word for e in category.entries] == ["标签"]


# -- Sprint 6 M1 · #18: a duplicate category name selects the existing one --


async def test_duplicate_category_name_selects_the_existing_category(
    source_tree, monkeypatch
):
    """A second `## Meat` would be a heading nothing can ever reach. Selecting
    the one already there is what subtitle creation already does."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        before = path.read_text(encoding="utf-8")

        notifications = []
        monkeypatch.setattr(
            pilot.app.screen, "notify", lambda *a, **k: notifications.append((a, k))
        )

        pilot.app.screen.query_one("#category-name").value = "Meat"
        pilot.app.screen._create_entry()
        await pilot.pause()

        # nothing written, and no second heading
        assert path.read_text(encoding="utf-8") == before
        assert before.count("## Meat") == 1

        # the cursor landed on the existing leaf, which is the active target
        assert pilot.app.screen._active_target.kind == "category"
        assert pilot.app.screen._active_target.category_name == "Meat"
        assert str(tree.cursor_node.label) == "Meat"
        food_leaves = [
            n.data.category_name
            for n in _find_all(tree.root, "category")
            if n.data.file_path.name == "Food.md"
        ]
        assert food_leaves == ["Meat"]
        assert notifications[0][0][0] == "Meat already exists — selected."

        # an entry created straight away lands under the existing heading
        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

        text = path.read_text(encoding="utf-8")
        assert text.count("## Meat") == 1
        deck, warnings = parse(text, path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        meat = next(c for c in deck.categories if c.name == "Meat")
        assert [e.word for e in meat.entries] == ["牛肉", "猪肉"]


async def test_duplicate_category_name_selects_existing_in_a_grammar_file(grammar_tree):
    app = _HostApp(grammar_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="G.md")
        _select(tree, new_cat)
        await pilot.pause()

        path = grammar_tree / "Grammar" / "G.md"
        before = path.read_text(encoding="utf-8")

        pilot.app.screen.query_one("#category-name").value = "Conjunctions"
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert path.read_text(encoding="utf-8") == before
        assert pilot.app.screen._active_target.category_name == "Conjunctions"
        assert pilot.app.screen._active_target.grammar is True
        # the grammar form's subtitle field came with it
        assert pilot.app.screen.query_one("#subtitle", SelectField).display is True


async def test_category_names_differing_only_in_case_are_both_created(source_tree):
    """Two headings the parser treats as distinct: neither is unreachable, so
    there is nothing to refuse."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new_cat = _find_one(tree.root, "new_category", file_name="Food.md")
        _select(tree, new_cat)
        await pilot.pause()

        pilot.app.screen.query_one("#category-name").value = "meat"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = source_tree / "Vocabulary" / "Food.md"
        deck, warnings = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        assert warnings == []
        assert [c.name for c in deck.categories] == ["Meat", "meat"]


# -- Sprint 6 M2 · #16: bracket text is text, not markup -------------------


@pytest.fixture
def bracket_tree(tmp_path):
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "[b]x.md").write_text(
        "# [b]x\n\n测试\tce4shi4\tto [/] test\n\n## Verbs [/x]\n\n走\tzou3\twalk\n",
        encoding="utf-8",
    )
    grammar = tmp_path / "Grammar"
    grammar.mkdir()
    (grammar / "G.md").write_text(
        "# G\n\n## Cat\n\n### [b]s[/b]\n\n和\the2\tand\n", encoding="utf-8"
    )
    return tmp_path


async def test_entry_opens_with_bracket_names_listed_literally(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        files = [str(n.label) for n in _find_all(tree.root, "file")]
        categories = [str(n.label) for n in _find_all(tree.root, "category")]
        assert "[b]x" in files
        assert "Verbs [/x]" in categories


async def test_bracket_category_is_selectable_and_takes_an_entry(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        verbs = _find_one(tree.root, "category", category_name="Verbs [/x]")
        _select(tree, verbs)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "[跑]"
        pilot.app.screen.query_one("#translation").value = "run"
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert pilot.app.is_running
        path = bracket_tree / "Vocabulary" / "[b]x.md"
        deck, _ = parse(path.read_text(encoding="utf-8"), path.stem, kind=CHARACTER_PHONETIC)
        verbs_category = next(c for c in deck.categories if c.name == "Verbs [/x]")
        assert [e.word for e in verbs_category.entries] == ["走", "[跑]"]
        assert "[跑] added successfully!" in [n.message for n in pilot.app._notifications]


async def test_creating_a_bracket_category_shows_it_literally(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        new = _find_one(tree.root, "new_category", file_name="[b]x.md")
        _select(tree, new)
        await pilot.pause()
        pilot.app.screen.query_one("#category-name").value = "[i]New[/i]"
        pilot.app.screen._create_entry()
        await pilot.pause()

        assert pilot.app.is_running
        categories = [str(n.label) for n in _find_all(tree.root, "category")]
        assert "[i]New[/i]" in categories


async def test_bracket_subtitle_is_listed_literally(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        cat = _find_one(tree.root, "category", file_name="G.md", category_name="Cat")
        _select(tree, cat)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        field.value = "[b]s[/b]"
        await pilot.pause()
        options = pilot.app.screen.query_one("#subtitle-list")
        drawn = [str(options._get_visual(option)) for option in options._options]
        assert "[b]s[/b]" in drawn
        assert "[b]s[/b]" in str(pilot.app.screen.query_one("#subtitle-display").render())


async def test_autocompiling_a_syllabic_consonant_raises_nothing_and_records(
    source_tree, monkeypatch
):
    """Sprint 6 M3, #4 and #11: `嗯` guesses to `n2`, which the tone renderer
    used to reject with a ValueError nothing caught; and the autocompile
    that follows records its stamp, so a later Compile knows what is in the
    PDF. Only pandoc is faked — the real render and the real cache run."""
    import vimdiomas.compile as compile_module

    monkeypatch.setattr(compile_module, "_run_pandoc", lambda md, dst, kind: dst.write_bytes(b"%PDF"))

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        pilot.app.screen.query_one("#word").value = "嗯"
        await pilot.pause()
        assert pilot.app.screen.query_one("#reading").value == "n2"
        pilot.app.screen.query_one("#translation").value = "uh-huh"
        pilot.app.screen._create_entry()
        await pilot.pause()

        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert pilot.app.is_running
    source_path = source_tree / "Vocabulary" / "Food.md"
    assert str(source_path) in compile_module._load_cache()
    assert source_path.with_suffix(".pdf") not in compile_module.compile_all(
        source_tree, kind=CHARACTER_PHONETIC
    ).compiled


# -- Sprint 6 M5: the form is built from the language's kind -------------------


async def test_chinese_placeholders_are_hanzi_and_pinyin(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        assert screen.query_one("#word", Input).placeholder == "Hanzi"
        assert screen.query_one("#reading", Input).placeholder == "Pinyin"


async def test_a_kind_without_a_reading_composes_no_reading_field(source_tree):
    """An alphabetical notebook's Entry: no reading field, nothing guessed, and
    the two-column row on disk (Sprint 6 M6)."""
    app = _HostApp(source_tree, kind=ALPHABETICAL)
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        tree = screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()

        assert list(screen.query("#reading")) == []
        assert screen.query_one("#word", Input).placeholder == "Word"

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "translation"

        screen.query_one("#word").value = "Fleisch"
        await pilot.pause()
        screen.query_one("#translation").value = "meat"
        screen._create_entry()
        await pilot.pause()

        text = (source_tree / "Vocabulary" / "Food.md").read_text(encoding="utf-8")
        assert "Fleisch\tmeat\n" in text
        assert screen.query_one("#word").value == ""


async def test_a_language_of_an_existing_kind_is_a_table_entry_not_a_code_change(
    tmp_path, monkeypatch
):
    """Sprint 6 M5's done-when: a character-and-phonetic language added only to
    the registry is functional on the landing menu, and its notebook behaves
    as Chinese's does — Entry guesses pinyin, writes the same row, and Compile
    hands pandoc the CJK font. Nothing outside the monkeypatched table
    changes."""
    from vimdiomas import compile as compile_module
    from vimdiomas import languages
    from vimdiomas.config import Config, LanguageConfig
    from vimdiomas.languages import Language
    from vimdiomas.tui.app import VimdiomasApp
    from vimdiomas.tui.screens.main_menu import MainMenuScreen

    monkeypatch.setattr(
        languages,
        "LANGUAGES",
        (*languages.LANGUAGES, Language("Testonese", CHARACTER_PHONETIC, input_hints=())),
    )
    monkeypatch.setattr(compile_module, "CACHE_PATH", tmp_path / "cache.json")
    pandoc_calls = []
    monkeypatch.setattr(
        compile_module.subprocess,
        "run",
        lambda args, **kwargs: pandoc_calls.append(args)
        or Path(args[args.index("-o") + 1]).write_bytes(b"%PDF"),
    )
    config = Config(
        user_name="Nico", root=tmp_path, languages=[LanguageConfig(name="Testonese")]
    )
    vocab = config.tree_root("Testonese") / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Food.md").write_text("# Food\n\n## Meat\n\n牛肉\tniu2rou4\tbeef\n", encoding="utf-8")

    async def choose(pilot, index):
        pilot.app.screen.query_one("OptionList").highlighted = index
        await pilot.press("enter")
        await pilot.pause()

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        legend = pilot.app.screen.query_one("OptionList")._options[0]
        assert str(legend.prompt) == "Testonese notebook"
        await choose(pilot, 0)
        assert isinstance(pilot.app.screen, MainMenuScreen)

        await choose(pilot, 0)  # Enter vocabulary
        screen = pilot.app.screen
        assert isinstance(screen, EntryScreen)
        assert screen.query_one("#word", Input).placeholder == "Hanzi"
        assert screen.query_one("#reading", Input).placeholder == "Pinyin"

        tree = screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        screen.query_one("#word").value = "猪肉"
        await pilot.pause()
        assert screen.query_one("#reading").value == "zhu1rou4"
        screen.query_one("#translation").value = "pork"
        screen._create_entry()
        await pilot.pause()
        assert "猪肉\tzhu1rou4\tpork\n" in (vocab / "Food.md").read_text(encoding="utf-8")

        await pilot.app.pop_screen()  # leaving autocompiles the changed file
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        assert isinstance(pilot.app.screen, MainMenuScreen)
        assert pandoc_calls
        assert f"cjkfont={CHARACTER_PHONETIC.cjk_font}" in pandoc_calls[0]

        pandoc_calls.clear()
        (tmp_path / "cache.json").unlink()
        await choose(pilot, 3)  # Compile, from a clean cache
        assert pandoc_calls
        assert f"cjkfont={CHARACTER_PHONETIC.cjk_font}" in pandoc_calls[0]


# -- Sprint 6 M6: the German notebook ---------------------------------------


@pytest.fixture
def german_tree(tmp_path):
    """A German tree: a vocabulary file with an uncategorized row and a
    category, and a grammar file with one subtitle. Rows are two-column."""
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Essen.md").write_text(
        "# Essen\n\nHaus\thouse\n\n## Obst\n\nApfel\tapple\n", encoding="utf-8"
    )
    grammar = tmp_path / "Grammar"
    grammar.mkdir()
    (grammar / "Konjunktionen.md").write_text(
        "# Konjunktionen\n\n## Nebensätze\n\n### Kausal\n\nweil\tbecause\n", encoding="utf-8"
    )
    return tmp_path


def _german_app(tree_root):
    return _HostApp(tree_root, language="German", kind=ALPHABETICAL)


async def test_german_tree_shows_categories_uncategorized_and_new_category(german_tree):
    app = _german_app(german_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        # `has_uncategorized` is what puts Essen's two-column row in the tree.
        assert _find_one(tree.root, "uncategorized", file_name="Essen.md")
        assert _find_one(tree.root, "category", file_name="Essen.md", category_name="Obst")
        assert len(_find_all(tree.root, "new_category")) == 2


async def test_german_entry_is_written_as_a_two_column_row_and_the_form_clears(german_tree):
    app = _german_app(german_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        obst = _find_one(tree.root, "category", file_name="Essen.md", category_name="Obst")
        _select(tree, obst)
        await pilot.pause()

        screen = pilot.app.screen
        assert list(screen.query("#reading")) == []
        screen.query_one("#word").value = "Birne"
        await pilot.pause()
        screen.query_one("#translation").value = "pear"
        screen.query_one("#note").value = "feminine"
        screen._create_entry()
        await pilot.pause()

        text = (german_tree / "Vocabulary" / "Essen.md").read_text(encoding="utf-8")
        assert text == (
            "# Essen\n\nHaus\thouse\n\n## Obst\n\nApfel\tapple\nBirne\tpear\n    *feminine*\n"
        )
        assert screen.query_one("#word").value == ""
        assert screen.query_one("#translation").value == ""
        assert screen.query_one("#note").value == ""


async def test_german_uncategorized_entry_lands_in_the_file_head(german_tree):
    app = _german_app(german_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        uncategorized = _find_one(tree.root, "uncategorized", file_name="Essen.md")
        _select(tree, uncategorized)
        await pilot.pause()
        pilot.app.screen.query_one("#word").value = "Auto"
        pilot.app.screen.query_one("#translation").value = "car"
        pilot.app.screen._create_entry()
        await pilot.pause()

        text = (german_tree / "Vocabulary" / "Essen.md").read_text(encoding="utf-8")
        assert text.startswith("# Essen\n\nHaus\thouse\nAuto\tcar\n\n## Obst")


async def test_german_tab_order_is_word_translation_note(german_tree):
    app = _german_app(german_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        obst = _find_one(tree.root, "category", file_name="Essen.md", category_name="Obst")
        _select(tree, obst)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        order = []
        for _ in range(3):
            order.append(pilot.app.focused.id)
            await pilot.press("tab")
            await pilot.pause()
        assert order == ["word", "translation", "note"]


async def test_german_grammar_category_has_the_subtitle_field_and_new_subtitle_works(german_tree):
    app = _german_app(german_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        category = _find_one(
            tree.root, "category", file_name="Konjunktionen.md", category_name="Nebensätze"
        )
        _select(tree, category)
        await pilot.pause()

        field = pilot.app.screen.query_one("#subtitle", SelectField)
        assert field.choices == [("", "(none)"), ("Kausal", "Kausal"), (NEW_SUBTITLE, NEW_SUBTITLE)]

        field.value = NEW_SUBTITLE
        pilot.app.screen.query_one("#subtitle-name").value = "Konzessiv"
        pilot.app.screen.query_one("#word").value = "obwohl"
        pilot.app.screen.query_one("#translation").value = "although"
        pilot.app.screen._create_entry()
        await pilot.pause()

        path = german_tree / "Grammar" / "Konjunktionen.md"
        deck, warnings = parse(
            path.read_text(encoding="utf-8"), path.stem, kind=ALPHABETICAL, grammar=True
        )
        assert warnings == []
        subtitle = next(s for s in deck.categories[0].subtitles if s.name == "Konzessiv")
        assert [(e.word, e.translation) for e in subtitle.entries] == [("obwohl", "although")]


async def test_german_word_field_switches_input_source_from_the_config(german_tree, monkeypatch):
    switched = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.entry.switch_to", lambda source_id: switched.append(source_id)
    )
    app = _HostApp(
        german_tree,
        language="German",
        kind=ALPHABETICAL,
        input_method="com.apple.keylayout.German",
        translation_input_method="com.apple.keylayout.USInternational-PC",
    )
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        obst = _find_one(tree.root, "category", file_name="Essen.md", category_name="Obst")
        _select(tree, obst)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "word"
        await pilot.press("tab")
        await pilot.pause()

        assert switched[-2:] == [
            "com.apple.keylayout.German",
            "com.apple.keylayout.USInternational-PC",
        ]


async def test_leaving_a_german_notebook_autocompiles_with_the_alphabetical_kind(
    german_tree, monkeypatch
):
    calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: calls.append((src, kwargs)),
    )
    app = _german_app(german_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        obst = _find_one(tree.root, "category", file_name="Essen.md", category_name="Obst")
        _select(tree, obst)
        await pilot.pause()
        pilot.app.screen.query_one("#word").value = "Birne"
        pilot.app.screen.query_one("#translation").value = "pear"
        pilot.app.screen._create_entry()
        await pilot.pause()

        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

    assert calls == [
        (german_tree / "Vocabulary" / "Essen.md", {"kind": ALPHABETICAL, "grammar": False})
    ]


# -- Sprint 6 M9: manual editing checks -------------------------------------
#
# Entry carries the same marker as Inspect Tree, and its tree is built from
# the file each time the screen is opened — which is what makes a non-trivial
# hand change (a category renamed, added or removed) reach the form without a
# relaunch (requirements.md §§3, 5).


async def test_a_warned_file_is_marked_in_entrys_tree(source_tree):
    (source_tree / "Vocabulary" / "NoUncat.md").write_text(
        "# NoUncat\n\n## OnlyCat\n\n字\tzi4\tcharacter\n\n| a | b |\n", encoding="utf-8"
    )
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        labels = sorted(str(n.label) for n in _find_all(tree.root, "file"))
        assert labels == ["Food", "NoUncat ⚠"]


async def test_a_category_renamed_by_hand_is_the_target_next_time(source_tree):
    """A non-trivial change: nothing in the app holds the old name, so the
    new one is simply what the file says when the screen is next built."""
    path = source_tree / "Vocabulary" / "Food.md"
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        names = [n.data.category_name for n in _find_all(tree.root, "category")]
        assert "Meat" in names and "Protein" not in names

    path.write_text(
        path.read_text(encoding="utf-8").replace("## Meat", "## Protein"), encoding="utf-8"
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        protein = _find_one(tree.root, "category", file_name="Food.md", category_name="Protein")
        _select(tree, protein)
        await pilot.pause()
        # And it is a usable target, not just a label.
        assert pilot.app.screen._active_target.category_name == "Protein"


async def test_a_category_added_by_hand_appears_without_relaunching(source_tree):
    path = source_tree / "Vocabulary" / "Food.md"
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        # The screen is open; the file changes underneath it in another
        # terminal. The app does not notice — that is the dev's own rule.
        path.write_text(
            path.read_text(encoding="utf-8") + "\n## Snacks\n\n薯片\tshu3pian4\tchips\n",
            encoding="utf-8",
        )
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert "Snacks" not in [n.data.category_name for n in _find_all(tree.root, "category")]

    # Opening the screen again is "entering through the app", and reads it.
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        assert "Snacks" in [n.data.category_name for n in _find_all(tree.root, "category")]


async def test_a_create_into_a_hand_edited_file_keeps_the_hand_edits(source_tree):
    """Entry re-reads the file before every write, so a hand edit made while
    the screen was open is not overwritten by it."""
    path = source_tree / "Vocabulary" / "Food.md"
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "## Meat\n", "## Meat\n\n羊肉\tyang2rou4\tlamb\n"
            ),
            encoding="utf-8",
        )
        tree = pilot.app.screen.query_one("#entry-tree", EntryTree)
        meat = _find_one(tree.root, "category", file_name="Food.md", category_name="Meat")
        _select(tree, meat)
        await pilot.pause()
        pilot.app.screen.query_one("#word").value = "猪肉"
        pilot.app.screen.query_one("#reading").value = "zhu1rou4"
        pilot.app.screen.query_one("#translation").value = "pork"
        pilot.app.screen._create_entry()
        await pilot.pause()

    deck, warnings = parse(path.read_text(encoding="utf-8"), "Food", kind=CHARACTER_PHONETIC)
    meat = next(c for c in deck.categories if c.name == "Meat")
    # The hand-added lamb is still there, with the app's pork after it.
    assert [e.word for e in meat.entries] == ["羊肉", "牛肉", "猪肉"]
    assert warnings == []
