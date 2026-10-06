"""The menu legend (Sprint 6 M4): `MenuOption`, `MenuLegend`, and what
`MenuScreen` does with them. Uses a test-only menu so the shared behaviour is
pinned independently of any real menu's wording."""

import pytest
from textual.app import App
from textual.widgets.option_list import Option

from vimdiomas.config import Config, LanguageConfig
from vimdiomas.tui.app import VimdiomasApp
from vimdiomas.tui.screens.base import MenuLegend
from vimdiomas.tui.screens.landing import LandingMenuScreen
from vimdiomas.tui.screens.main_menu import MainMenuScreen
from vimdiomas.tui.screens.panels import MenuOption, MenuScreen
from vimdiomas.tui.screens.settings import InputMethodLanguagesScreen, SettingsScreen

ONE_LINE = "Short."
TWO_LINES = "A description long enough that it needs a second line to fit."


class _TestMenu(MenuScreen):
    options: list = []

    def menu_options(self):
        return type(self).options


class _TestApp(App):
    CSS_PATH = VimdiomasApp.CSS_PATH

    def __init__(self, screen):
        super().__init__()
        self._screen = screen

    def on_mount(self):
        self.push_screen(self._screen)


def _menu(*descriptions, cls=_TestMenu):
    menu_cls = type("Menu", (cls,), {"options": [
        MenuOption(f"Item {i}", text, id=f"item{i}") for i, text in enumerate(descriptions)
    ]})
    return menu_cls()


def _text(legend):
    return str(legend.render())


async def test_the_legend_shows_the_first_description_on_open():
    app = _TestApp(_menu(ONE_LINE, TWO_LINES))
    async with app.run_test() as pilot:
        await pilot.pause()
        assert _text(pilot.app.screen.query_one(MenuLegend)) == ONE_LINE


async def test_j_and_k_change_the_legend():
    app = _TestApp(_menu(ONE_LINE, TWO_LINES))
    async with app.run_test() as pilot:
        await pilot.pause()
        legend = pilot.app.screen.query_one(MenuLegend)
        await pilot.press("j")
        await pilot.pause()
        assert _text(legend) == TWO_LINES
        await pilot.press("k")
        await pilot.pause()
        assert _text(legend) == ONE_LINE


async def test_the_legend_is_two_rows_and_the_list_never_moves():
    app = _TestApp(_menu(ONE_LINE, TWO_LINES))
    async with app.run_test() as pilot:
        await pilot.pause()
        screen = pilot.app.screen
        legend = screen.query_one(MenuLegend)
        option_list = screen.query_one("OptionList")
        one_line = (legend.region.height, option_list.region, legend.region)
        await pilot.press("j")
        await pilot.pause()
        two_lines = (legend.region.height, option_list.region, legend.region)
        assert one_line[0] == two_lines[0] == 2
        assert one_line[1] == two_lines[1]
        assert one_line[2] == two_lines[2]


async def test_a_plain_option_is_refused():
    menu_cls = type("Menu", (_TestMenu,), {"options": [Option("Plain", id="plain")]})
    app = _TestApp(menu_cls())
    with pytest.raises(TypeError, match="Menu"):
        async with app.run_test() as pilot:
            await pilot.pause()


async def test_a_description_is_shown_verbatim():
    app = _TestApp(_menu("Use [b]x[/b] here."))
    async with app.run_test() as pilot:
        await pilot.pause()
        assert _text(pilot.app.screen.query_one(MenuLegend)) == "Use [b]x[/b] here."


async def test_the_legend_never_takes_focus_and_tab_does_nothing():
    app = _TestApp(_menu(ONE_LINE, TWO_LINES))
    async with app.run_test() as pilot:
        await pilot.pause()
        option_list = pilot.app.screen.query_one("OptionList")
        assert not pilot.app.screen.query_one(MenuLegend).can_focus
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused is option_list


# -- every real menu ---------------------------------------------------------


@pytest.fixture
def config(tmp_path):
    config = Config(
        user_name="Nico",
        root=tmp_path,
        languages=[LanguageConfig(name="Chinese"), LanguageConfig(name="German")],
    )
    config.tree_root("Chinese").mkdir()
    return config


async def test_every_option_on_every_menu_has_a_legend_that_fits_two_lines(config):
    # The legend's width is 40 with 2 columns of padding each side.

    text_width = 36
    app = VimdiomasApp(config)
    seen = 0
    async with app.run_test() as pilot:
        for screen in (
            LandingMenuScreen(),
            MainMenuScreen("Chinese"),
            SettingsScreen(),
            InputMethodLanguagesScreen(),
        ):
            await pilot.app.push_screen(screen)
            await pilot.pause()
            option_list = screen.query_one("OptionList")
            legend = screen.query_one(MenuLegend)
            for index, option in enumerate(option_list._options):
                option_list.highlighted = index
                await pilot.pause()
                shown = _text(legend)
                assert shown == option.description
                assert shown.strip()
                assert _wrapped_lines(shown, text_width) <= 2, (type(screen).__name__, shown)
                seen += 1
    assert seen == 3 + 4 + 3 + 2


def _wrapped_lines(text: str, width: int) -> int:
    from textwrap import wrap

    return len(wrap(text, width))
