"""Settings and what is real under it: input methods (Sprint 4 M6), adding a
language (Sprint 6 M7) and removing one (Sprint 6 M8)."""

import pytest

from vimdiomas.config import Config, LanguageConfig, load_config
from vimdiomas.platform import InputSource
from vimdiomas.tui.app import VimdiomasApp
from vimdiomas.tui.screens.input_methods import (
    LANGUAGE_FIELD_ID,
    NO_SOURCES_MESSAGE,
    ONE_SOURCE_MESSAGE,
    TRANSLATION_FIELD_ID,
)
from vimdiomas.tui.screens.panels import SelectField
from vimdiomas.tui.screens.placeholder import PlaceholderScreen
from vimdiomas import doctor
from vimdiomas.tui.screens.base import ConfirmDialog
from vimdiomas.tui.screens.landing import LandingMenuScreen
from vimdiomas.tui.screens.main_menu import MainMenuScreen
from vimdiomas.tui.screens.settings import (
    AddLanguageFormScreen,
    AddLanguageScreen,
    InputMethodLanguagesScreen,
    InputMethodSettingsScreen,
    RemoveLanguageScreen,
    SettingsScreen,
)

HANZI = "com.apple.inputmethod.SCIM.ITABC"
ENGLISH = "com.apple.keylayout.USInternational-PC"
GERMAN = "com.apple.keylayout.German"

SOURCES = [
    InputSource(id=ENGLISH, name="U.S. International – PC"),
    InputSource(id=HANZI, name="Pinyin – Simplified"),
    InputSource(id=GERMAN, name="German"),
]


@pytest.fixture(autouse=True)
def sources(monkeypatch):
    """Every test drives a fixed source list: the real one depends on the
    machine's own keyboards."""
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources", lambda: list(SOURCES)
    )


def _all_ok():
    return [
        doctor.Check("pandoc", "pandoc", required=True, ok=True),
        doctor.Check("xeCJK", "xecjk", required=False, ok=True, needed_for=("Chinese",)),
    ]


@pytest.fixture(autouse=True)
def dependencies_ok(monkeypatch):
    """Every dependency present, unless a test says otherwise: the real answer
    depends on the machine running the tests."""
    monkeypatch.setattr(doctor, "run", _all_ok)


@pytest.fixture
def config(tmp_path, monkeypatch):
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", tmp_path / "config.toml")
    config = Config(
        user_name="Nico",
        root=tmp_path,
        languages=[
            LanguageConfig(
                name="Chinese",
                input_method=HANZI,
                translation_input_method=ENGLISH,
            ),
            LanguageConfig(name="German"),
        ],
    )
    config.tree_root("Chinese").mkdir()
    return config


async def _select(pilot, index):
    option_list = pilot.app.screen.query_one("OptionList")
    option_list.highlighted = index
    await pilot.press("enter")
    await pilot.pause()


async def _open_settings(pilot):
    # Settings is always the landing menu's last option.
    await _select(pilot, pilot.app.screen.query_one("OptionList").option_count - 1)


async def test_settings_lists_its_three_options(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        assert isinstance(pilot.app.screen, SettingsScreen)
        option_list = pilot.app.screen.query_one("OptionList")
        labels = [str(option.prompt) for option in option_list._options]
        assert labels == ["Input methods", "Add a language", "Remove a language"]


async def test_input_methods_lists_the_registered_languages(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, InputMethodLanguagesScreen)
        option_list = pilot.app.screen.query_one("OptionList")
        labels = [str(option.prompt) for option in option_list._options]
        assert labels == ["Chinese", "German"]


async def test_fields_open_prefilled_from_the_config(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 0)
        screen = pilot.app.screen
        assert isinstance(screen, InputMethodSettingsScreen)
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == HANZI
        assert screen.query_one(f"#{TRANSLATION_FIELD_ID}", SelectField).value == ENGLISH


async def test_an_unconfigured_language_preselects_rather_than_blanking(config):
    """German has nothing stored; the fields must still land on a real
    choice rather than showing empty — the dev's "it should have a default
    setting"."""
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 1)
        screen = pilot.app.screen
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == GERMAN
        assert screen.query_one(f"#{TRANSLATION_FIELD_ID}", SelectField).value == ENGLISH


async def test_saving_writes_the_config_and_updates_the_running_app(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 0)
        screen = pilot.app.screen

        field = screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField)
        field.focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("j", "enter")
        await pilot.pause()
        assert field.value == GERMAN

        screen.query_one("#save-button").focus()
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, InputMethodLanguagesScreen)
        # In the running app, so the next Entry screen picks it up with no
        # relaunch — the whole reason this screen exists.
        assert pilot.app.config.language("Chinese").input_method == GERMAN
        # And on disk.
        assert load_config().language("Chinese").input_method == GERMAN


async def test_one_source_warns_and_uses_it_for_both_fields(config, monkeypatch):
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources",
        lambda: [InputSource(id=ENGLISH, name="U.S. International – PC")],
    )
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 1)
        screen = pilot.app.screen
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == ENGLISH
        assert screen.query_one(f"#{TRANSLATION_FIELD_ID}", SelectField).value == ENGLISH
        assert ONE_SOURCE_MESSAGE in str(screen.query(".wizard-advisory").first().content)


async def test_no_sources_warns_and_stores_nothing(config, monkeypatch):
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources", lambda: []
    )
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 1)
        screen = pilot.app.screen
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == ""
        assert NO_SOURCES_MESSAGE in str(screen.query(".wizard-advisory").first().content)


async def test_tab_cycles_the_two_fields_and_the_button(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 0)
        assert pilot.app.focused.id == LANGUAGE_FIELD_ID
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == TRANSLATION_FIELD_ID
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "save-button"
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == LANGUAGE_FIELD_ID


async def test_q_leaves_without_saving(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        await _select(pilot, 0)
        field = pilot.app.screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField)
        field.value = GERMAN

        await pilot.press("q")
        await pilot.pause()

        assert isinstance(pilot.app.screen, InputMethodLanguagesScreen)
        assert pilot.app.config.language("Chinese").input_method == HANZI


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


async def test_settings_legend_describes_each_option(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        assert await _legend_texts(pilot, 3) == [
            "Choose which keyboard each language is typed with.",
            "Start a notebook for another language.",
            "Stop using a language. Its notes are kept unless you ask.",
        ]


async def test_input_methods_picker_legend_names_the_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await _select(pilot, 0)
        assert await _legend_texts(pilot, 2) == [
            "Change the keyboards used for Chinese.",
            "Change the keyboards used for German.",
        ]


# -- Sprint 6 M7: Add a language ---------------------------------------------

ADD_LANGUAGE = 1  # Settings' second option


def _labels(pilot):
    return [str(option.prompt) for option in pilot.app.screen.query_one("OptionList")._options]


async def _open_add_picker(pilot):
    await _open_settings(pilot)
    await _select(pilot, ADD_LANGUAGE)


async def _open_add_form(pilot, index=0):
    await _open_add_picker(pilot)
    await _select(pilot, index)


async def _press_add(pilot):
    pilot.app.screen.query_one("#add-button").focus()
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


async def test_the_picker_lists_exactly_the_unregistered_languages(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_picker(pilot)
        assert isinstance(pilot.app.screen, AddLanguageScreen)
        assert _labels(pilot) == ["Italian", "French", "English", "Spanish"]


async def test_the_picker_legend_names_the_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_picker(pilot)
        assert await _legend_texts(pilot, 2) == [
            "Start a notebook for Italian.",
            "Start a notebook for French.",
        ]


async def test_with_every_language_registered_it_says_so(tmp_path, monkeypatch):
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", tmp_path / "config.toml")
    from vimdiomas.languages import LANGUAGES

    config = Config(
        user_name="Nico",
        root=tmp_path,
        languages=[LanguageConfig(name=language.name) for language in LANGUAGES],
    )
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_picker(pilot)
        assert isinstance(pilot.app.screen, PlaceholderScreen)
        assert str(pilot.app.screen.query_one("Static").render()) == (
            "Every supported language is already added."
        )


async def test_the_form_asks_the_wizards_question_with_the_wizards_fields(config):
    from vimdiomas.tui.screens.input_methods import INPUT_METHOD_PROMPT
    from vimdiomas.tui.screens.wizard import InputMethodScreen

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        screen = pilot.app.screen
        assert isinstance(screen, AddLanguageFormScreen)
        texts = [str(static.render()) for static in screen.query("Static")]
        assert "Add a language · Italian" in texts
        assert INPUT_METHOD_PROMPT in texts
        assert pilot.app.focused.id == LANGUAGE_FIELD_ID
        # The wizard's step shows the same constant, not its own copy.
        import inspect

        assert "INPUT_METHOD_PROMPT" in inspect.getsource(InputMethodScreen)


async def test_the_form_preselects_the_languages_own_layout(config, monkeypatch):
    italian = "com.apple.keylayout.Italian"
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources",
        lambda: [*SOURCES, InputSource(id=italian, name="Italian")],
    )
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        screen = pilot.app.screen
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == italian


async def test_tab_cycles_the_two_fields_and_the_add_button(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        seen = [pilot.app.focused.id]
        for _ in range(3):
            await pilot.press("tab")
            await pilot.pause()
            seen.append(pilot.app.focused.id)
        assert seen == [LANGUAGE_FIELD_ID, TRANSLATION_FIELD_ID, "add-button", LANGUAGE_FIELD_ID]


async def test_adding_italian_writes_the_folder_and_the_config(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)

        tree = config.tree_root("Italian")
        assert (tree / "Vocabulary").is_dir()
        assert (tree / "Grammar").is_dir()
        assert load_config().language("Italian") is not None
        assert [entry.name for entry in load_config().languages] == [
            "Chinese",
            "German",
            "Italian",
        ]
        assert [entry.name for entry in pilot.app.config.languages] == [
            "Chinese",
            "German",
            "Italian",
        ]


async def test_the_answers_are_stored_with_the_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        expected = (GERMAN, ENGLISH)  # preselection: German layout, then the first plain one
        await _press_add(pilot)
        entry = load_config().language("Italian")
        # Italian has no layout in SOURCES, so the first source is preselected.
        assert (entry.input_method, entry.translation_input_method) == (
            ENGLISH,
            GERMAN,
        ) or (entry.input_method, entry.translation_input_method) == expected


async def test_adding_returns_to_settings_with_a_notification(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert [n.message for n in pilot.app._notifications] == ["Italian added."]


async def test_the_new_language_reaches_the_landing_menu_without_relaunching(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)
        await pilot.press("q")
        await pilot.pause()

        assert isinstance(pilot.app.screen, LandingMenuScreen)
        assert _labels(pilot) == [
            "Chinese notebook",
            "German notebook",
            "Italian notebook",
            "Settings",
        ]
        await _select(pilot, 2)
        assert isinstance(pilot.app.screen, MainMenuScreen)
        assert pilot.app.screen.language == "Italian"


async def test_the_landing_highlight_stays_on_the_same_option(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)
        await pilot.press("q")
        await pilot.pause()
        # Settings was highlighted when it was opened, and still is, though
        # its index moved from 2 to 3.
        option_list = pilot.app.screen.query_one("OptionList")
        assert option_list.highlighted_option.id == "settings"


async def test_input_methods_lists_the_new_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)
        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, InputMethodLanguagesScreen)
        assert _labels(pilot) == ["Chinese", "German", "Italian"]


async def test_the_added_language_leaves_the_picker(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)
        await _select(pilot, ADD_LANGUAGE)
        assert isinstance(pilot.app.screen, AddLanguageScreen)
        assert _labels(pilot) == ["French", "English", "Spanish"]


async def test_an_existing_tree_folder_is_adopted_untouched(config):
    tree = config.tree_root("Italian")
    (tree / "Vocabulary").mkdir(parents=True)
    note = tree / "Vocabulary" / "Cibo.md"
    note.write_text("# Cibo\n")
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)

        assert note.read_text() == "# Cibo\n"
        assert (tree / "Grammar").is_dir()
        assert pilot.app.config.language("Italian") is not None


async def test_a_failed_save_shows_the_error_and_changes_nothing(config, monkeypatch):
    def failing_save(config):
        raise OSError("disk full")

    monkeypatch.setattr("vimdiomas.tui.screens.settings.save_config", failing_save)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)

        screen = pilot.app.screen
        assert isinstance(screen, AddLanguageFormScreen)
        error = screen.query_one("#add-language-error")
        assert error.display
        assert "disk full" in str(error.render())
        assert [entry.name for entry in pilot.app.config.languages] == ["Chinese", "German"]


async def test_a_failed_save_can_be_retried(config, monkeypatch):
    from vimdiomas.tui.screens import settings

    real_save = settings.save_config
    attempts = []

    def flaky_save(config):
        attempts.append(1)
        if len(attempts) == 1:
            raise OSError("disk full")
        real_save(config)

    monkeypatch.setattr(settings, "save_config", flaky_save)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await _press_add(pilot)
        assert isinstance(pilot.app.screen, AddLanguageFormScreen)
        # A button ignores a second press while it is still showing the first
        # (Textual's ~0.2s active state).
        await pilot.pause(0.4)
        await _press_add(pilot)
        assert isinstance(pilot.app.screen, SettingsScreen)
        assert pilot.app.config.language("Italian") is not None


async def test_q_on_the_form_adds_nothing(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_add_form(pilot)
        await pilot.press("q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, AddLanguageScreen)
        assert not config.tree_root("Italian").exists()
        assert [entry.name for entry in pilot.app.config.languages] == ["Chinese", "German"]


@pytest.fixture
def german_only(tmp_path, monkeypatch):
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", tmp_path / "config.toml")
    return Config(user_name="Nico", root=tmp_path, languages=[LanguageConfig(name="German")])


def _chinese_needs_xecjk():
    return [
        doctor.Check("pandoc", "pandoc", required=True, ok=True),
        doctor.Check("xeCJK", "xecjk", required=False, ok=False, needed_for=("Chinese",)),
    ]


@pytest.fixture(autouse=True)
def _platform_can_install(monkeypatch):
    """The offer, with the platform able to install everything and its package
    manager present: the real answer depends on the machine running the tests."""
    from vimdiomas.tui.screens import dependencies

    monkeypatch.setattr(dependencies.platform, "installable", lambda key: True)
    monkeypatch.setattr(dependencies.platform, "package_manager_available", lambda: True)


async def test_adding_a_non_chinese_language_never_asks_about_xecjk(german_only, monkeypatch):
    monkeypatch.setattr(doctor, "run", _chinese_needs_xecjk)
    app = VimdiomasApp(german_only)
    async with app.run_test() as pilot:
        await _select(pilot, 1)  # Settings
        await _select(pilot, ADD_LANGUAGE)
        assert _labels(pilot) == ["Chinese", "Italian", "French", "English", "Spanish"]
        await _select(pilot, 1)  # Italian
        await _press_add(pilot)
        assert isinstance(pilot.app.screen, SettingsScreen)


async def test_adding_chinese_without_xecjk_goes_through_the_offer(german_only, monkeypatch):
    from vimdiomas.tui.screens import dependencies

    installs = []
    states = [_chinese_needs_xecjk, _all_ok]

    def run():
        return (states.pop(0) if len(states) > 1 else states[0])()

    monkeypatch.setattr(doctor, "run", run)
    monkeypatch.setattr(
        dependencies.installer,
        "run",
        lambda app, checks: installs.append([check.key for check in checks]),
    )
    app = VimdiomasApp(german_only)
    async with app.run_test() as pilot:
        await _select(pilot, 1)  # Settings
        await _select(pilot, ADD_LANGUAGE)
        await _select(pilot, 0)  # Chinese
        await _press_add(pilot)
        assert isinstance(pilot.app.screen, ConfirmDialog)
        await pilot.press("y")
        await pilot.pause()

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert pilot.app.config.language("Chinese") is not None
    assert installs == [["xecjk"]]


async def test_declining_the_offer_adds_nothing_and_says_what_is_missing(german_only, monkeypatch):
    monkeypatch.setattr(doctor, "run", _chinese_needs_xecjk)
    app = VimdiomasApp(german_only)
    async with app.run_test() as pilot:
        await _select(pilot, 1)  # Settings
        await _select(pilot, ADD_LANGUAGE)
        await _select(pilot, 0)  # Chinese
        await _press_add(pilot)
        await pilot.press("n")
        await pilot.pause()

        screen = pilot.app.screen
        assert isinstance(screen, AddLanguageFormScreen)
        error = str(screen.query_one("#add-language-error").render())
        assert "Chinese needs xeCJK, which is missing." in error
        assert "tlmgr" not in error and "`" not in error
        assert pilot.app.config.language("Chinese") is None
        assert not german_only.tree_root("Chinese").exists()


# -- Sprint 6 M8: Remove a language ------------------------------------------

REMOVE_LANGUAGE = 2  # Settings' third option
CHINESE, GERMAN_ROW = 0, 1  # the picker's rows, in config order


async def _open_remove_picker(pilot):
    await _open_settings(pilot)
    await _select(pilot, REMOVE_LANGUAGE)


async def _answer(pilot, key):
    await pilot.press(key)
    await pilot.pause()


async def _remove(pilot, row, *answers):
    """Open the picker, choose `row`, then give each answer in turn."""
    await _open_remove_picker(pilot)
    await _select(pilot, row)
    for key in answers:
        await _answer(pilot, key)


def _dialog_text(pilot):
    return str(pilot.app.screen.query_one("Static").render())


def _notices(pilot):
    return [n.message for n in pilot.app._notifications]


def _give_chinese_notes(config, cache_too=True):
    """A file and a PDF in Chinese's tree, and cache entries for it and for
    German and for a prefix-sharing sibling."""
    from vimdiomas import compile as compile_module

    vocabulary = config.tree_root("Chinese") / "Vocabulary"
    vocabulary.mkdir()
    note = vocabulary / "Food.md"
    note.write_text("# Food\n")
    pdf = vocabulary / "Food.pdf"
    pdf.write_bytes(b"%PDF")
    if cache_too:
        compile_module._save_cache(
            {
                str(note): "chinese",
                str(config.root / "tree-German" / "Essen.md"): "german",
                str(config.root / "tree-Chinese2" / "Food.md"): "sibling",
            }
        )
    return note, pdf


async def test_the_picker_lists_the_registered_languages_in_config_order(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_remove_picker(pilot)
        assert isinstance(pilot.app.screen, RemoveLanguageScreen)
        assert _labels(pilot) == ["Chinese", "German"]
        assert await _legend_texts(pilot, 2) == [
            "Remove Chinese. You'll be asked about its notes.",
            "Remove German. You'll be asked about its notes.",
        ]


async def test_the_picker_lists_a_name_outside_the_registry(config):
    config.languages.append(LanguageConfig(name="Klingon"))
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_remove_picker(pilot)
        assert _labels(pilot) == ["Chinese", "German", "Klingon"]


async def test_the_first_dialog_names_the_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_remove_picker(pilot)
        await _select(pilot, CHINESE)
        assert isinstance(pilot.app.screen, ConfirmDialog)
        assert _dialog_text(pilot) == (
            "Remove Chinese from Vimdiomas? It leaves the main menu and Settings."
        )


@pytest.mark.parametrize("key", ["n", "escape"])
async def test_declining_the_first_dialog_changes_nothing(config, key):
    note, _ = _give_chinese_notes(config)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, key)

        assert isinstance(pilot.app.screen, RemoveLanguageScreen)
        assert [entry.name for entry in pilot.app.config.languages] == ["Chinese", "German"]
        assert not (config.root / "config.toml").exists()
        assert note.exists()
        assert _notices(pilot) == []


async def test_enter_confirms_neither_dialog(config):
    _give_chinese_notes(config)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "enter")
        assert isinstance(pilot.app.screen, ConfirmDialog)
        assert "Remove Chinese" in _dialog_text(pilot)

        await _answer(pilot, "y")
        assert "Also delete" in _dialog_text(pilot)
        await _answer(pilot, "enter")
        assert isinstance(pilot.app.screen, ConfirmDialog)
        assert config.tree_root("Chinese").exists()
        assert pilot.app.config.language("Chinese") is not None


async def test_the_second_dialog_names_the_folder_and_counts_its_files(config):
    _give_chinese_notes(config)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "y")
        assert _dialog_text(pilot) == (
            f"Also delete {config.tree_root('Chinese')} and the 2 files in it? "
            "This cannot be undone."
        )


async def test_the_second_dialog_wording_for_one_file_and_for_none(config):
    from vimdiomas.tui.screens.settings import _delete_notes_question

    folder = config.tree_root("Chinese")
    assert _delete_notes_question(folder) == (
        f"Also delete the empty folder {folder}? This cannot be undone."
    )
    # Folders alone are not files.
    (folder / "Vocabulary").mkdir()
    assert "the empty folder" in _delete_notes_question(folder)
    (folder / "Vocabulary" / "Food.md").write_text("# Food\n")
    assert _delete_notes_question(folder) == (
        f"Also delete {folder} and the 1 file in it? This cannot be undone."
    )


@pytest.mark.parametrize("key", ["n", "escape"])
async def test_removing_and_keeping_the_notes(config, key):
    note, pdf = _give_chinese_notes(config)
    from vimdiomas import compile as compile_module

    cache_before = compile_module._load_cache()
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "y", key)

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert [entry.name for entry in load_config().languages] == ["German"]
        assert [entry.name for entry in pilot.app.config.languages] == ["German"]
        assert note.read_text() == "# Food\n"
        assert pdf.exists()
        assert compile_module._load_cache() == cache_before
        assert _notices(pilot) == [
            f"Chinese removed. Its notes are still in {config.tree_root('Chinese')}."
        ]


async def test_removing_and_deleting_the_notes(config):
    _give_chinese_notes(config)
    from vimdiomas import compile as compile_module

    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "y", "y")

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert not config.tree_root("Chinese").exists()
        assert [entry.name for entry in load_config().languages] == ["German"]
        assert compile_module._load_cache() == {
            str(config.root / "tree-German" / "Essen.md"): "german",
            str(config.root / "tree-Chinese2" / "Food.md"): "sibling",
        }
        assert _notices(pilot) == ["Chinese removed, and its notes deleted."]


async def test_with_no_folder_on_disk_there_is_one_dialog(config):
    assert not config.tree_root("German").exists()
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, GERMAN_ROW, "y")

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert [entry.name for entry in load_config().languages] == ["Chinese"]
        assert _notices(pilot) == ["German removed."]


async def test_a_failed_save_changes_nothing(config, monkeypatch):
    note, _ = _give_chinese_notes(config)

    def failing_save(config):
        raise OSError("disk full")

    monkeypatch.setattr("vimdiomas.tui.screens.settings.save_config", failing_save)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "y", "y")

        assert isinstance(pilot.app.screen, RemoveLanguageScreen)
        assert [entry.name for entry in pilot.app.config.languages] == ["Chinese", "German"]
        assert note.exists()
        assert not (config.root / "config.toml").exists()
        assert _notices(pilot) == ["Could not remove Chinese: disk full"]


async def test_a_failing_delete_still_removes_the_language(config, monkeypatch):
    note, _ = _give_chinese_notes(config)
    from vimdiomas import compile as compile_module

    cache_before = compile_module._load_cache()

    def failing_rmtree(path):
        raise OSError("permission denied")

    monkeypatch.setattr("vimdiomas.tui.screens.settings.shutil.rmtree", failing_rmtree)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "y", "y")

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert [entry.name for entry in load_config().languages] == ["German"]
        assert [entry.name for entry in pilot.app.config.languages] == ["German"]
        assert note.exists()
        assert compile_module._load_cache() == cache_before
        assert _notices(pilot) == [
            f"Chinese removed, but {config.tree_root('Chinese')} could not be deleted: "
            "permission denied"
        ]


async def test_markup_in_a_name_or_path_is_shown_literally(config):
    config.languages.append(LanguageConfig(name="[b]Odd[/]"))
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, 2, "y")  # no folder: one dialog
        assert _notices(pilot) == ["[b]Odd[/] removed."]


async def test_the_language_leaves_the_landing_menu_without_relaunching(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, GERMAN_ROW, "y")
        await pilot.press("q")
        await pilot.pause()

        assert isinstance(pilot.app.screen, LandingMenuScreen)
        assert _labels(pilot) == ["Chinese notebook", "Settings"]
        assert pilot.app.screen.query_one("OptionList").highlighted_option.id == "settings"


async def test_the_landing_highlight_falls_back_when_its_language_is_removed(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _open_settings(pilot)
        await pilot.press("q")
        await pilot.pause()
        pilot.app.screen.query_one("OptionList").highlighted = 1  # German
        # Remove German from Settings, then come back with the highlight on it.
        await _open_settings(pilot)
        await _select(pilot, REMOVE_LANGUAGE)
        await _select(pilot, GERMAN_ROW)
        await _answer(pilot, "y")
        await pilot.press("q")
        await pilot.pause()
        assert _labels(pilot) == ["Chinese notebook", "Settings"]


async def test_input_methods_no_longer_lists_the_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, GERMAN_ROW, "y")
        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, InputMethodLanguagesScreen)
        assert _labels(pilot) == ["Chinese"]


async def test_the_picker_drops_the_removed_language(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, GERMAN_ROW, "y")
        await _select(pilot, REMOVE_LANGUAGE)
        assert _labels(pilot) == ["Chinese"]


async def _remove_every_language(pilot):
    await _remove(pilot, GERMAN_ROW, "y")
    await _select(pilot, REMOVE_LANGUAGE)
    await _select(pilot, 0)
    await _answer(pilot, "y")
    await _answer(pilot, "n")  # keep Chinese's notes


async def test_removing_every_language_leaves_only_settings(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove_every_language(pilot)
        assert pilot.app.config.languages == []
        assert load_config().languages == []

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, LandingMenuScreen)
        assert _labels(pilot) == ["Settings"]
        assert await _legend_texts(pilot, 1) == ["Add a language to start a notebook."]


async def test_with_no_language_both_pickers_show_placeholders(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove_every_language(pilot)

        await _select(pilot, 0)
        assert isinstance(pilot.app.screen, PlaceholderScreen)
        assert _dialog_text(pilot) == "There is no language to set up. Add one first."
        await pilot.press("q")
        await pilot.pause()

        await _select(pilot, REMOVE_LANGUAGE)
        assert isinstance(pilot.app.screen, PlaceholderScreen)
        assert _dialog_text(pilot) == "There is no language to remove."


async def test_adding_a_language_back_restores_the_landing_entry(config):
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove_every_language(pilot)
        await _select(pilot, ADD_LANGUAGE)
        await _select(pilot, 0)  # the registry's first: Chinese
        await _press_add(pilot)
        await pilot.press("q")
        await pilot.pause()

        assert _labels(pilot) == ["Chinese notebook", "Settings"]
        pilot.app.screen.query_one("OptionList").highlighted = 0
        await pilot.pause()
        assert await _legend_texts(pilot, 2) == [
            "Add words, explore and compile your Chinese notes.",
            "Input methods, and adding or removing a language.",
        ]


async def test_removing_then_re_adding_restores_the_kept_notes(config):
    note, pdf = _give_chinese_notes(config)
    app = VimdiomasApp(config)
    async with app.run_test() as pilot:
        await _remove(pilot, CHINESE, "y", "n")
        assert pilot.app.config.language("Chinese") is None

        await _select(pilot, ADD_LANGUAGE)
        assert _labels(pilot)[0] == "Chinese"
        await _select(pilot, 0)
        # The kept folder doesn't carry the keyboard answers: asked afresh.
        assert isinstance(pilot.app.screen, AddLanguageFormScreen)
        await _press_add(pilot)

        assert isinstance(pilot.app.screen, SettingsScreen)
        assert note.read_text() == "# Food\n"
        assert pdf.exists()
        assert pilot.app.config.language("Chinese") is not None
        await pilot.press("q")
        await pilot.pause()
        await _select(pilot, 1)  # Chinese notebook, now after German
        assert isinstance(pilot.app.screen, MainMenuScreen)
        assert pilot.app.screen.language == "Chinese"
