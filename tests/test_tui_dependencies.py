"""The install offer shared by the wizard and Settings (Sprint 6 M7; Sprint 8
M3: the offer shows no command, and the install goes through `installer`)."""

import pytest
from textual.app import App

from vimdiomas import doctor
from vimdiomas.tui.screens import dependencies
from vimdiomas.tui.screens.base import ConfirmDialog

PANDOC = doctor.Check("pandoc", "pandoc", required=True, ok=True)


def _xecjk(ok=False):
    return doctor.Check("xeCJK", "xecjk", required=False, ok=ok, needed_for=("Chinese",))


def _font(ok=False):
    return doctor.Check("Songti SC", "cjk-font", required=False, ok=ok, needed_for=("Chinese",))


class _Harness(App):
    pass


@pytest.fixture
def runs(monkeypatch):
    """Records each install the offer runs, with no real process; the platform
    can install every language dependency, and its package manager is there."""
    calls = {"installs": []}

    def fake_run(app, checks):
        calls["installs"].append([check.key for check in checks])

    monkeypatch.setattr(dependencies.installer, "run", fake_run)
    monkeypatch.setattr(dependencies.platform, "installable", lambda key: True)
    monkeypatch.setattr(dependencies.platform, "package_manager_available", lambda: True)
    monkeypatch.setattr(dependencies.platform, "PACKAGE_MANAGER", "Homebrew")
    return calls


def _checks_then(monkeypatch, *states):
    """`doctor.run` returns each state in turn, the last one repeating."""
    remaining = list(states)

    def run():
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    monkeypatch.setattr(dependencies.doctor, "run", run)


def _no_command(text):
    assert "`" not in text
    for word in ("brew", "pacman", "tlmgr", "sudo", "install it with", "http"):
        assert word not in text.lower(), word


async def test_nothing_missing_calls_back_at_once(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(ok=True)])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert results == [None]
    assert runs["installs"] == []


async def test_a_language_that_does_not_need_it_is_not_asked_about_it(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["German"], results.append)
        await pilot.pause()
    assert results == [None]


async def test_a_dependency_the_platform_cannot_install_refuses_without_a_dialog(
    monkeypatch, runs
):
    monkeypatch.setattr(dependencies.platform, "installable", lambda key: key != "xecjk")
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert results == ["Chinese needs xeCJK, which is missing."]
    assert runs["installs"] == []


async def test_one_dependency_that_cannot_be_installed_means_no_offer_for_any(monkeypatch, runs):
    monkeypatch.setattr(dependencies.platform, "installable", lambda key: key != "cjk-font")
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert "Chinese needs xeCJK, which is missing." in results[0]
    assert "Songti SC" in results[0]
    _no_command(results[0])


async def test_a_missing_required_dependency_is_reported_not_offered(monkeypatch, runs):
    pandoc = doctor.Check("pandoc", "pandoc", required=True, ok=False)
    _checks_then(monkeypatch, [pandoc])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["German"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert results == ["pandoc is missing."]
    assert runs["installs"] == []


async def test_a_missing_package_manager_refuses_with_its_line(monkeypatch, runs):
    monkeypatch.setattr(dependencies.platform, "package_manager_available", lambda: False)
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert results == [
        "Chinese needs xeCJK, which is missing.\n"
        "Homebrew isn't installed, so Vimdiomas can't install it."
    ]
    assert runs["installs"] == []


async def test_a_missing_package_manager_says_them_for_several(monkeypatch, runs):
    monkeypatch.setattr(dependencies.platform, "package_manager_available", lambda: False)
    monkeypatch.setattr(dependencies.platform, "PACKAGE_MANAGER", "pacman")
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
    assert results[0].endswith("pacman isn't installed, so Vimdiomas can't install them.")


async def test_the_offer_names_the_dependency_and_no_command(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], lambda error: None)
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, ConfirmDialog)
        assert dialog.message == (
            "Chinese needs xeCJK, which is missing. Install it now? "
            "Your password may be asked for in the terminal."
        )
        _no_command(dialog.message)


async def test_the_offer_names_every_dependency_when_several_are_missing(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font()])
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], lambda error: None)
        await pilot.pause()
        message = pilot.app.screen.message
        assert message == (
            "Chinese needs xeCJK and Songti SC, which are missing. Install them now? "
            "Your password may be asked for in the terminal."
        )
        _no_command(message)


async def test_declining_refuses_and_installs_nothing(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
    assert results == ["Chinese needs xeCJK, which is missing."]
    assert runs["installs"] == []


async def test_escape_declines_too(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
    assert len(results) == 1 and results[0] is not None
    assert runs["installs"] == []


async def test_accepting_installs_the_missing_checks_then_rechecks(monkeypatch, runs):
    _checks_then(
        monkeypatch,
        [PANDOC, _xecjk(), _font()],
        [PANDOC, _xecjk(ok=True), _font(ok=True)],
    )
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
    assert results == [None]
    assert runs["installs"] == [["xecjk", "cjk-font"]]


async def test_accepting_but_still_missing_names_what_is_left_and_no_command(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()], [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
    assert results == ["Chinese needs xeCJK, which is missing."]


def test_refusal_names_each_language_that_needs_the_dependency():
    check = doctor.Check(
        "xeCJK", "xecjk", required=False, ok=False, needed_for=("Chinese", "Japanese")
    )
    assert dependencies.refusal([check], ["Japanese", "Chinese", "German"]) == (
        "Chinese and Japanese need xeCJK, which is missing."
    )


def test_refusal_words_a_check_with_a_detail_as_what_is_missing():
    check = doctor.Check(
        "LaTeX packages", "latex-packages", required=True, ok=False, detail="caption, xcolor"
    )
    assert dependencies.refusal([check], ["German"]) == "LaTeX packages missing: caption, xcolor."


def test_refusal_for_a_missing_tex_names_what_is_missing_only():
    check = doctor.Check(
        "LaTeX packages",
        "latex-packages",
        required=True,
        ok=False,
        detail="needs a TeX distribution",
    )
    assert dependencies.refusal([check], []) == (
        "LaTeX packages missing: needs a TeX distribution."
    )


def test_a_failing_latex_packages_check_is_never_offered(monkeypatch):
    # Not a language's own: step 1 installs it.
    monkeypatch.setattr(dependencies.platform, "installable", lambda key: True)
    check = doctor.Check("LaTeX packages", "latex-packages", required=True, ok=False)
    assert not dependencies._installable([check])
