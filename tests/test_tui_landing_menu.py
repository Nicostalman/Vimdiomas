import pytest

from vimdiomas.config import Config, LanguageConfig
from vimdiomas.tui.app import VimdiomasApp
from vimdiomas.tui.screens.landing import LandingMenuScreen, SettingsScreen
from vimdiomas.tui.screens.main_menu import MainMenuScreen
from vimdiomas.tui.screens.placeholder import PlaceholderScreen


@pytest.fixture
def config(tmp_path):
    config = Config(
        user_name="Nico",
        root=tmp_path,
        languages=[LanguageConfig(name="Chinese"), LanguageConfig(name="German")],
    )
    config.tree_root("Chinese").mkdir()
    return config


async def _select(pilot, index):
    option_list = pilot.app.screen.query_one("OptionList")
    option_list.highlighted = index
    await pilot.press("enter")
    await pilot.pause()


async def test_landing_menu_shows_three_items_in_order(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        option_list = pilot.app.screen.query_one("OptionList")
        labels = [str(option.prompt) for option in option_list._options]
        assert labels == ["Chinese notebook", "German notebook", "Settings"]


async def test_chinese_notebook_shows_main_menu(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, MainMenuScreen)


async def test_german_notebook_opens_the_notebook_menu(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _select(pilot, 1)
        assert isinstance(pilot.app.screen, MainMenuScreen)
        assert pilot.app.screen.language == "German"


async def test_menu_options_come_from_config_languages(tmp_path):
    # Only one language registered — the menu must reflect that, not a
    # hardcoded Chinese/German pair.
    config = Config(
        user_name="Nico", root=tmp_path, languages=[LanguageConfig(name="Chinese")]
    )
    config.tree_root("Chinese").mkdir()

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        option_list = pilot.app.screen.query_one("OptionList")
        labels = [str(option.prompt) for option in option_list._options]
        assert labels == ["Chinese notebook", "Settings"]


async def test_q_on_settings_returns_to_landing_menu(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _select(pilot, 2)
        assert isinstance(pilot.app.screen, SettingsScreen)
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, LandingMenuScreen)


async def test_q_on_landing_menu_exits_the_app(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await pilot.press("q")
        await pilot.pause()
        assert not pilot.app.is_running


async def test_jk_move_landing_menu_highlight(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
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
        await pilot.pause()
        option_list = pilot.app.screen.query_one("OptionList")
        assert pilot.app.focused is option_list


async def test_escape_on_the_list_does_nothing(config):
    # Dev feedback, hands-on: a menu has nothing to gain by climbing to the
    # backpanel, so escape leaves focus on the list — unlike Browse, which
    # has a real panel and does climb.
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await pilot.pause()
        option_list = pilot.app.screen.query_one("OptionList")
        assert pilot.app.focused is option_list

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is option_list


async def test_shift_hjkl_do_nothing(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await pilot.pause()
        option_list = pilot.app.screen.query_one("OptionList")

        for key in ("H", "L", "K", "J"):
            await pilot.press(key)
            await pilot.pause()
            assert pilot.app.focused is option_list


# -- Sprint 6 M4: the legend -------------------------------------------------


async def _legend_texts(pilot, count):
    from vimdiomas.tui.screens.base import MenuLegend

    legend = pilot.app.screen.query_one(MenuLegend)
    shown = [str(legend.render())]
    for _ in range(count - 1):
        await pilot.press("j")
        await pilot.pause()
        shown.append(str(legend.render()))
    return shown


async def test_landing_legend_describes_each_option_as_it_is_highlighted(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        assert await _legend_texts(pilot, 3) == [
            "Add words, explore and compile your Chinese notes.",
            "Add words, explore and compile your German notes.",
            "Input methods, and adding or removing a language.",
        ]


# -- Sprint 6 M5: a language that isn't in the registry --------------------


async def test_an_unregistered_language_is_listed_and_opens_the_placeholder(tmp_path):
    """A hand-edited config can name a language the registry doesn't know. It
    is treated as a language that isn't functional yet, never as an error."""
    config = Config(
        user_name="Nico", root=tmp_path, languages=[LanguageConfig(name="Klingon")]
    )

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        option_list = pilot.app.screen.query_one("OptionList")
        assert str(option_list._options[0].prompt) == "Klingon notebook"
        assert await _legend_texts(pilot, 1) == ["Not available yet."]
        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, PlaceholderScreen)
