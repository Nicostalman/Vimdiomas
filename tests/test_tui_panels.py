from pathlib import Path

import pytest
from textual.app import App, ComposeResult
from textual.containers import Horizontal

from vimdiomas.tui.screens.base import literal
from vimdiomas.tui.screens.panels import (
    Backpanel,
    MenuOption,
    MenuScreen,
    Panel,
    PanelScreen,
    SelectField,
    TextField,
)

APP_TCSS = Path(__file__).parent.parent / "src" / "vimdiomas" / "tui" / "app.tcss"


class _HostScreen(PanelScreen):
    """Three panels: left and right side by side, one spanning below.

    Left is wider than right so a tie between them (equal edge distance
    from "below", which spans both) breaks towards left — the geometry a
    real screen with an all-disabled panel would also have to cope with.
    """

    CSS = """
    #left { width: 70%; }
    #right { width: 30%; }
    """

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Horizontal():
                with Panel(id="left"):
                    yield TextField(id="left-field")
                with Panel(id="right"):
                    yield TextField(id="right-field")
            with Panel(id="below"):
                yield TextField(id="below-field", disabled=True)


class _HostApp(App):
    def on_mount(self) -> None:
        self.push_screen(_HostScreen())


async def test_opening_focuses_first_panels_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_escape_climbs_content_then_panel_then_backpanel_then_stays():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        await pilot.press("escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is backpanel


async def test_enter_on_backpanel_lands_in_first_panels_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_enter_on_a_panel_lands_in_its_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_h_from_backpanel_focuses_leftmost_panel_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel

        await pilot.press("H")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_l_from_backpanel_focuses_rightmost_panel_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "escape")
        await pilot.pause()

        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused.id == "right-field"


async def test_k_from_backpanel_focuses_topmost_panel_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "escape")
        await pilot.pause()

        # left and right are both topmost (y=0); ties break towards leftmost
        await pilot.press("K")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_j_from_backpanel_focuses_bottommost_panel():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "escape")
        await pilot.pause()

        await pilot.press("shift+down")
        await pilot.pause()
        # below-field is disabled, so its panel is the landing spot
        assert pilot.app.focused.id == "below"


async def test_tab_on_a_panel_focuses_its_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_shift_right_from_left_panel_lands_in_right_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused.id == "right-field"


async def test_shift_right_from_right_panel_does_nothing():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "shift+right", "escape")
        await pilot.pause()
        assert pilot.app.focused.id == "right"

        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused.id == "right"


async def test_shift_left_from_right_panel_lands_in_left_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "shift+right", "escape")
        await pilot.pause()
        assert pilot.app.focused.id == "right"

        await pilot.press("shift+left")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_shift_left_from_left_panel_does_nothing():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        await pilot.press("shift+left")
        await pilot.pause()
        assert pilot.app.focused.id == "left"


async def test_shift_down_from_left_panel_lands_on_below_panel():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        await pilot.press("shift+down")
        await pilot.pause()
        # below-field is disabled, so its panel is the landing spot
        assert pilot.app.focused.id == "below"


async def test_shift_up_from_below_panel_lands_on_left_content():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "shift+down")
        await pilot.pause()
        assert pilot.app.focused.id == "below"

        await pilot.press("shift+up")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_shift_left_and_right_from_below_panel_do_nothing():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "shift+down")
        await pilot.pause()
        assert pilot.app.focused.id == "below"

        await pilot.press("shift+left")
        await pilot.pause()
        assert pilot.app.focused.id == "below"

        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused.id == "below"


async def test_shift_hjkl_inert_while_content_has_focus():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"

        await pilot.press("shift+right")
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"


async def test_capital_h_typed_into_a_field_is_text():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"

        await pilot.press("H")
        await pilot.pause()
        assert pilot.app.screen.query_one("#left-field", TextField).value == "H"
        assert pilot.app.focused.id == "left-field"


async def test_landing_on_an_all_disabled_panel_focuses_the_panel():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape", "shift+down")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#below", Panel)
        assert pilot.app.focused is panel


async def test_q_from_a_panel_pops_the_screen():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "left"

        screens_before = len(pilot.app.screen_stack)
        await pilot.press("q")
        await pilot.pause()
        assert len(pilot.app.screen_stack) == screens_before - 1


async def test_q_types_into_a_focused_field():
    app = _HostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "left-field"

        await pilot.press("q")
        await pilot.pause()
        assert pilot.app.screen.query_one("#left-field", TextField).value == "q"
        assert pilot.app.focused.id == "left-field"


class _FlatHostScreen(PanelScreen):
    """A backpanel with no `Panel` children at all — the flat-menu case
    (Sprint 4 M2): content sits directly inside the backpanel."""

    def compose(self) -> ComposeResult:
        with Backpanel():
            yield TextField(id="content-field")


class _FlatHostApp(App):
    def on_mount(self) -> None:
        self.push_screen(_FlatHostScreen())


async def test_flat_opening_focuses_content_directly():
    app = _FlatHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "content-field"


async def test_flat_escape_on_content_does_nothing():
    # Dev feedback, hands-on: a flat screen (a menu) has nothing to gain by
    # climbing to the backpanel — no second panel to reach from there — so
    # escape leaves focus on the content, unlike escape from a real panel's
    # content (which does focus the backpanel).
    app = _FlatHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        field = pilot.app.screen.query_one("#content-field", TextField)
        assert pilot.app.focused is field

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is field


async def test_flat_escape_on_backpanel_does_nothing():
    # The backpanel is never reached via escape in a flat screen, but its
    # own escape guard is still a no-op if focus ever lands on it directly.
    app = _FlatHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        backpanel.focus()
        await pilot.pause()
        assert pilot.app.focused is backpanel

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is backpanel


async def test_flat_enter_from_backpanel_refocuses_content():
    app = _FlatHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        backpanel.focus()
        await pilot.pause()
        assert pilot.app.focused is backpanel

        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.focused.id == "content-field"


async def test_flat_tab_from_backpanel_refocuses_content():
    app = _FlatHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        backpanel.focus()
        await pilot.pause()
        assert pilot.app.focused is backpanel

        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "content-field"


async def test_flat_shift_hjkl_are_no_ops():
    app = _FlatHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        backpanel.focus()
        await pilot.pause()
        assert pilot.app.focused is backpanel

        for key in ("H", "L", "K", "J"):
            await pilot.press(key)
            await pilot.pause()
            assert pilot.app.focused is backpanel


class _SinglePanelHostScreen(PanelScreen):
    """One panel — the Browse/Inspect Tree shape: escape from it should
    reach the panel from content, but never climb past it to the
    backpanel, since there's nothing else to jump to from there."""

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(id="only"):
                yield TextField(id="only-field")


class _SinglePanelHostApp(App):
    def on_mount(self) -> None:
        self.push_screen(_SinglePanelHostScreen())


async def test_single_panel_escape_from_content_focuses_panel():
    app = _SinglePanelHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "only-field"

        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#only", Panel)
        assert pilot.app.focused is panel


async def test_single_panel_escape_from_panel_does_nothing():
    app = _SinglePanelHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#only", Panel)
        assert pilot.app.focused is panel

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused is panel


async def test_single_panel_backpanel_not_reachable():
    app = _SinglePanelHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert not backpanel.reachable()


class _MenuHostScreen(MenuScreen):
    def menu_options(self):
        return [MenuOption("One", "First.", id="one"), MenuOption("Two", "Second.", id="two")]


class _MenuHostApp(App):
    def on_mount(self) -> None:
        self.push_screen(_MenuHostScreen())


async def test_menu_tab_does_not_defocus_the_option_list():
    # Dev feedback, hands-on: with the OptionList as the only focusable
    # content, Textual's default tab-cycling moved focus onto the
    # Backpanel itself (also can_focus=True), visibly defocusing the list
    # for no reason. MenuScreen binds `tab` to a no-op to prevent this.
    app = _MenuHostApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        option_list = pilot.app.screen.query_one("OptionList")
        assert pilot.app.focused is option_list

        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused is option_list


# --- SelectField (Sprint 4 M6) -------------------------------------------

CHOICES = [
    ("a", "Alpha  (a)"),
    ("b", "Beta  (b)"),
    ("c", "Gamma  (c)"),
]


class _SelectHostScreen(PanelScreen):
    """One panel holding a select field and a text field below it, so a
    collapsed `esc` and a blur both have somewhere real to go."""

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(id="only"):
                yield SelectField(
                    "Choice",
                    CHOICES,
                    value="b",
                    short_labels={"a": "Alpha", "b": "Beta", "c": "Gamma"},
                    id="choice",
                )
                yield TextField(id="after")


class _SelectHostApp(App):
    def on_mount(self) -> None:
        self.push_screen(_SelectHostScreen())


async def test_select_field_starts_collapsed_showing_its_value():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        assert not field.expanded
        assert "Choice: Beta" in str(
            pilot.app.screen.query_one("#choice-display").content
        )


async def test_enter_expands_and_focuses_the_list():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert field.expanded
        assert pilot.app.focused.id == "choice-list"


async def test_the_list_opens_on_the_current_value():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.screen.query_one("#choice-list").highlighted == 1


async def test_choosing_sets_the_value_and_collapses():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j", "enter")
        await pilot.pause()
        assert field.value == "c"
        assert not field.expanded
        assert pilot.app.focused.id == "choice"


async def test_escape_on_the_open_list_collapses_without_changing_the_value():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j")
        await pilot.pause()

        await pilot.press("escape")
        await pilot.pause()

        assert field.value == "b"
        assert not field.expanded
        # The field, not the panel: `esc` climbs exactly one rung.
        assert pilot.app.focused.id == "choice"


async def test_escape_on_the_collapsed_field_reaches_the_panel():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        pilot.app.screen.query_one("#choice", SelectField).focus()
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "only"


async def test_focus_leaving_an_open_field_collapses_it():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert field.expanded

        pilot.app.screen.query_one("#after").focus()
        await pilot.pause()
        await pilot.pause()

        assert not field.expanded
        assert field.value == "b"


# --- SelectField.set_choices / Changed (Sprint 5 M5) ----------------------


async def test_set_choices_replaces_options_and_resets_value():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.set_choices([("x", "Xray"), ("y", "Yankee")], value="x")

        assert field.value == "x"
        assert "Choice: Xray" in str(pilot.app.screen.query_one("#choice-display").content)

        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        option_list = pilot.app.screen.query_one("#choice-list")
        assert [str(option_list.get_option_at_index(i).prompt) for i in range(option_list.option_count)] == [
            "Xray",
            "Yankee",
        ]


async def test_choosing_an_option_posts_changed_not_setting_value_in_code():
    app = _SelectHostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        posted = []
        original_post_message = field.post_message

        def _spy(message):
            if isinstance(message, SelectField.Changed):
                posted.append(message.value)
            return original_post_message(message)

        field.post_message = _spy

        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j", "enter")
        await pilot.pause()

        assert posted == ["c"]

        posted.clear()
        field.value = "a"  # setting in code posts nothing
        await pilot.pause()
        assert posted == []


# --- Screen real estate: overflow scrollbars and scroll-into-view (M1) ----


class _TallHostScreen(PanelScreen):
    """One panel holding more fields than a short terminal can show at
    once, so it overflows — the Entry-form-panel shape."""

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(id="only"):
                for i in range(20):
                    yield TextField(id=f"field-{i}")


class _TallHostApp(App):
    CSS_PATH = APP_TCSS

    def on_mount(self) -> None:
        self.push_screen(_TallHostScreen())


class _ShortHostScreen(PanelScreen):
    """Few enough fields to fit any terminal used in these tests."""

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(id="only"):
                for i in range(3):
                    yield TextField(id=f"field-{i}")


class _ShortHostApp(App):
    CSS_PATH = APP_TCSS

    def on_mount(self) -> None:
        self.push_screen(_ShortHostScreen())


async def test_panel_shows_no_scrollbar_when_content_fits():
    app = _ShortHostApp()
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause()
        panel = pilot.app.screen.query_one("#only", Panel)
        assert panel.max_scroll_y == 0
        assert not panel.show_vertical_scrollbar


async def test_panel_shows_a_scrollbar_when_content_overflows():
    app = _TallHostApp()
    async with app.run_test(size=(80, 10)) as pilot:
        await pilot.pause()
        panel = pilot.app.screen.query_one("#only", Panel)
        assert panel.max_scroll_y > 0
        assert panel.show_vertical_scrollbar


async def test_tabbing_to_an_offscreen_field_scrolls_it_into_view():
    app = _TallHostApp()
    async with app.run_test(size=(80, 10)) as pilot:
        await pilot.pause()
        panel = pilot.app.screen.query_one("#only", Panel)
        assert panel.scroll_y == 0

        last_field = pilot.app.screen.query_one("#field-19", TextField)
        last_field.focus()
        await pilot.pause()
        await pilot.pause()

        assert panel.scroll_y > 0
        assert last_field.region.y >= panel.content_region.y
        assert (
            last_field.region.y + last_field.region.height
            <= panel.content_region.y + panel.content_region.height
        )


async def test_a_panel_shorter_than_one_row_does_not_crash():
    app = _TallHostApp()
    async with app.run_test(size=(80, 3)) as pilot:
        await pilot.pause()
        panel = pilot.app.screen.query_one("#only", Panel)
        assert panel is not None


async def test_a_backpanel_with_many_panels_scrolls_and_focus_follows():
    class _ManyPanelsScreen(PanelScreen):
        def compose(self) -> ComposeResult:
            with Backpanel():
                for i in range(15):
                    with Panel(id=f"panel-{i}"):
                        yield TextField(id=f"field-{i}")

    class _ManyPanelsApp(App):
        CSS_PATH = APP_TCSS

        def on_mount(self) -> None:
            self.push_screen(_ManyPanelsScreen())

    app = _ManyPanelsApp()
    async with app.run_test(size=(80, 10)) as pilot:
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert backpanel.max_scroll_y > 0
        assert backpanel.show_vertical_scrollbar

        last_field = pilot.app.screen.query_one("#field-14", TextField)
        last_field.focus()
        await pilot.pause()
        await pilot.pause()

        assert backpanel.scroll_y > 0


async def test_navigation_model_unchanged_on_a_small_overflowing_panel():
    # A scrollbar must never become a focus stop, and shift+hjkl/escape
    # behave exactly as they do without overflow.
    app = _TallHostApp()
    async with app.run_test(size=(80, 10)) as pilot:
        await pilot.pause()
        assert pilot.app.focused.id == "field-0"

        await pilot.press("escape")
        await pilot.pause()
        assert pilot.app.focused.id == "only"

        await pilot.press("escape")
        await pilot.pause()
        # Single panel: escape from the panel does not reach the backpanel.
        assert pilot.app.focused.id == "only"


async def test_a_field_with_no_choices_never_expands():
    """A machine with no enabled input sources: the field shows the empty
    text and `enter` does nothing rather than opening an empty list."""

    class _EmptyScreen(PanelScreen):
        def compose(self) -> ComposeResult:
            with Backpanel():
                with Panel(id="only"):
                    yield SelectField("Choice", [], id="choice")

    class _EmptyApp(App):
        def on_mount(self) -> None:
            self.push_screen(_EmptyScreen())

    app = _EmptyApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#choice", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert not field.expanded
        assert "(none available)" in str(
            pilot.app.screen.query_one("#choice-display").content
        )


# -- Sprint 6 M1 · #15: a field sanitises its own control characters -------


async def test_pasted_tab_becomes_a_space_in_the_field():
    """The report's reproduction, at the widget: a spreadsheet row pasted into
    a field carried its tab straight into the triad row and shifted its
    columns. A space, not a deletion, so `苹果` and `apple` stay two words."""
    app = _HostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#left-field", TextField)
        field.value = "苹果\tapple"
        await pilot.pause()
        assert field.value == "苹果 apple"


async def test_every_control_character_becomes_a_space():
    app = _HostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#left-field", TextField)
        field.value = "a\tb\nc\rd\x00e\x1bf\x7fg"
        await pilot.pause()
        assert field.value == "a b c d e f g"


async def test_ordinary_text_and_edge_spaces_are_untouched():
    app = _HostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#left-field", TextField)
        field.value = "  ping2 guo3  "
        await pilot.pause()
        assert field.value == "  ping2 guo3  "


async def test_typed_tab_never_reaches_the_value_and_keeps_the_cursor_put():
    """One character for one, so the cursor doesn't move under the typist."""
    app = _HostApp()
    async with app.run_test() as pilot:
        field = pilot.app.screen.query_one("#left-field", TextField)
        field.focus()
        await pilot.pause()
        field.insert_text_at_cursor("苹果\tapple")
        await pilot.pause()
        assert field.value == "苹果 apple"
        assert field.cursor_position == len("苹果 apple")


async def test_changed_message_carries_the_sanitised_value():
    """Sanitising through the reactive's own validation hook means every
    listener — Entry's hanzi → pinyin auto-fill among them — sees the cleaned
    value, whatever order the messages arrive in."""
    seen: list[str] = []

    class _Screen(_HostScreen):
        def on_input_changed(self, event) -> None:
            seen.append(event.value)

    class _App(App):
        def on_mount(self) -> None:
            self.push_screen(_Screen())

    app = _App()
    async with app.run_test() as pilot:
        pilot.app.screen.query_one("#left-field", TextField).value = "a\tb"
        await pilot.pause()
        assert seen == ["a b"]


# -- Sprint 6 M2 · #16: literal() ------------------------------------------


@pytest.mark.parametrize(
    "text", ["to [/] test", "Verbs [/x]", "[b]x[/b]", "a\\[b]", "trail\\", "[@click=app.quit]x"]
)
def test_literal_draws_exactly_what_it_was_given(text):
    # The screen tests check what widgets draw; this is the helper itself.
    assert literal(text).plain == text
