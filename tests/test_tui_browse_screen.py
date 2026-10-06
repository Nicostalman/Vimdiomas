from pathlib import Path
from unittest.mock import patch

import pytest
from rich.cells import cell_len

from vimdiomas.languages import ALPHABETICAL, CHARACTER_PHONETIC
from vimdiomas.store import ContentHit
from vimdiomas.tui.screens.browse import (
    BrowseScreen,
    format_row,
    hit_fields,
    hit_location,
    hit_style,
    list_pdfs,
    paths_with_tag,
)
from vimdiomas.tui.screens.panels import Panel
from textual.app import App
from textual.widgets import Input, OptionList, Static


class _HostApp(App):
    def __init__(self, tree_root: Path, *, kind=CHARACTER_PHONETIC) -> None:
        super().__init__()
        self._tree_root = tree_root
        self._kind = kind

    def on_mount(self) -> None:
        self.push_screen(BrowseScreen(self._tree_root, kind=self._kind))


@pytest.fixture
def tree(tmp_path):
    tree_root = tmp_path / "tree-Chinese"
    (tree_root / "Vocabulary").mkdir(parents=True)
    (tree_root / "Grammar").mkdir(parents=True)

    (tree_root / "Vocabulary" / "Food.md").write_text(
        "# Food\n\n苹果\tping2guo3\tapple\n\n## Tags\n\n#food #travel\n",
        encoding="utf-8",
    )
    (tree_root / "Grammar" / "Asking for directions.md").write_text(
        "# Asking for directions\n\n请问\tqing3wen4\texcuse me\n\n"
        '## Tags\n\n#travel #"C1 exam"\n',
        encoding="utf-8",
    )
    (tree_root / "Vocabulary" / "Numbers.md").write_text(
        "# Numbers\n\n一\tyi1\tone\n", encoding="utf-8"
    )

    (tree_root / "Vocabulary" / "Food.pdf").write_bytes(b"%PDF fake")
    (tree_root / "Grammar" / "Asking for directions.pdf").write_bytes(b"%PDF fake")
    # Numbers.md deliberately not compiled yet.

    return tree_root


def _labels(screen):
    results = screen.query_one("#results", OptionList)
    return [str(option.prompt) for option in results._options]


async def test_list_pdfs_returns_relative_paths(tree):
    paths = {str(p) for p in list_pdfs(tree)}
    assert paths == {"Vocabulary/Food.pdf", "Grammar/Asking for directions.pdf"}


async def test_paths_with_tag_only_includes_compiled_files(tree):
    # Numbers.md has no tags at all, and isn't compiled - shouldn't appear regardless.
    travel = paths_with_tag(tree, "travel", kind=CHARACTER_PHONETIC)
    assert travel == {
        Path("Vocabulary/Food.pdf"),
        Path("Grammar/Asking for directions.pdf"),
    }

    exam = paths_with_tag(tree, "C1 exam", kind=CHARACTER_PHONETIC)
    assert exam == {Path("Grammar/Asking for directions.pdf")}

    nothing = paths_with_tag(tree, "nonexistent", kind=CHARACTER_PHONETIC)
    assert nothing == set()


async def test_unfiltered_lists_all_notebook_pdfs(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        labels = _labels(pilot.app.screen)
        assert set(labels) == {"Vocabulary/Food.pdf", "Grammar/Asking for directions.pdf"}


async def test_filename_filter_ranks_via_fuzzy(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        pilot.app.screen.query_one("#query").value = "Food"
        await pilot.pause()
        labels = _labels(pilot.app.screen)
        assert labels[0] == "Vocabulary/Food.pdf"


async def test_tag_filter_excludes_untagged_and_uncompiled(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        pilot.app.screen.query_one("#tag-filter").value = "C1 exam"
        await pilot.pause()
        labels = _labels(pilot.app.screen)
        assert labels == ["Grammar/Asking for directions.pdf"]


async def test_combined_filename_and_tag_filter(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        # "Vocabulary/Food" isn't a fuzzy subsequence of the other candidate,
        # so this genuinely tests the filename+tag intersection rather than
        # relying on both filters happening to admit everything.
        pilot.app.screen.query_one("#query").value = "Vocabulary/Food"
        pilot.app.screen.query_one("#tag-filter").value = "travel"
        await pilot.pause()
        labels = _labels(pilot.app.screen)
        assert labels == ["Vocabulary/Food.pdf"]


async def test_no_matches_shows_empty_state(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        pilot.app.screen.query_one("#tag-filter").value = "nonexistent"
        await pilot.pause()
        assert _labels(pilot.app.screen) == []
        assert pilot.app.screen.query_one("#empty-state", Static).display is True
        assert pilot.app.screen.query_one("#results", OptionList).display is False


async def test_capital_l_from_results_panel_does_nothing(tree):
    # L is a printable character, so it only switches panels when focus
    # starts outside any Input (a focused Input intercepts it as a keystroke
    # instead - see test_shift_left_from_input_does_not_switch_panel for
    # that case). One panel, so there's nowhere to switch to.
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        results = pilot.app.screen.query_one("#results", OptionList)
        results.focus()
        await pilot.pause()

        await pilot.press("L")
        await pilot.pause()
        assert pilot.app.focused is results


async def test_shift_left_from_input_does_not_switch_panel(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        tag_filter = pilot.app.screen.query_one("#tag-filter")
        tag_filter.focus()
        await pilot.pause()

        await pilot.press("shift+left")
        await pilot.pause()
        assert pilot.app.focused is tag_filter


async def test_opening_focuses_filename_filter(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)
        assert pilot.app.focused is query


async def test_panels_stack_query_then_results_then_tag(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        query_panel = pilot.app.screen.query_one("#query-panel", Panel)
        results_panel = pilot.app.screen.query_one("#results-panel", Panel)
        tag_panel = pilot.app.screen.query_one("#tag-panel", Panel)
        assert query_panel.region.y < results_panel.region.y < tag_panel.region.y


async def test_escape_from_filename_filter_focuses_panel(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#query-panel", Panel)
        assert pilot.app.focused is panel


async def test_escape_from_tag_filter_focuses_panel(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)
        tag_filter.focus()
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#tag-panel", Panel)
        assert pilot.app.focused is panel


# -- M3 · Search by content: three panels makes the backpanel reachable ----


async def test_escape_twice_from_query_reaches_the_backpanel(tree):
    # With three panels now (M3), "esc" a second time climbs to the
    # backpanel instead of staying put — unlike the old single-panel
    # Browse, where a second escape did nothing (there was nowhere to go).
    from vimdiomas.tui.screens.panels import Backpanel

    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#query-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel


async def test_j_k_move_between_the_three_panels(tree):
    # J/K only engage once a Panel (not its content) has focus -- escape up
    # to it first, same as any other panel-move key.
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("J")
        await pilot.pause()
        results = pilot.app.screen.query_one("#results", OptionList)
        assert pilot.app.focused is results

        await pilot.press("escape")
        await pilot.pause()
        await pilot.press("J")
        await pilot.pause()
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)
        assert pilot.app.focused is tag_filter


async def test_q_from_a_filter_field_types_q(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)
        tag_filter.focus()
        await pilot.pause()

        await pilot.press("q")
        await pilot.pause()
        assert tag_filter.value == "q"


async def test_q_from_results_pops_the_screen(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        results = pilot.app.screen.query_one("#results", OptionList)
        results.focus()
        await pilot.pause()
        screens_before = len(pilot.app.screen_stack)
        await pilot.press("q")
        await pilot.pause()
        assert len(pilot.app.screen_stack) == screens_before - 1


async def test_opening_highlights_the_first_result(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        results = pilot.app.screen.query_one("#results", OptionList)
        assert results.highlighted == 0


async def test_filtering_highlights_the_first_result(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        pilot.app.screen.query_one("#query").value = "Food"
        await pilot.pause()
        results = pilot.app.screen.query_one("#results", OptionList)
        assert results.highlighted == 0


# -- M3 · Search by content: tab toggles the mode --------------------------


async def test_opening_starts_in_filename_mode(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        badge = pilot.app.screen.query_one("#mode-badge", Static)
        assert str(badge.render()) == "FILENAME MODE"
        assert badge.has_class("mode-filename")
        query = pilot.app.screen.query_one("#query", Input)
        assert query.placeholder == "Filter by filename"


@pytest.mark.parametrize("focus_id", ["query", "tag-filter", "results"])
async def test_tab_toggles_mode_and_keeps_focus(tree, focus_id):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        focused = pilot.app.screen.query_one(f"#{focus_id}")
        focused.focus()
        await pilot.pause()

        await pilot.press("tab")
        await pilot.pause()

        badge = pilot.app.screen.query_one("#mode-badge", Static)
        assert str(badge.render()) == "CONTENT MODE"
        assert badge.has_class("mode-content")
        query = pilot.app.screen.query_one("#query", Input)
        assert query.placeholder == "Search entries and categories"
        footer = pilot.app.screen.query_one("#footer-hint", Static)
        assert "search by filename" in str(footer.render())
        if focus_id != "results":
            # The results list is empty in content mode (no query typed
            # yet), so it cannot keep focus (next test covers that case).
            assert pilot.app.focused is focused


async def test_tab_from_results_into_an_empty_mode_focuses_query(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        results = pilot.app.screen.query_one("#results", OptionList)
        results.focus()
        await pilot.pause()

        await pilot.press("tab")
        await pilot.pause()

        query = pilot.app.screen.query_one("#query", Input)
        assert pilot.app.focused is query


async def test_tab_on_a_focused_panel_focuses_content_instead_of_toggling(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        await pilot.press("tab")
        await pilot.pause()

        badge = pilot.app.screen.query_one("#mode-badge", Static)
        assert str(badge.render()) == "FILENAME MODE"
        query = pilot.app.screen.query_one("#query", Input)
        assert pilot.app.focused is query


async def test_query_text_is_kept_across_a_mode_toggle(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        query = pilot.app.screen.query_one("#query", Input)
        query.value = "你好"
        await pilot.pause()

        await pilot.press("tab")
        await pilot.pause()

        assert pilot.app.screen.query_one("#query", Input).value == "你好"


async def test_reopening_browse_starts_in_filename_mode_again(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.screen.mode == "content"

        pilot.app.pop_screen()
        await pilot.pause()
        pilot.app.push_screen(BrowseScreen(tree, kind=CHARACTER_PHONETIC))
        await pilot.pause()
        assert pilot.app.screen.mode == "filename"


# -- M3 · Search by content: enter moves between fields ---------------------


async def test_enter_in_query_focuses_results_when_present(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        results = pilot.app.screen.query_one("#results", OptionList)
        assert pilot.app.focused is results


async def test_enter_in_query_focuses_tag_filter_without_results(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        query = pilot.app.screen.query_one("#query", Input)
        query.value = "nothing matches this"
        await pilot.pause()
        query.focus()
        await pilot.pause()

        await pilot.press("enter")
        await pilot.pause()
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)
        assert pilot.app.focused is tag_filter


async def test_enter_in_tag_filter_does_nothing_with_results(tree):
    # The tag field is the last panel, so there is no next one to move to.
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)
        tag_filter.focus()
        await pilot.pause()

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused is tag_filter


async def test_enter_in_tag_filter_does_nothing_without_results(tree):
    app = _HostApp(tree)
    async with app.run_test() as pilot:
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)
        tag_filter.value = "nonexistent"
        await pilot.pause()
        tag_filter.focus()
        await pilot.pause()

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused is tag_filter


async def test_selecting_a_result_opens_it(tree):
    app = _HostApp(tree)
    with patch("vimdiomas.tui.screens.browse.open_file") as mock_open_file:
        async with app.run_test() as pilot:
            results = pilot.app.screen.query_one("#results", OptionList)
            results.focus()
            results.highlighted = results.options.index(results.get_option("Vocabulary/Food.pdf"))
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            mock_open_file.assert_called_once_with(tree / "Vocabulary" / "Food.pdf")


# -- Sprint 6 M2 · #16: bracket text is text, not markup -------------------


async def test_bracket_filenames_are_listed_literally(tmp_path):
    tree_root = tmp_path / "tree"
    tree_root.mkdir()
    (tree_root / "[b]x.md").write_text("# [b]x\n", encoding="utf-8")
    (tree_root / "[b]x.pdf").write_bytes(b"%PDF fake")
    app = _HostApp(tree_root)
    async with app.run_test() as pilot:
        results = pilot.app.screen.query_one("#results", OptionList)
        # What is drawn, not just what is stored: an OptionList parses a `str`
        # prompt as markup at render time.
        visual = results._get_visual(results.get_option_at_index(0))
        assert str(visual) == "[b]x.pdf"


async def test_paths_with_tag_in_a_german_tree(tmp_path):
    """Sprint 6 M6: Browse takes the notebook's kind, so a German file's
    two-column rows are not read as stray lines on the way to its tags."""
    (tmp_path / "Vocabulary").mkdir()
    (tmp_path / "Vocabulary" / "Essen.md").write_text(
        "# Essen\n\nHaus\thouse\n\n## Tags\n\n#food\n", encoding="utf-8"
    )
    assert paths_with_tag(tmp_path, "food", kind=ALPHABETICAL) == {Path("Vocabulary/Essen.pdf")}


# -- M3 · Search by content: format_row() / hit_fields() / hit_location() --


def _hit(**kwargs) -> ContentHit:
    defaults = dict(kind="entry", source=Path("Vocabulary/x.md"), file_label="Vocabulary/x")
    defaults.update(kwargs)
    return ContentHit(**defaults)


def test_format_row_fits_whole():
    row = format_row(["你好", "nǐhǎo", "hola"], "Vocabulary/Saludos › Saludos", 60)
    assert str(row) == "你好  nǐhǎo  hola               Vocabulary/Saludos › Saludos"


def test_format_row_cuts_the_longest_field_first():
    row = format_row(["aaaaaaaaaa", "b"], "X", 10)
    assert str(row) == "aaa…  b  X"


def test_format_row_cuts_location_from_the_left_once_fields_are_at_minimum():
    row = format_row(["aaaaaaaaaa", "bbbbbbbbbb"], "deeplocationname", 10)
    text = str(row)
    assert cell_len(text) <= 10
    assert text.startswith("a…  b…")
    assert "…" in text[text.index("  ", 6) :]  # the location itself was cut too


def test_format_row_hanzi_counts_as_two_cells_not_one_character():
    row = format_row(["番茄番茄番茄番茄番茄", "一些翻译文字"], "Vocabulary/Food › Fruits", 40)
    assert cell_len(str(row)) == 40


def test_format_row_brackets_are_literal():
    row = format_row(["[b]x"], "Vocabulary/x", 40)
    assert "[b]x" in str(row)


@pytest.mark.parametrize("width", range(8, 121))
def test_format_row_never_exceeds_width(width):
    fields = [
        "你好你好你好你好你好你好你好你好你好你好",
        "nǐhǎonǐhǎonǐhǎonǐhǎonǐhǎonǐhǎo",
        "a rather long translation that keeps going and going",
    ]
    location = "Grammar/Some long file name here › Some Category › Some Subtitle"
    assert cell_len(str(format_row(fields, location, width))) <= width


def test_hit_fields_chinese_entry_tone_marks_and_drops_empty_translation():
    hit = _hit(word="你好", reading="ni3hao3", translation="")
    assert hit_fields(hit, CHARACTER_PHONETIC) == ["你好", "nǐhǎo"]


def test_hit_fields_alphabetical_entry_has_no_reading():
    hit = _hit(word="Haus", translation="house")
    assert hit_fields(hit, ALPHABETICAL) == ["Haus", "house"]


def test_hit_fields_category_and_subtitle_are_bare_names():
    category = _hit(kind="category", name="Saludos")
    subtitle = _hit(kind="subtitle", name="copulative conjunction")
    assert hit_fields(category, CHARACTER_PHONETIC) == ["Saludos"]
    assert hit_fields(subtitle, CHARACTER_PHONETIC) == ["copulative conjunction"]


def test_hit_style_is_bold_for_categories_and_subtitles_only():
    category = _hit(kind="category", name="Saludos")
    subtitle = _hit(kind="subtitle", name="copulative conjunction")
    entry = _hit(kind="entry", word="你好", translation="hola")
    assert hit_style(category) == "bold"
    assert hit_style(subtitle) == "bold"
    assert hit_style(entry) == ""


def test_format_row_style_covers_fields_not_location():
    row = format_row(["Saludos"], "Vocabulary/Food", 40, style="bold")
    spans = {(span.start, span.end, span.style) for span in row.spans}
    assert (0, len("Saludos"), "bold") in spans
    assert all(span.style != "bold" or span.end <= len("Saludos") for span in row.spans)
    assert any(span.style == "dim" for span in row.spans)


def test_hit_location_variants():
    uncategorized = _hit(file_label="Vocabulary/Repaso clase 2")
    assert hit_location(uncategorized) == "Vocabulary/Repaso clase 2"

    under_category = _hit(file_label="Vocabulary/Saludos", category="Saludos")
    assert hit_location(under_category) == "Vocabulary/Saludos › Saludos"

    category_row = _hit(kind="category", file_label="Vocabulary/Saludos", name="Saludos")
    assert hit_location(category_row) == "Vocabulary/Saludos"

    subtitle_row = _hit(
        kind="subtitle", file_label="Grammar/Conjunctions", category="Linking words",
        name="copulative conjunction",
    )
    assert hit_location(subtitle_row) == "Grammar/Conjunctions › Linking words"

    under_subtitle = _hit(
        file_label="Grammar/Conjunctions", category="Linking words",
        subtitle="copulative conjunction",
    )
    assert hit_location(under_subtitle) == "Grammar/Conjunctions › Linking words › copulative conjunction"


# -- M3 · Search by content: content mode in Browse -------------------------


@pytest.fixture
def content_tree(tmp_path):
    root = tmp_path / "tree-Chinese"
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
    (vocab / "Saludos.pdf").write_bytes(b"%PDF fake")
    # Conjunctions.md deliberately left uncompiled.
    return root


async def test_empty_query_shows_the_content_hint(content_tree):
    app = _HostApp(content_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        empty = pilot.app.screen.query_one("#empty-state", Static)
        assert empty.display is True
        assert "Type to search" in str(empty.render())
        assert pilot.app.screen.query_one("#results", OptionList).display is False


async def test_content_mode_hanzi_pinyin_and_translation_find_the_same_entry(content_tree):
    app = _HostApp(content_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)

        for text in ("你好", "nihao", "hola"):
            query.value = text
            await pilot.pause()
            labels = _labels(pilot.app.screen)
            assert any("你好" in label and "nǐhǎo" in label and "hola" in label for label in labels), (
                text,
                labels,
            )


async def test_content_mode_category_and_subtitle_rows(content_tree):
    app = _HostApp(content_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)

        query.value = "salu"
        await pilot.pause()
        assert any("Saludos" in label for label in _labels(pilot.app.screen))

        query.value = "copulative"
        await pilot.pause()
        assert any("copulative conjunction" in label for label in _labels(pilot.app.screen))


async def test_content_mode_no_matches(content_tree):
    app = _HostApp(content_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)
        query.value = "xyznonexistent"
        await pilot.pause()

        assert _labels(pilot.app.screen) == []
        empty = pilot.app.screen.query_one("#empty-state", Static)
        assert empty.display is True
        assert str(empty.render()) == "No matches."


async def test_content_mode_tag_filter_limits_hits(content_tree):
    app = _HostApp(content_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)
        tag_filter = pilot.app.screen.query_one("#tag-filter", Input)

        query.value = "ni"
        tag_filter.value = "greeting"
        await pilot.pause()
        assert any("你好" in label for label in _labels(pilot.app.screen))

        tag_filter.value = "nonexistent"
        await pilot.pause()
        assert _labels(pilot.app.screen) == []


async def test_enter_on_an_entry_result_opens_its_compiled_pdf(content_tree):
    app = _HostApp(content_tree)
    with patch("vimdiomas.tui.screens.base.open_file") as mock_open_file:
        async with app.run_test() as pilot:
            await pilot.press("tab")
            await pilot.pause()
            query = pilot.app.screen.query_one("#query", Input)
            query.value = "你好"
            await pilot.pause()

            results = pilot.app.screen.query_one("#results", OptionList)
            results.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            mock_open_file.assert_called_once_with(content_tree / "Vocabulary" / "Saludos.pdf")


async def test_enter_on_an_uncompiled_result_compiles_then_opens(content_tree, monkeypatch):
    compile_calls = []

    def _fake_compile(src, dst, **kwargs):
        compile_calls.append((src, dst))
        dst.write_bytes(b"%PDF-fake")

    monkeypatch.setattr("vimdiomas.tui.screens.base.compile_file", _fake_compile)

    app = _HostApp(content_tree)
    with patch("vimdiomas.tui.screens.base.open_file") as mock_open_file:
        async with app.run_test() as pilot:
            await pilot.press("tab")
            await pilot.pause()
            query = pilot.app.screen.query_one("#query", Input)
            query.value = "copulative"
            await pilot.pause()

            results = pilot.app.screen.query_one("#results", OptionList)
            results.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            md_path = content_tree / "Grammar" / "Conjunctions.md"
            pdf_path = content_tree / "Grammar" / "Conjunctions.pdf"
            assert compile_calls == [(md_path, pdf_path)]
            mock_open_file.assert_called_once_with(pdf_path)


async def test_enter_on_a_result_from_a_file_that_fails_to_compile_notifies(content_tree, monkeypatch):
    import subprocess

    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda *a, **kw: (_ for _ in ()).throw(
            subprocess.CalledProcessError(43, ["pandoc"], stderr=b"! boom\n")
        ),
    )

    app = _HostApp(content_tree)
    with patch("vimdiomas.tui.screens.base.open_file") as mock_open_file:
        async with app.run_test() as pilot:
            await pilot.press("tab")
            await pilot.pause()
            query = pilot.app.screen.query_one("#query", Input)
            query.value = "copulative"
            await pilot.pause()

            results = pilot.app.screen.query_one("#results", OptionList)
            results.focus()
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

            mock_open_file.assert_not_called()
            [note] = [n for n in pilot.app._notifications if n.severity == "error"]
            assert "Conjunctions.md" in note.message


async def test_content_mode_bracket_row_shows_literal_brackets(tmp_path):
    root = tmp_path / "tree"
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Brackets.md").write_text("# Brackets\n\n[b]x\tzi4\ttranslation\n", encoding="utf-8")

    app = _HostApp(root)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)
        query.value = "[b]x"
        await pilot.pause()

        results = pilot.app.screen.query_one("#results", OptionList)
        visual = results._get_visual(results.get_option_at_index(0))
        assert "[b]x" in str(visual)


async def test_german_tree_content_mode_word_and_translation(tmp_path):
    root = tmp_path / "tree-German"
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Essen.md").write_text(
        "# Essen\n\nÜber\tabout\n\n## Essen\n\nHaus\thouse\n", encoding="utf-8"
    )

    app = _HostApp(root, kind=ALPHABETICAL)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        query = pilot.app.screen.query_one("#query", Input)

        for text in ("Über", "about", "uber"):
            query.value = text
            await pilot.pause()
            labels = _labels(pilot.app.screen)
            assert any("Über" in label and "about" in label for label in labels), (text, labels)

        query.value = "essen"
        await pilot.pause()
        assert any("Essen" in label for label in _labels(pilot.app.screen))
