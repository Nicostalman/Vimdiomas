from unittest.mock import patch

import pytest

from vimdiomas.compile import CompileReport
from vimdiomas.config import Config, LanguageConfig
from vimdiomas.languages import CHARACTER_PHONETIC
from vimdiomas.tui.app import VimdiomasApp
from vimdiomas.tui.screens.browse import BrowseScreen
from vimdiomas.tui.screens.entry import EntryScreen
from vimdiomas.tui.screens.inspect import InspectTreeScreen
from vimdiomas.tui.screens.landing import LandingMenuScreen
from vimdiomas.tui.screens.main_menu import MainMenuScreen
from vimdiomas.tui.screens.placeholder import PlaceholderScreen


@pytest.fixture
def config(tmp_path):
    config = Config(
        user_name="Nico", root=tmp_path, languages=[LanguageConfig(name="Chinese")]
    )
    config.tree_root("Chinese").mkdir()
    return config


async def _select(pilot, index):
    option_list = pilot.app.screen.query_one("OptionList")
    option_list.highlighted = index
    await pilot.press("enter")
    await pilot.pause()


async def _open_notebook_menu(pilot):
    await _select(pilot, 0)  # Chinese notebook, on the landing menu


async def test_menu_shows_four_items_in_order(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        option_list = pilot.app.screen.query_one("OptionList")
        labels = [str(option.prompt) for option in option_list._options]
        assert labels == ["Enter vocabulary", "Inspect tree", "Browse", "Compile"]
        assert "compile_force" not in [option.id for option in option_list._options]


async def test_enter_vocabulary_shows_entry_screen(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, EntryScreen)


async def test_browse_shows_browse_screen(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        await _select(pilot, 2)
        assert isinstance(pilot.app.screen, BrowseScreen)


async def test_inspect_tree_shows_inspect_tree_screen(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        await _select(pilot, 1)
        assert isinstance(pilot.app.screen, InspectTreeScreen)
        assert pilot.app.screen.tree_root == config.tree_root("Chinese")


async def test_compile_calls_compile_all_and_shows_result(config):
    app = VimdiomasApp(config)
    with patch(
        "vimdiomas.tui.screens.main_menu.compile_all",
        return_value=CompileReport(compiled=[config.tree_root("Chinese") / "Food.pdf"]),
    ) as mock_compile:
        async with app.run_test() as pilot:
            await _open_notebook_menu(pilot)
            await _select(pilot, 3)
            mock_compile.assert_called_once_with(
                config.tree_root("Chinese"), kind=CHARACTER_PHONETIC, force=False
            )
            assert isinstance(pilot.app.screen, PlaceholderScreen)
            assert "Food.pdf" in pilot.app.screen.message


async def test_compile_shows_up_to_date_when_nothing_compiled(config):
    app = VimdiomasApp(config)
    with patch("vimdiomas.tui.screens.main_menu.compile_all", return_value=CompileReport()):
        async with app.run_test() as pilot:
            await _open_notebook_menu(pilot)
            await _select(pilot, 3)
            assert str(pilot.app.screen.message) == "Everything is up to date."


async def test_q_from_placeholder_returns_to_main_menu(config):
    app = VimdiomasApp(config)
    with patch("vimdiomas.tui.screens.main_menu.compile_all", return_value=CompileReport()):
        async with app.run_test() as pilot:
            await _open_notebook_menu(pilot)
            await _select(pilot, 3)
            assert isinstance(pilot.app.screen, PlaceholderScreen)
            await pilot.press("q")
            await pilot.pause()
            assert isinstance(pilot.app.screen, MainMenuScreen)


async def test_q_on_main_menu_returns_to_landing_menu(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, LandingMenuScreen)
        assert pilot.app.is_running


async def test_jk_move_main_menu_highlight(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        option_list = pilot.app.screen.query_one("OptionList")
        assert option_list.highlighted == 0
        await pilot.press("j")
        await pilot.pause()
        assert option_list.highlighted == 1
        await pilot.press("k")
        await pilot.pause()
        assert option_list.highlighted == 0


async def test_opening_focuses_the_list(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        option_list = pilot.app.screen.query_one("OptionList")
        assert pilot.app.focused is option_list


async def test_escape_on_the_list_does_nothing(config):
    # Dev feedback, hands-on: a menu has nothing to gain by climbing to the
    # backpanel, so escape leaves focus on the list — unlike Browse, which
    # has a real panel and does climb.
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        option_list = pilot.app.screen.query_one("OptionList")
        assert pilot.app.focused is option_list

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is option_list


async def test_shift_hjkl_do_nothing(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        option_list = pilot.app.screen.query_one("OptionList")

        for key in ("H", "L", "K", "J"):
            await pilot.press(key)
            await pilot.pause()
            assert pilot.app.focused is option_list


# -- Sprint 6 M4: one Compile, and the legend ------------------------------


async def test_notebook_menu_legend_follows_the_highlight(config):
    from vimdiomas.tui.screens.base import MenuLegend

    expected = [
        "Add a word or a grammar point to a file, under a category.",
        "Walk your files: preview them, open in Neovim, rename, delete.",
        "Fuzzy-find a file by name, or filter by tag.",
        "Rebuild the PDFs of files changed since their last compile.",
    ]
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        legend = pilot.app.screen.query_one(MenuLegend)
        shown = [str(legend.render())]
        for _ in expected[1:]:
            await pilot.press("j")
            await pilot.pause()
            shown.append(str(legend.render()))
        assert shown == expected


async def test_menu_compile_picks_up_an_edit_made_outside_the_app(
    config, monkeypatch
):
    import vimdiomas.compile as compile_module

    monkeypatch.setattr(compile_module, "CACHE_PATH", config.root / "cache.json")
    vocab = config.tree_root("Chinese") / "Vocabulary"
    vocab.mkdir()
    source = vocab / "Food.md"
    source.write_text("# Food\n\n字\tzi4\tchar\n", encoding="utf-8")
    monkeypatch.setattr(
        compile_module, "_run_pandoc", lambda markdown, dst, kind: dst.write_bytes(b"%PDF")
    )

    async def _compile(pilot):
        await _select(pilot, 3)
        shown = str(pilot.app.screen.query_one("Static").render())
        await pilot.press("q")
        await pilot.pause()
        return shown

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        assert "Food.pdf" in await _compile(pilot)

        # As Neovim would: the file changes on disk, no autocompile involved.
        source.write_text("# Food\n\n字\tzi4\tcharacter\n", encoding="utf-8")
        assert "Food.pdf" in await _compile(pilot)

        assert await _compile(pilot) == "Everything is up to date."


# -- Sprint 6 M2 · #12: a compile failure is reported, not fatal -----------


async def test_compile_with_a_failing_file_reports_it_and_stays_up(config, monkeypatch):
    import subprocess

    import vimdiomas.compile as compile_module

    monkeypatch.setattr(compile_module, "CACHE_PATH", config.root / "cache.json")
    vocab = config.tree_root("Chinese") / "Vocabulary"
    vocab.mkdir()
    (vocab / "Good.md").write_text("# Good\n\n字\tzi4\tchar\n", encoding="utf-8")
    (vocab / "Bad [i].md").write_text("# Bad [i]\n\n字\tzi4\tchar\n", encoding="utf-8")

    def _fake(markdown, dst, kind):
        if dst.stem == "Bad [i]":
            raise subprocess.CalledProcessError(
                43, ["pandoc"], stderr=b"! Undefined control sequence.\nl.9 \\\\[0.4em]\n"
            )
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr(compile_module, "_run_pandoc", _fake)

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        await _select(pilot, 3)

        assert pilot.app.is_running
        assert isinstance(pilot.app.screen, PlaceholderScreen)
        shown = str(pilot.app.screen.query_one("Static").render())
        assert "Good.pdf" in shown
        assert "Failed:" in shown
        assert "Bad [i].md" in shown
        assert "! Undefined control sequence." in shown
        assert "l.9 \\\\[0.4em]" in shown
        assert (vocab / "Good.pdf").exists()
        assert str(vocab / "Good.md") in compile_module._load_cache()
        assert str(vocab / "Bad [i].md") not in compile_module._load_cache()


def test_compile_summary_lists_warnings_below_failures():
    from pathlib import Path

    from vimdiomas.compile import CompileFailure, CompileReport, CompileWarning
    from vimdiomas.tui.screens.main_menu import compile_summary

    report = CompileReport(
        compiled=[Path("/t/Good.pdf")],
        failed=[CompileFailure(Path("/t/Bad.md"), "! Undefined control sequence.")],
        warnings=[CompileWarning(Path("/t/Odd.md"), "printed without a tone mark: x4")],
    )
    summary = compile_summary(report)

    assert summary.index("Failed:") < summary.index("Warnings:")
    assert "Warnings:\n/t/Odd.md\n    printed without a tone mark: x4" in summary


def test_an_up_to_date_tree_still_shows_its_warnings():
    from pathlib import Path

    from vimdiomas.compile import CompileReport, CompileWarning
    from vimdiomas.tui.screens.main_menu import compile_summary

    report = CompileReport(warnings=[CompileWarning(Path("/t/Odd.md"), "x4")])
    summary = compile_summary(report)

    assert summary.startswith("Everything is up to date.")
    assert "Warnings:" in summary


async def test_opening_a_notebook_menu_completes_its_tree(tmp_path):
    """Sprint 6 M6: a tree with only `Vocabulary/` (the dev's `tree-German`,
    from before the folders were automatic) gets `Grammar/` when opened."""
    config = Config(
        user_name="Nico", root=tmp_path, languages=[LanguageConfig(name="German")]
    )
    (config.tree_root("German") / "Vocabulary").mkdir(parents=True)

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_notebook_menu(pilot)
        assert isinstance(pilot.app.screen, MainMenuScreen)

    assert (config.tree_root("German") / "Grammar").is_dir()
    assert (config.tree_root("German") / "Vocabulary").is_dir()


async def test_compile_in_one_notebook_touches_only_that_notebooks_tree(tmp_path, monkeypatch):
    """With two languages configured, a notebook menu's Compile builds that
    language's tree alone — it neither parses nor compiles the other's, and
    gives its own kind (Sprint 6 M6)."""
    import vimdiomas.compile as compile_module
    from vimdiomas.languages import ALPHABETICAL

    config = Config(
        user_name="Nico",
        root=tmp_path,
        languages=[LanguageConfig(name="Chinese"), LanguageConfig(name="German")],
    )
    monkeypatch.setattr(compile_module, "CACHE_PATH", tmp_path / "cache.json")
    chinese = config.tree_root("Chinese") / "Vocabulary"
    german = config.tree_root("German") / "Vocabulary"
    chinese.mkdir(parents=True)
    german.mkdir(parents=True)
    (chinese / "Food.md").write_text("# Food\n\n字\tzi4\tchar\n", encoding="utf-8")
    (german / "Essen.md").write_text("# Essen\n\nHaus\thouse\n", encoding="utf-8")

    built = []
    monkeypatch.setattr(
        compile_module,
        "_run_pandoc",
        lambda markdown, dst, kind: (built.append((dst.name, kind)), dst.write_bytes(b"%PDF")),
    )
    rendered = []
    original = compile_module.render_source
    monkeypatch.setattr(
        compile_module,
        "render_source",
        lambda source, **kwargs: (rendered.append(source), original(source, **kwargs))[1],
    )

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _select(pilot, 1)  # German notebook
        await _select(pilot, 3)  # Compile
        shown = str(pilot.app.screen.query_one("Static").render())

    assert built == [("Essen.pdf", ALPHABETICAL)]
    assert rendered == [german / "Essen.md"]
    assert "Essen.pdf" in shown and "Food" not in shown
    assert not (chinese / "Food.pdf").exists()


# -- Sprint 6 M9: several warnings for one file are grouped under it --------


def test_compile_summary_groups_a_files_warnings_under_one_path():
    from pathlib import Path

    from vimdiomas.compile import CompileReport, CompileWarning
    from vimdiomas.tui.screens.main_menu import compile_summary

    odd = Path("/t/Odd.md")
    report = CompileReport(
        warnings=[
            CompileWarning(odd, "line 5: unrecognized line: | a | b |"),
            CompileWarning(odd, "line 7: an entry with no word: \tni3\tyou"),
            CompileWarning(Path("/t/Other.md"), "no '# Other' header line"),
        ]
    )
    summary = compile_summary(report)

    assert summary.count("/t/Odd.md") == 1
    assert (
        "Warnings:\n/t/Odd.md\n"
        "    line 5: unrecognized line: | a | b |\n"
        "    line 7: an entry with no word: \tni3\tyou\n"
        "/t/Other.md\n"
        "    no '# Other' header line"
    ) in summary


def test_compile_summary_indents_every_line_of_a_warning():
    from pathlib import Path

    from vimdiomas.compile import CompileReport, CompileWarning
    from vimdiomas.tui.screens.main_menu import compile_summary

    report = CompileReport(warnings=[CompileWarning(Path("/t/Odd.md"), "first\nsecond")])

    assert "/t/Odd.md\n    first\n    second" in compile_summary(report)
