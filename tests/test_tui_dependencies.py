"""The install offer shared by the wizard and Settings (Sprint 6 M7)."""

from contextlib import contextmanager

import pytest
from textual.app import App
from textual.widgets import Static

from vimdiomas import doctor
from vimdiomas.tui.screens import dependencies
from vimdiomas.tui.screens.base import ConfirmDialog

PANDOC = doctor.Check("pandoc", required=True, ok=True)


def _xecjk(ok=False, install="sudo tlmgr install xecjk"):
    return doctor.Check(
        "xeCJK",
        required=False,
        ok=ok,
        message="xeCJK not found",
        needed_for=("Chinese",),
        install=install,
    )


def _font(ok=False, install=""):
    return doctor.Check(
        "Songti SC",
        required=False,
        ok=ok,
        message="CJK font not found at /x/Songti.ttc (Songti SC)",
        needed_for=("Chinese",),
        install=install,
    )


class _Harness(App):
    pass


@pytest.fixture
def runs(monkeypatch):
    """Records each command run and each suspend, with no real process."""
    calls = {"commands": [], "suspends": 0, "inputs": 0}

    def fake_run(command, **kwargs):
        calls["commands"].append(command)

    def fake_input(prompt=""):
        calls["inputs"] += 1
        return ""

    monkeypatch.setattr(dependencies.subprocess, "run", fake_run)
    monkeypatch.setattr("builtins.input", fake_input)
    return calls


def _fake_suspend(app, calls):
    @contextmanager
    def suspend():
        calls["suspends"] += 1
        yield

    app.suspend = suspend


def _checks_then(monkeypatch, *states):
    """`doctor.run` returns each state in turn, the last one repeating."""
    remaining = list(states)

    def run():
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    monkeypatch.setattr(dependencies.doctor, "run", run)


async def test_nothing_missing_calls_back_at_once(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(ok=True)])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert results == [None]
    assert runs["commands"] == []


async def test_a_language_that_does_not_need_it_is_not_asked_about_it(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["German"], results.append)
        await pilot.pause()
    assert results == [None]


async def test_no_command_refuses_without_a_dialog(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(install="")])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert len(results) == 1
    assert "Chinese needs xeCJK, which is missing." in results[0]
    assert "xeCJK not found" in results[0]
    assert runs["commands"] == []


async def test_one_dependency_without_a_command_means_no_offer_for_any(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font(install="")])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert "Install it with `sudo tlmgr install xecjk`." in results[0]
    assert "Songti SC" in results[0]


async def test_a_missing_required_dependency_is_reported_not_offered(monkeypatch, runs):
    pandoc = doctor.Check(
        "pandoc", required=True, ok=False, message="pandoc not found", install="brew install pandoc"
    )
    _checks_then(monkeypatch, [pandoc])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["German"], results.append)
        await pilot.pause()
        assert not isinstance(pilot.app.screen, ConfirmDialog)
    assert results[0].startswith("pandoc is missing.")
    assert runs["commands"] == []


async def test_the_offer_names_the_dependency_and_the_command(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], lambda error: None)
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, ConfirmDialog)
        assert dialog.message == (
            "Chinese needs xeCJK, which is missing. Install it now? "
            "This runs `sudo tlmgr install xecjk` in your terminal."
        )


async def test_the_offer_lists_every_command_when_several_are_missing(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk(), _font(install="sudo pacman -S noto-fonts-cjk")])
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], lambda error: None)
        await pilot.pause()
        message = pilot.app.screen.message
        assert "xeCJK and Songti SC, which are missing. Install them now?" in message
        assert "`sudo tlmgr install xecjk`" in message
        assert "`sudo pacman -S noto-fonts-cjk`" in message


async def test_declining_refuses_and_runs_nothing(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        _fake_suspend(pilot.app, runs)
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
    assert len(results) == 1
    assert "Install it with `sudo tlmgr install xecjk`." in results[0]
    assert runs["commands"] == []
    assert runs["suspends"] == 0


async def test_escape_declines_too(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
    assert len(results) == 1 and results[0] is not None


async def test_accepting_runs_exactly_the_listed_commands_without_a_shell(monkeypatch, runs):
    _checks_then(
        monkeypatch,
        [PANDOC, _xecjk(), _font(install="sudo pacman -S noto-fonts-cjk")],
        [PANDOC, _xecjk(ok=True), _font(ok=True)],
    )
    results = []
    async with _Harness().run_test() as pilot:
        _fake_suspend(pilot.app, runs)
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
    assert results == [None]
    assert runs["commands"] == [
        ["sudo", "tlmgr", "install", "xecjk"],
        ["sudo", "apt", "install", "fonts-noto-cjk"],
    ]
    assert runs["suspends"] == 1
    assert runs["inputs"] == 1


async def test_accepting_but_still_missing_names_what_is_left(monkeypatch, runs):
    _checks_then(monkeypatch, [PANDOC, _xecjk()], [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        _fake_suspend(pilot.app, runs)
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
    assert len(results) == 1
    assert "Chinese needs xeCJK, which is missing." in results[0]
    assert "`sudo tlmgr install xecjk`" in results[0]


async def test_a_command_that_cannot_run_is_reported_not_raised(monkeypatch, runs):
    def broken_run(command, **kwargs):
        raise FileNotFoundError("sudo")

    monkeypatch.setattr(dependencies.subprocess, "run", broken_run)
    _checks_then(monkeypatch, [PANDOC, _xecjk()], [PANDOC, _xecjk()])
    results = []
    async with _Harness().run_test() as pilot:
        _fake_suspend(pilot.app, runs)
        dependencies.ensure_dependencies(pilot.app, ["Chinese"], results.append)
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()
    assert len(results) == 1
    assert "Could not run `sudo tlmgr install xecjk`" in results[0]
    assert "Chinese needs xeCJK" in results[0]


def test_refusal_names_each_language_that_needs_the_dependency():
    check = doctor.Check(
        "xeCJK", required=False, ok=False, needed_for=("Chinese", "Japanese"), install="x y"
    )
    assert dependencies.refusal([check], ["Japanese", "Chinese", "German"]) == (
        "Chinese and Japanese need xeCJK, which is missing. Install it with `x y`."
    )
