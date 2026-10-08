from dataclasses import dataclass
from pathlib import Path

import pytest

from vimdiomas.config import Config, LanguageConfig, load_config
from vimdiomas.platform import CJK_FONT_NAME, InputSource
from vimdiomas.tui.screens.input_methods import (
    LANGUAGE_FIELD_ID,
    NO_SOURCES_MESSAGE,
    ONE_SOURCE_MESSAGE,
    TRANSLATION_FIELD_ID,
)
from vimdiomas.tui.screens.base import ConfirmDialog
from vimdiomas.tui.screens.panels import Backpanel, Panel, SelectField
from vimdiomas import install
from vimdiomas.tui.screens.wizard import (
    DependenciesScreen,
    InputMethodScreen,
    LanguagesScreen,
    NameScreen,
    PathScreen,
    TreeLocationScreen,
    WizardApp,
    PANEL_CONTENT_WIDTH,
    _checks_text,
    _pending_checks_text,
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
def _patched_input_sources(monkeypatch):
    """A fixed source list: the real one is whatever keyboards the machine
    running the tests happens to have enabled."""
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources", lambda: list(SOURCES)
    )


@dataclass
class _FakeCheck:
    name: str
    required: bool
    ok: bool
    key: str = ""
    needed_for: tuple = ()
    detail: str = ""


def _all_ok_checks():
    return [
        _FakeCheck("pandoc", required=True, ok=True),
        _FakeCheck("xelatex", required=True, ok=True),
        _FakeCheck("xeCJK", required=False, ok=True, needed_for=("Chinese",)),
        _FakeCheck(CJK_FONT_NAME, required=False, ok=True, needed_for=("Chinese",)),
        _FakeCheck("macism", required=False, ok=False),
        _FakeCheck("nvim", required=False, ok=True),
    ]


def _blocked_checks():
    checks = _all_ok_checks()
    checks[0] = _FakeCheck("pandoc", required=True, ok=False)
    return checks


@pytest.fixture(autouse=True)
def _patched_config_path(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)
    monkeypatch.setattr("vimdiomas.tui.screens.wizard.DEFAULT_ROOT", str(tmp_path / "Vimdiomas"))
    # No artificial delay in tests — production keeps it so Recheck's
    # loading indicator reads as intentional rather than a flash.
    monkeypatch.setattr("vimdiomas.tui.screens.wizard.MIN_RECHECK_SECONDS", 0)
    return config_path


@pytest.fixture(autouse=True)
def _patched_user_bin(tmp_path, monkeypatch):
    """Keep the wizard's final step (Sprint 4 M7) inside tmp_path.

    Autouse and unconditional: the step creates a symlink **and now appends
    to a shell config** on Finish, and a test must never be able to write
    into the real `~/.local/bin` or the real `~/.zshrc`.
    """
    bin_dir = tmp_path / "local-bin"
    monkeypatch.setattr("vimdiomas.install.user_bin_dir", lambda: bin_dir)
    monkeypatch.setattr(
        "vimdiomas.install.shell_config_path", lambda: tmp_path / "shell-rc"
    )
    # A console script to link to, since the test process's argv[0] is
    # pytest's, not an `vimdiomas` entry point.
    script = tmp_path / "venv-bin" / "vimdiomas"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/bin/sh\n")
    monkeypatch.setattr("vimdiomas.install.sys.argv", [str(script)])
    return bin_dir


async def _advance_past_dependencies(pilot, monkeypatch, checks_fn=_all_ok_checks):
    monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", checks_fn)
    pilot.app.screen.query_one("#dependencies-list")
    pilot.app.screen._refresh_checks()
    # Let the layout settle after the content update before computing
    # click coordinates — clicking in the same tick as a content change
    # can hit a stale (pre-reflow) position.
    await pilot.pause()
    await pilot.click("#next-button")
    await pilot.pause()


def test_checks_text_shows_missing_and_nothing_else():
    # Sprint 8 M3: no link, no command, no hint on how to get it.
    lines = _checks_text(_blocked_checks()).plain.split("\n")

    assert lines[0] == "[required] pandoc     missing"
    assert not any(word in "\n".join(lines).lower() for word in ("http", "<--", "brew", "install"))


def _latex_check(ok=False, detail="fontspec, caption, xcolor, lmodern, lmodern fonts"):
    return _FakeCheck(
        "LaTeX packages", required=True, ok=ok, key="latex-packages", detail="" if ok else detail
    )


def test_checks_text_shows_the_detail_under_a_failing_check():
    checks = [_FakeCheck("pandoc", required=True, ok=True), _latex_check()]

    lines = _checks_text(checks).plain.split("\n")

    assert lines == [
        "[required] pandoc         ok",
        "[required] LaTeX packages missing",
        "  fontspec, caption, xcolor, lmodern, lmodern fonts",
    ]


def test_checks_text_wraps_a_long_detail_inside_the_panel():
    detail = ", ".join(["fontspec", "geometry", "longtable", "caption", "array", "xcolor", "lmodern", "lmodern fonts"])
    text = _checks_text([_latex_check(detail=detail)])

    lines = text.plain.split("\n")

    assert len(lines) > 2
    assert all(len(line) <= PANEL_CONTENT_WIDTH for line in lines)
    assert all(line.startswith("  ") for line in lines[1:])
    assert " ".join(line.strip() for line in lines[1:]) == detail
    detail_start = text.plain.index("\n") + 1
    assert all(span.style == "red" for span in text.spans if span.start >= detail_start)


def test_checks_text_shows_no_detail_for_an_ok_check():
    lines = _checks_text([_latex_check(ok=True)]).plain.split("\n")

    assert lines == ["[required] LaTeX packages ok"]


def test_pending_checks_text_has_no_detail():
    text = _pending_checks_text([_latex_check()], 0).plain

    assert "fontspec" not in text
    assert "\n" not in text


async def test_dependencies_blocks_next_on_missing_latex_packages(monkeypatch):
    def checks():
        return [_latex_check(), *_all_ok_checks()[2:]]

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch, checks)
        assert isinstance(pilot.app.screen, DependenciesScreen)
        assert pilot.app.screen.query_one("#dependencies-error").display


def test_checks_text_colors_ok_green_and_failing_red():
    checks = _all_ok_checks()  # includes one failing optional check
    text = _checks_text(checks)
    plain = text.plain

    def _style_at(substring: str) -> str | None:
        offset = plain.index(substring)
        for span in text.spans:
            if span.start <= offset < span.end:
                return span.style
        return None

    for check in checks:
        status = "ok" if check.ok else "missing"
        expected_style = "green" if check.ok else "red"
        assert _style_at(status) == expected_style


def test_checks_text_aligns_status_column():
    checks = _all_ok_checks()
    lines = _checks_text(checks).plain.splitlines()
    # Check names differ in length ("pandoc" vs the CJK font's name), but the
    # name padding keeps every status starting in the same column.
    status_columns = set()
    for line, check in zip(lines, checks):
        status = "ok" if check.ok else "missing"
        status_columns.add(line.index(status))
    assert len(status_columns) == 1


def test_checks_text_aligns_names_longer_than_ten():
    """Linux's names run past the old fixed 10-character column (Sprint 5 M7)."""
    checks = [
        _FakeCheck("pandoc", required=True, ok=True),
        _FakeCheck("Noto Serif CJK SC", required=True, ok=True),
        _FakeCheck("fcitx5 or ibus", required=False, ok=False),
    ]
    lines = _checks_text(checks).plain.splitlines()
    columns = {line.index("ok" if check.ok else "missing") for line, check in zip(lines, checks)}
    assert len(columns) == 1


def test_checks_text_keeps_the_ten_character_column_for_short_names():
    """Every macOS name fits in 10, so its layout is what it was before M7."""
    line = _checks_text([_FakeCheck("pandoc", required=True, ok=True)]).plain
    assert line == "[required] pandoc     ok"


async def test_dependencies_blocks_next_on_missing_required(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch, _blocked_checks)
        assert isinstance(pilot.app.screen, DependenciesScreen)
        assert pilot.app.screen.query_one("#dependencies-error").display


async def test_dependencies_recheck_unblocks_without_restarting(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _blocked_checks)
        pilot.app.screen._refresh_checks()
        await pilot.pause()
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DependenciesScreen)

        monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _all_ok_checks)
        await pilot.click("#recheck-button")
        await app.workers.wait_for_complete()
        await pilot.pause()
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, NameScreen)


async def test_recheck_shows_inline_spinner_then_results(monkeypatch):
    # Fake checks from the start, so the pending list (drawn from the
    # previous run's names) doesn't depend on which OS runs the test.
    monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _all_ok_checks)
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        list_widget = pilot.app.screen.query_one("#dependencies-list")
        assert "ok" in list_widget.render().plain

        # A brief floor, just for this test, so the intermediate spinner
        # state is observable rather than racing past it — production
        # relies on this same floor for the same reason.
        monkeypatch.setattr("vimdiomas.tui.screens.wizard.MIN_RECHECK_SECONDS", 0.3)
        monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _all_ok_checks)
        await pilot.click("#recheck-button")
        await pilot.pause()
        pending_text = list_widget.render().plain
        # Every check's own name is still visible (inline per dependency,
        # not one big indicator replacing the whole list) but its status
        # column is a spinner frame, not "ok"/a failure message.
        for check in _all_ok_checks():
            assert check.name in pending_text
        assert "ok" not in pending_text
        assert pilot.app.screen.query_one("#recheck-button").disabled

        await app.workers.wait_for_complete()
        await pilot.pause()
        assert "ok" in list_widget.render().plain
        assert not pilot.app.screen.query_one("#recheck-button").disabled


async def test_dependencies_proceeds_when_all_required_ok(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)
        assert isinstance(pilot.app.screen, NameScreen)


async def test_tab_cycles_dependencies_buttons_without_reaching_panel_or_backpanel(
    monkeypatch,
):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _all_ok_checks)

        seen_ids = set()
        for _ in range(6):
            await pilot.press("tab")
            await pilot.pause()
            focused = pilot.app.focused
            assert not isinstance(focused, (Panel, Backpanel))
            seen_ids.add(focused.id)
        assert seen_ids == {"recheck-button", "next-button"}


async def test_tab_cycles_tree_location_field_and_button(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch)

        await pilot.press("tab")
        await pilot.pause()
        focused = pilot.app.focused
        assert not isinstance(focused, (Panel, Backpanel))
        assert focused.id == "next-button"


async def test_q_on_first_step_asks_for_confirmation_before_aborting(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _all_ok_checks)
        await pilot.press("q")
        await pilot.pause()

        assert not app._exit
        await pilot.press("n")
        await pilot.pause()
        assert not app._exit
        assert isinstance(pilot.app.screen, DependenciesScreen)


async def test_q_on_first_step_confirmed_aborts_with_no_config_written(
    monkeypatch, tmp_path
):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", _all_ok_checks)
        await pilot.press("q")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

    assert app.return_value is None
    assert not (tmp_path / "config.toml").exists()


async def test_q_from_name_screen_returns_to_dependencies(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)
        assert isinstance(pilot.app.screen, NameScreen)

        # The name field has focus (content), and `q` types into a focused
        # Input rather than going back (PanelScreen's existing rule) — esc
        # to the panel first, same as any other screen.
        await pilot.press("escape", "q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DependenciesScreen)


async def test_name_step_refuses_empty_name(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)

        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, NameScreen)
        assert pilot.app.screen.query_one("#name-error").display


async def test_name_step_advances_with_a_real_name(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)

        pilot.app.screen.query_one("#name-field").value = "Nico"
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, LanguagesScreen)
        assert pilot.app.user_name == "Nico"


async def test_languages_step_refuses_zero_selected(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)
        pilot.app.screen.query_one("#name-field").value = "Nico"
        await pilot.click("#next-button")
        await pilot.pause()

        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, LanguagesScreen)
        assert pilot.app.screen.query_one("#languages-error").display


async def test_languages_step_space_does_not_toggle_checkbox(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)
        pilot.app.screen.query_one("#name-field").value = "Nico"
        await pilot.click("#next-button")
        await pilot.pause()

        checkbox = pilot.app.screen.query_one("#language-chinese")
        checkbox.focus()
        await pilot.pause()
        await pilot.press("space")
        await pilot.pause()
        assert checkbox.value is False

        await pilot.press("enter")
        await pilot.pause()
        assert checkbox.value is True


async def test_languages_step_advances_with_a_selection(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch)
        pilot.app.screen.query_one("#name-field").value = "Nico"
        await pilot.click("#next-button")
        await pilot.pause()

        await pilot.click("#language-chinese")
        await pilot.click("#language-german")
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TreeLocationScreen)
        assert pilot.app.languages == ["Chinese", "German"]


async def _reach_tree_location(pilot, monkeypatch, languages=("Chinese", "German")):
    await _advance_past_dependencies(pilot, monkeypatch)
    pilot.app.screen.query_one("#name-field").value = "Nico"
    await pilot.click("#next-button")
    await pilot.pause()
    for language in languages:
        await pilot.click(f"#language-{language.lower()}")
    await pilot.click("#next-button")
    await pilot.pause()


async def _reach_input_methods(pilot, monkeypatch, languages=("Chinese", "German"), root=None):
    await _reach_tree_location(pilot, monkeypatch, languages=languages)
    if root is not None:
        pilot.app.screen.query_one("#root-field").value = str(root)
    await pilot.click("#next-button")
    await pilot.pause()


async def _advance_through_input_methods(pilot):
    """Accept each input-method step's preselection and move on, once per
    chosen language — bounded by that count rather than by "still on an
    input-method screen": the last click exits the app, which leaves the
    final screen in place.
    """
    for _ in range(len(pilot.app.languages)):
        await pilot.click("#next-button")
        await pilot.pause()
    # The last input-method step now lands on the PATH step, which is what
    # actually writes (Sprint 4 M7). Driven by key rather than click: the
    # step's report can wrap to several lines under a long tmp_path, which
    # pushes the button outside the 80x24 test screen.
    await pilot.press("enter")
    await pilot.pause()


async def test_tree_location_rejects_path_inside_package(monkeypatch):
    from vimdiomas.config import PACKAGE_ROOT

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch)

        pilot.app.screen.query_one("#root-field").value = str(PACKAGE_ROOT / "trees")
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TreeLocationScreen)
        assert pilot.app.screen.query_one("#root-error").display


async def test_tree_location_rejects_unwritable_path(monkeypatch, tmp_path):
    unwritable = tmp_path / "locked"
    unwritable.mkdir()
    unwritable.chmod(0o500)
    try:
        app = WizardApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await _reach_tree_location(pilot, monkeypatch)

            pilot.app.screen.query_one("#root-field").value = str(unwritable / "Vimdiomas")
            await pilot.click("#next-button")
            await pilot.pause()
            assert isinstance(pilot.app.screen, TreeLocationScreen)
            assert pilot.app.screen.query_one("#root-error").display
    finally:
        unwritable.chmod(0o700)


async def test_finish_creates_tree_folders_for_every_selected_language(
    monkeypatch, tmp_path
):
    existing_root = tmp_path / "Existing"
    existing_chinese = existing_root / "tree-Chinese"
    existing_chinese.mkdir(parents=True)
    (existing_chinese / "keepme.md").write_text("已有内容", encoding="utf-8")

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch)

        pilot.app.screen.query_one("#root-field").value = str(existing_root)
        await pilot.click("#next-button")
        await pilot.pause()
        await _advance_through_input_methods(pilot)

    assert app.return_value is not None
    config = app.return_value
    assert (existing_root / "tree-Chinese" / "keepme.md").read_text(
        encoding="utf-8"
    ) == "已有内容"
    assert (existing_root / "tree-German").is_dir()
    # Every tree has both folders, an existing one completed (Sprint 6 M6).
    for language in ("Chinese", "German"):
        for folder in ("Vocabulary", "Grammar"):
            assert (existing_root / f"tree-{language}" / folder).is_dir()
    assert config.languages == [
        LanguageConfig(
            name="Chinese", input_method=HANZI, translation_input_method=ENGLISH
        ),
        LanguageConfig(
            name="German", input_method=GERMAN, translation_input_method=ENGLISH
        ),
    ]


async def test_full_happy_path_writes_a_config_load_config_reads_back(
    monkeypatch, tmp_path, _patched_config_path
):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch, languages=("Chinese",))

        root = tmp_path / "MyTrees"
        pilot.app.screen.query_one("#root-field").value = str(root)
        await pilot.click("#next-button")
        await pilot.pause()
        await _advance_through_input_methods(pilot)

    assert app.return_value == Config(
        user_name="Nico",
        root=root,
        languages=[
            LanguageConfig(
                name="Chinese", input_method=HANZI, translation_input_method=ENGLISH
            )
        ],
    )
    assert load_config() == app.return_value
    assert _patched_config_path.exists()


async def test_one_input_method_step_per_language_in_order(monkeypatch, tmp_path):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(pilot, monkeypatch, root=tmp_path / "Trees")

        assert isinstance(pilot.app.screen, InputMethodScreen)
        assert pilot.app.screen.language == "Chinese"
        assert pilot.app.screen.query_one("#next-button").label.plain == "Next"

        await pilot.click("#next-button")
        await pilot.pause()
        assert pilot.app.screen.language == "German"
        # Every input-method step reads "Next" now: the PATH step is the
        # last one, and the one that says Finish (Sprint 4 M7).
        assert pilot.app.screen.query_one("#next-button").label.plain == "Next"

        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, PathScreen)
        assert pilot.app.screen.query_one("#finish-button").label.plain == "Finish"


async def test_input_method_step_preselects_per_language(monkeypatch, tmp_path):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(pilot, monkeypatch, root=tmp_path / "Trees")

        screen = pilot.app.screen
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == HANZI
        assert screen.query_one(f"#{TRANSLATION_FIELD_ID}", SelectField).value == ENGLISH

        await pilot.click("#next-button")
        await pilot.pause()
        screen = pilot.app.screen
        assert screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField).value == GERMAN
        assert screen.query_one(f"#{TRANSLATION_FIELD_ID}", SelectField).value == ENGLISH


async def test_q_from_input_methods_returns_to_tree_location_with_root_intact(
    monkeypatch, tmp_path
):
    root = tmp_path / "Trees"
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(pilot, monkeypatch, root=root)

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TreeLocationScreen)
        assert pilot.app.screen.query_one("#root-field").value == str(root)


async def test_choices_survive_walking_back_and_forward(monkeypatch, tmp_path):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(
            pilot, monkeypatch, languages=("Chinese",), root=tmp_path / "Trees"
        )

        field = pilot.app.screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField)
        field.value = GERMAN

        await pilot.press("q")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TreeLocationScreen)
        await pilot.click("#next-button")
        await pilot.pause()

        assert pilot.app.screen.query_one(
            f"#{LANGUAGE_FIELD_ID}", SelectField
        ).value == GERMAN


async def test_nothing_is_written_until_the_last_input_method_step(
    monkeypatch, tmp_path, _patched_config_path
):
    """Tree folders and the config both moved off tree location and onto the
    final step (Sprint 4 M6), so quitting from an input-method step still
    leaves nothing behind — M5's standing rule."""
    root = tmp_path / "Trees"
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(pilot, monkeypatch, root=root)

        assert not root.exists()
        assert not _patched_config_path.exists()


async def test_one_source_warns_and_still_finishes(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources",
        lambda: [InputSource(id=ENGLISH, name="U.S. International – PC")],
    )
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(
            pilot, monkeypatch, languages=("Chinese",), root=tmp_path / "Trees"
        )
        screen = pilot.app.screen
        assert ONE_SOURCE_MESSAGE in str(screen.query(".wizard-advisory").first().content)
        await _advance_through_input_methods(pilot)

    assert app.return_value.languages == [
        LanguageConfig(
            name="Chinese", input_method=ENGLISH, translation_input_method=ENGLISH
        )
    ]


async def test_no_sources_warns_and_still_finishes(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "vimdiomas.tui.screens.input_methods.list_input_sources", lambda: []
    )
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(
            pilot, monkeypatch, languages=("Chinese",), root=tmp_path / "Trees"
        )
        screen = pilot.app.screen
        assert NO_SOURCES_MESSAGE in str(screen.query(".wizard-advisory").first().content)
        await _advance_through_input_methods(pilot)

    assert app.return_value.languages == [LanguageConfig(name="Chinese")]


async def test_tab_cycles_input_method_fields_and_button(monkeypatch, tmp_path):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(
            pilot, monkeypatch, languages=("Chinese",), root=tmp_path / "Trees"
        )
        assert pilot.app.focused.id == LANGUAGE_FIELD_ID
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == TRANSLATION_FIELD_ID
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.focused.id == "next-button"


async def test_choosing_from_the_deployed_list_changes_the_value(monkeypatch, tmp_path):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_input_methods(
            pilot, monkeypatch, languages=("Chinese",), root=tmp_path / "Trees"
        )
        field = pilot.app.screen.query_one(f"#{LANGUAGE_FIELD_ID}", SelectField)
        assert not field.expanded

        await pilot.press("enter")
        await pilot.pause()
        assert field.expanded

        await pilot.press("k", "enter")
        await pilot.pause()
        assert not field.expanded
        assert field.value == ENGLISH

        await _advance_through_input_methods(pilot)

    assert app.return_value.languages[0].input_method == ENGLISH


# --- the PATH step (Sprint 4 M7) -----------------------------------------


async def _reach_path_step(pilot, monkeypatch, root, languages=("Chinese",)):
    """Walk to the PATH step without finishing it."""
    await _reach_input_methods(pilot, monkeypatch, languages=languages, root=root)
    for _ in range(len(languages)):
        await pilot.click("#next-button")
        await pilot.pause()
    assert isinstance(pilot.app.screen, PathScreen)


async def test_path_step_creates_the_link_on_finish(
    monkeypatch, tmp_path, _patched_user_bin, _patched_config_path
):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        await pilot.press("enter")
        await pilot.pause()

    link = _patched_user_bin / "vimdiomas"
    assert link.is_symlink()
    assert link.resolve() == Path(install.sys.argv[0]).resolve()
    assert _patched_config_path.exists()
    assert app.return_value is not None


async def test_path_step_creates_the_bin_directory(
    monkeypatch, tmp_path, _patched_user_bin
):
    assert not _patched_user_bin.exists()
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        await pilot.press("enter")
        await pilot.pause()

    assert _patched_user_bin.is_dir()


async def test_path_step_leaves_an_occupied_path_alone(
    monkeypatch, tmp_path, _patched_user_bin, _patched_config_path
):
    _patched_user_bin.mkdir(parents=True)
    (_patched_user_bin / "vimdiomas").write_text("someone else's program")

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        report = pilot.app.screen.query_one("#path-report").render().plain
        assert "in the way" in report
        await pilot.press("enter")
        await pilot.pause()

    # Not overwritten, and the wizard still finished and wrote the config.
    assert (_patched_user_bin / "vimdiomas").read_text() == "someone else's program"
    assert _patched_config_path.exists()
    assert app.return_value is not None


async def test_path_step_reports_an_existing_correct_link(
    monkeypatch, tmp_path, _patched_user_bin
):
    _patched_user_bin.mkdir(parents=True)
    link = _patched_user_bin / "vimdiomas"
    link.symlink_to(Path(install.sys.argv[0]))
    before = link.lstat().st_ino

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        assert "already linked" in pilot.app.screen.query_one("#path-report").render().plain
        await pilot.press("enter")
        await pilot.pause()

    # Re-running the wizard doesn't recreate a link that's already right.
    assert link.lstat().st_ino == before
    assert app.return_value is not None


async def test_path_step_still_writes_when_linking_fails(
    monkeypatch, tmp_path, _patched_config_path
):
    def boom(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(Path, "symlink_to", boom)

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        await pilot.press("enter")
        await pilot.pause()

        # The failure is reported rather than exiting over the top of it,
        # and the config is already saved by then.
        assert pilot.app.screen.query_one("#path-error").display
        assert _patched_config_path.exists()

        # A second press leaves, with the config that was written. The
        # button is still mid "active press" from the first `enter`, which
        # swallows a key sent in the same tick — let it settle first.
        await pilot.pause(0.2)
        await pilot.press("enter")
        await pilot.pause()

    assert app.return_value is not None


async def test_path_step_previews_the_line_finish_will_add(
    monkeypatch, tmp_path, _patched_user_bin
):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SHELL", "/bin/zsh")

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        report = pilot.app.screen.query_one("#path-report").render().plain

    assert "isn't on your PATH yet" in report
    assert "Finish will add this line" in report
    assert "export PATH=" in report


async def test_path_step_says_nothing_to_add_when_already_on_path(
    monkeypatch, tmp_path, _patched_user_bin
):
    _patched_user_bin.mkdir(parents=True)
    monkeypatch.setenv("PATH", f"/usr/bin:{_patched_user_bin}")

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        report = pilot.app.screen.query_one("#path-report").render().plain

    assert "already on your PATH" in report
    assert "export PATH=" not in report


async def test_path_step_finish_appends_the_line_when_missing(
    monkeypatch, tmp_path, _patched_user_bin
):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SHELL", "/bin/zsh")
    config_path = tmp_path / "shell-rc"
    expected_line = install.path_export_line(_patched_user_bin)

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        await pilot.press("enter")
        await pilot.pause()

    assert expected_line in config_path.read_text()


async def test_path_step_finish_never_duplicates_the_line(
    monkeypatch, tmp_path, _patched_user_bin
):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SHELL", "/bin/zsh")
    config_path = tmp_path / "shell-rc"
    expected_line = install.path_export_line(_patched_user_bin)
    config_path.write_text(f"{expected_line}\n")

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        # Already present, so the report says so rather than "will add".
        report = pilot.app.screen.query_one("#path-report").render().plain
        assert "already in" in report
        assert "Finish will add" not in report

        await pilot.press("enter")
        await pilot.pause()

    text = config_path.read_text()
    assert text.count(expected_line) == 1


async def test_path_step_finish_does_not_touch_config_when_already_on_path(
    monkeypatch, tmp_path, _patched_user_bin
):
    _patched_user_bin.mkdir(parents=True)
    monkeypatch.setenv("PATH", f"/usr/bin:{_patched_user_bin}")
    config_path = tmp_path / "shell-rc"

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        await pilot.press("enter")
        await pilot.pause()

    assert not config_path.exists()


async def test_path_step_still_writes_when_shell_config_write_fails(
    monkeypatch, tmp_path, _patched_user_bin, _patched_config_path
):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SHELL", "/bin/zsh")

    # A read-only parent directory: the append fails with a real permission
    # error rather than a blanket monkeypatch that would also break the
    # config save this test is checking survives it.
    locked_dir = tmp_path / "locked"
    locked_dir.mkdir()
    locked_dir.chmod(0o500)
    monkeypatch.setattr(
        "vimdiomas.install.shell_config_path", lambda: locked_dir / "shell-rc"
    )

    try:
        app = WizardApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
            await pilot.press("enter")
            await pilot.pause()

            assert pilot.app.screen.query_one("#path-error").display
            assert _patched_config_path.exists()

            await pilot.pause(0.2)
            await pilot.press("enter")
            await pilot.pause()

        assert app.return_value is not None
    finally:
        locked_dir.chmod(0o700)


async def test_path_step_explains_when_there_is_no_script_to_link(
    monkeypatch, tmp_path, _patched_user_bin
):
    monkeypatch.setattr("vimdiomas.install.sys.argv", [])

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, tmp_path / "Trees")
        report = pilot.app.screen.query_one("#path-report").render().plain
        await pilot.press("enter")
        await pilot.pause()

    assert "no command to link" in report
    assert not (_patched_user_bin / "vimdiomas").exists()
    assert app.return_value is not None


async def test_q_on_the_path_step_writes_nothing(
    monkeypatch, tmp_path, _patched_user_bin, _patched_config_path
):
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.setenv("SHELL", "/bin/zsh")
    root = tmp_path / "Trees"
    shell_config = tmp_path / "shell-rc"

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_path_step(pilot, monkeypatch, root)

        await pilot.press("q")
        await pilot.pause()
        # Back on the last input-method step, with nothing written.
        assert isinstance(pilot.app.screen, InputMethodScreen)

    assert not _patched_config_path.exists()
    assert not root.exists()
    assert not (_patched_user_bin / "vimdiomas").exists()
    assert not shell_config.exists()


# -- Sprint 6 M1 · #7: the wizard stores an absolute tree root --------------


async def test_a_relative_root_is_stored_absolute(monkeypatch, tmp_path):
    """The bug: the wizard validated a resolved path but stored the raw one,
    so a relative answer was re-interpreted against every future process's
    working directory — the same command found a different tree, or none,
    depending on where it was launched."""
    launch_dir = tmp_path / "launched-from"
    launch_dir.mkdir()
    monkeypatch.chdir(launch_dir)

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch, languages=("Chinese",))

        pilot.app.screen.query_one("#root-field").value = "notebooks"
        await pilot.click("#next-button")
        await pilot.pause()
        await _advance_through_input_methods(pilot)

    config = load_config()
    assert config.root.is_absolute()
    assert config.root == launch_dir / "notebooks"
    assert (launch_dir / "notebooks" / "tree-Chinese").is_dir()


async def test_the_tree_is_found_from_a_different_working_directory(
    monkeypatch, tmp_path
):
    """The report's reproduction in full: finish setup from one directory,
    change to another, and the app still finds the same tree."""
    launch_dir = tmp_path / "A"
    launch_dir.mkdir()
    other_dir = tmp_path / "B"
    other_dir.mkdir()
    monkeypatch.chdir(launch_dir)

    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch, languages=("Chinese",))
        pilot.app.screen.query_one("#root-field").value = "notebooks"
        await pilot.click("#next-button")
        await pilot.pause()
        await _advance_through_input_methods(pilot)

    monkeypatch.chdir(other_dir)
    tree_root = load_config().tree_root("Chinese")
    assert tree_root.is_dir()
    assert tree_root == launch_dir / "notebooks" / "tree-Chinese"


# -- Sprint 6 M7: six languages, and what a language needs -------------------


def _cjk_missing_checks():
    """Everything required is there; Chinese's xeCJK is not."""
    checks = _all_ok_checks()
    checks[2] = _FakeCheck("xeCJK", required=False, ok=False, key="xecjk", needed_for=("Chinese",))
    return checks


async def _reach_languages(pilot, monkeypatch, checks_fn=_all_ok_checks):
    await _advance_past_dependencies(pilot, monkeypatch, checks_fn)
    pilot.app.screen.query_one("#name-field").value = "Nico"
    await pilot.click("#next-button")
    await pilot.pause()
    assert isinstance(pilot.app.screen, LanguagesScreen)


def _sequence(monkeypatch, *states):
    """`doctor.run` returns each state in turn, the last one repeating."""
    remaining = list(states)

    def run():
        return remaining.pop(0)() if len(remaining) > 1 else remaining[0]()

    monkeypatch.setattr("vimdiomas.tui.screens.wizard.doctor.run", run)


@pytest.fixture
def install_runs(monkeypatch):
    """Step 3's offer, with no real process: the platform can install every
    language dependency, its package manager is there, and the install is
    recorded as the keys it was asked for."""
    from vimdiomas.tui.screens import dependencies

    calls = {"installs": []}
    monkeypatch.setattr(
        dependencies.installer,
        "run",
        lambda app, checks: calls["installs"].append([check.key for check in checks]),
    )
    monkeypatch.setattr(dependencies.platform, "installable", lambda key: True)
    monkeypatch.setattr(dependencies.platform, "package_manager_available", lambda: True)
    return calls


async def test_languages_step_offers_all_six_in_registry_order(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch)
        checkboxes = list(pilot.app.screen.query("EnterOnlyCheckbox"))
        assert [str(box.label) for box in checkboxes] == [
            "Chinese",
            "German",
            "Italian",
            "French",
            "English",
            "Spanish",
        ]
        # All of it, Next included, fits an 80x24 terminal.
        assert pilot.app.screen.query_one("#next-button").region.bottom <= 24


def test_checks_text_labels_a_language_check_with_the_language():
    lines = _checks_text(_all_ok_checks()).plain.splitlines()
    # Widened to the longest label, still right-aligned in its brackets.
    assert lines[0].startswith("[required] pandoc")
    assert lines[2].startswith("[ Chinese] xeCJK")


def test_checks_text_widens_the_label_column_for_long_language_lists():
    checks = [
        _FakeCheck("pandoc", required=True, ok=True),
        _FakeCheck("xeCJK", required=False, ok=True, needed_for=("Chinese", "Japanese")),
    ]
    lines = _checks_text(checks).plain.splitlines()
    assert lines[0].startswith("[" + " " * 9 + "required] pandoc")
    assert lines[1].startswith("[Chinese, Japanese] xeCJK")


async def test_step_one_does_not_block_on_a_missing_language_dependency(monkeypatch):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _advance_past_dependencies(pilot, monkeypatch, _cjk_missing_checks)
        assert isinstance(pilot.app.screen, NameScreen)


async def test_german_only_proceeds_with_xecjk_missing(monkeypatch, install_runs):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch, _cjk_missing_checks)
        await pilot.click("#language-german")
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, TreeLocationScreen)
    assert install_runs["installs"] == []


async def test_chinese_with_xecjk_missing_offers_to_install(monkeypatch, install_runs):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch, _cjk_missing_checks)
        await pilot.click("#language-chinese")
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, ConfirmDialog)
        message = pilot.app.screen.message
        assert message.startswith("Chinese needs xeCJK, which is missing. Install it now?")
        assert "`" not in message and "tlmgr" not in message and "sudo" not in message


async def test_declining_the_offer_stays_on_languages_and_names_what_is_missing(
    monkeypatch, install_runs
):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch, _cjk_missing_checks)
        await pilot.click("#language-chinese")
        await pilot.click("#next-button")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        assert isinstance(pilot.app.screen, LanguagesScreen)
        error = pilot.app.screen.query_one("#languages-error")
        assert error.display
        text = str(error.render())
        assert "Chinese needs xeCJK, which is missing." in text
        assert "tlmgr" not in text and "`" not in text
        assert "untick" in text
    assert install_runs["installs"] == []


async def test_a_dependency_the_platform_cannot_install_still_blocks_next(
    monkeypatch, install_runs
):
    from vimdiomas.tui.screens import dependencies

    monkeypatch.setattr(dependencies.platform, "installable", lambda key: False)
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch, _cjk_missing_checks)
        await pilot.click("#language-chinese")
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, LanguagesScreen)
        assert pilot.app.screen.query_one("#languages-error").display


async def test_accepting_the_offer_proceeds_once_the_recheck_is_clean(
    monkeypatch, install_runs
):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch, _cjk_missing_checks)
        # Step 3's own check finds it missing; after the install, it is there.
        _sequence(monkeypatch, _cjk_missing_checks, _all_ok_checks)
        await pilot.click("#language-chinese")
        await pilot.click("#next-button")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        assert isinstance(pilot.app.screen, TreeLocationScreen)
        assert pilot.app.languages == ["Chinese"]
    assert install_runs["installs"] == [["xecjk"]]


async def test_accepting_but_still_missing_stays_on_languages(monkeypatch, install_runs):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_languages(pilot, monkeypatch, _cjk_missing_checks)
        await pilot.click("#language-chinese")
        await pilot.click("#next-button")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        assert isinstance(pilot.app.screen, LanguagesScreen)
        assert pilot.app.screen.query_one("#languages-error").display
    assert install_runs["installs"] == [["xecjk"]]


async def test_a_full_run_choosing_italian_writes_its_tree_and_config(monkeypatch, tmp_path):
    app = WizardApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await _reach_tree_location(pilot, monkeypatch, languages=("Italian",))
        root = tmp_path / "Trees"
        pilot.app.screen.query_one("#root-field").value = str(root)
        await pilot.click("#next-button")
        await pilot.pause()
        assert pilot.app.screen.language == "Italian"
        await _advance_through_input_methods(pilot)

    assert (root / "tree-Italian" / "Vocabulary").is_dir()
    assert (root / "tree-Italian" / "Grammar").is_dir()
    assert [language.name for language in load_config().languages] == ["Italian"]


# -- Sprint 8 M3: step 1's Install missing -----------------------------------


def _keyed(name, key, ok, required=False, needed_for=()):
    return _FakeCheck(name, required=required, ok=ok, key=key, needed_for=needed_for)


def _step_one_checks(pandoc_ok=False, switcher_ok=False, xecjk_ok=False):
    """pandoc (required), macism (optional) and xeCJK (Chinese's own)."""
    return [
        _keyed("pandoc", "pandoc", pandoc_ok, required=True),
        _keyed("xelatex", "xelatex", True, required=True),
        _keyed("xeCJK", "xecjk", xecjk_ok, needed_for=("Chinese",)),
        _keyed("macism", "input-switcher", switcher_ok),
    ]


@pytest.fixture
def installing(monkeypatch):
    """Step 1's install with no real process: the platform can install every
    key and its package manager is there. `installer.run` is recorded and
    swaps `doctor.run`'s answer for `calls["after"]`, as an install would."""
    from vimdiomas.tui.screens import wizard

    calls = {"installs": [], "state": _step_one_checks(), "after": None}
    monkeypatch.setattr(wizard.doctor, "run", lambda: list(calls["state"]))
    monkeypatch.setattr(wizard.platform, "installable", lambda key: True)
    monkeypatch.setattr(wizard.platform, "package_manager_available", lambda: True)
    monkeypatch.setattr(wizard.platform, "PACKAGE_MANAGER", "Homebrew")

    def fake_run(app, checks):
        calls["installs"].append([check.name for check in checks])
        if calls["after"] is not None:
            calls["state"] = calls["after"]

    monkeypatch.setattr(wizard.installer, "run", fake_run)
    return calls


def _install_button(pilot):
    return pilot.app.screen.query_one("#install-button")


def _error(pilot):
    return pilot.app.screen.query_one("#dependencies-error")


def _error_text(pilot):
    return str(_error(pilot).render())


async def _recheck_settled(pilot):
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


async def test_install_missing_is_shown_for_a_missing_required_or_optional_check(installing):
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        assert _install_button(pilot).display
        assert str(_install_button(pilot).label) == "Install missing"


async def test_install_missing_is_shown_for_an_optional_check_alone(installing):
    installing["state"] = _step_one_checks(pandoc_ok=True)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        assert _install_button(pilot).display


async def test_install_missing_is_hidden_when_only_a_language_check_is_missing(installing):
    installing["state"] = _step_one_checks(pandoc_ok=True, switcher_ok=True)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        assert not _install_button(pilot).display


async def test_install_missing_is_hidden_when_the_platform_cannot_install_it(
    installing, monkeypatch
):
    from vimdiomas.tui.screens import wizard

    monkeypatch.setattr(wizard.platform, "installable", lambda key: False)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        assert not _install_button(pilot).display


async def test_install_missing_comes_first_and_has_the_focus(installing):
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        ids = [button.id for button in pilot.app.screen.query("Button") if button.display]
        assert ids == ["install-button", "recheck-button", "next-button"]
        assert pilot.app.focused is _install_button(pilot)


async def test_focus_starts_on_recheck_when_nothing_can_be_installed(installing):
    installing["state"] = _step_one_checks(pandoc_ok=True, switcher_ok=True)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        assert pilot.app.focused.id != "install-button"


async def test_tab_visits_install_missing_while_shown_and_skips_it_when_hidden(installing):
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        seen = []
        for _ in range(3):
            await pilot.press("tab")
            await pilot.pause()
            seen.append(pilot.app.focused.id)
        assert seen == ["recheck-button", "next-button", "install-button"]

    installing["state"] = _step_one_checks(pandoc_ok=True, switcher_ok=True)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        seen = set()
        for _ in range(4):
            await pilot.press("tab")
            await pilot.pause()
            seen.add(pilot.app.focused.id)
        assert seen == {"recheck-button", "next-button"}


async def test_install_missing_asks_first_naming_what_is_missing_and_no_command(installing):
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, ConfirmDialog)
        assert dialog.message == (
            "pandoc and macism are missing. Install them now? "
            "Your password may be asked for in the terminal."
        )
        assert "`" not in dialog.message
    assert installing["installs"] == []


async def test_a_single_missing_check_is_worded_in_the_singular(installing):
    installing["state"] = _step_one_checks(switcher_ok=True)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert pilot.app.screen.message == (
            "pandoc is missing. Install it now? Your password may be asked for in the terminal."
        )


@pytest.mark.parametrize("key", ["n", "escape"])
async def test_declining_install_missing_does_nothing(installing, key):
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press(key)
        await pilot.pause()
        assert isinstance(pilot.app.screen, DependenciesScreen)
        assert _install_button(pilot).display
        assert not _error(pilot).display
    assert installing["installs"] == []


async def test_accepting_installs_what_is_missing_then_rechecks_and_hides_the_button(installing):
    installing["after"] = _step_one_checks(pandoc_ok=True, switcher_ok=True)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("y")
        await _recheck_settled(pilot)

        # The language's own check is not what it installs.
        assert installing["installs"] == [["pandoc", "macism"]]
        lines = pilot.app.screen.query_one("#dependencies-list").render().plain.splitlines()
        assert [line.endswith("ok") for line in lines] == [True, True, False, True]
        assert not _install_button(pilot).display
        assert not _error(pilot).display
        assert pilot.app.focused.id == "next-button"


async def test_after_a_partial_install_the_button_stays_and_names_what_is_left(installing):
    installing["after"] = _step_one_checks(pandoc_ok=True, switcher_ok=False)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("y")
        await _recheck_settled(pilot)

        assert _install_button(pilot).display
        assert _error(pilot).display
        assert _error_text(pilot) == "Still missing: macism."


async def test_pressing_it_again_installs_only_what_is_left(installing):
    installing["after"] = _step_one_checks(pandoc_ok=True, switcher_ok=False)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("y")
        await _recheck_settled(pilot)

        installing["after"] = _step_one_checks(pandoc_ok=True, switcher_ok=True)
        await pilot.click("#install-button")
        await pilot.pause()
        await pilot.press("y")
        await _recheck_settled(pilot)

        assert installing["installs"] == [["pandoc", "macism"], ["macism"]]
        assert not _install_button(pilot).display
        assert not _error(pilot).display


async def test_a_recheck_after_the_install_clears_the_still_missing_line(installing):
    installing["after"] = _step_one_checks(pandoc_ok=True, switcher_ok=False)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.press("y")
        await _recheck_settled(pilot)
        assert _error(pilot).display

        await pilot.click("#recheck-button")
        await _recheck_settled(pilot)
        assert not _error(pilot).display


async def test_without_a_package_manager_a_line_says_so_and_nothing_runs(installing, monkeypatch):
    from vimdiomas.tui.screens import wizard

    monkeypatch.setattr(wizard.platform, "package_manager_available", lambda: False)
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DependenciesScreen)
        assert _error(pilot).display
        assert _error_text(pilot) == "Homebrew isn't installed, so Vimdiomas can't install anything."
    assert installing["installs"] == []


async def test_next_still_blocks_on_a_missing_required_check_without_a_hint(installing):
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        await pilot.click("#next-button")
        await pilot.pause()
        assert isinstance(pilot.app.screen, DependenciesScreen)
        assert _error_text(pilot) == "A required dependency is still missing."


async def test_nothing_on_step_one_shows_a_command_or_a_link(installing):
    forbidden = ("brew", "pacman", "tlmgr", "sudo", "`", "http", "<--")
    async with WizardApp().run_test() as pilot:
        await pilot.pause()
        shown = [
            pilot.app.screen.query_one("#dependencies-list").render().plain,
            str(pilot.app.screen.query_one("#footer-hint").render()),
        ]
        await pilot.press("enter")
        await pilot.pause()
        shown.append(pilot.app.screen.message)
        await pilot.press("n")
        await pilot.pause()
        await pilot.click("#next-button")
        await pilot.pause()
        shown.append(_error_text(pilot))
        for text in shown:
            assert not any(word in text.lower() for word in forbidden), text
