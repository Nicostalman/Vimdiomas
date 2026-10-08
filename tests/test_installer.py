"""`vimdiomas.installer` (Sprint 8 M3): the one place the platform's install
commands run, in the user's terminal with the TUI suspended."""

import subprocess
from contextlib import contextmanager

import pytest

from vimdiomas import doctor, installer

PANDOC = doctor.Check("pandoc", "pandoc", required=True, ok=False)
XELATEX = doctor.Check("xelatex", "xelatex", required=True, ok=False)
NVIM = doctor.Check("nvim", "nvim", required=False, ok=False)


class _App:
    def __init__(self):
        self.suspends = 0
        self.events = []

    @contextmanager
    def suspend(self):
        self.suspends += 1
        self.events.append("suspend")
        try:
            yield
        finally:
            self.events.append("resume")


@pytest.fixture
def platform_calls(monkeypatch):
    calls = {"install": [], "extend_path": 0}

    def install(keys, run, missing_latex):
        calls["install"].append((keys, run, missing_latex))

    def extend_path():
        calls["extend_path"] += 1

    monkeypatch.setattr(installer.platform, "install", install)
    monkeypatch.setattr(installer.platform, "extend_path", extend_path)
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    return calls


def test_run_hands_the_keys_and_the_probe_to_the_platform(platform_calls):
    app = _App()
    installer.run(app, [PANDOC, XELATEX, NVIM])

    ((keys, run, missing_latex),) = platform_calls["install"]
    assert keys == ["pandoc", "xelatex", "nvim"]
    assert run is installer.run_command
    assert missing_latex is doctor.missing_latex_packages


def test_run_suspends_the_app_and_extends_path_again(platform_calls):
    app = _App()
    installer.run(app, [PANDOC])
    assert app.suspends == 1
    assert platform_calls["extend_path"] == 1


def test_run_prints_a_header_and_waits_for_enter(platform_calls, monkeypatch, capsys):
    prompts = []
    monkeypatch.setattr("builtins.input", lambda prompt="": prompts.append(prompt) or "")
    installer.run(_App(), [PANDOC, XELATEX, NVIM])
    assert "Installing pandoc, xelatex and nvim." in capsys.readouterr().out
    assert "Press Enter to return to Vimdiomas." in prompts[0]


def test_run_tolerates_the_end_of_input(platform_calls, monkeypatch):
    def eof(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    installer.run(_App(), [PANDOC])  # must not raise


def test_run_never_raises_and_still_resumes(platform_calls, monkeypatch, capsys):
    def broken(keys, run, missing_latex):
        raise RuntimeError("boom")

    monkeypatch.setattr(installer.platform, "install", broken)
    app = _App()
    installer.run(app, [PANDOC])  # must not raise
    assert app.events == ["suspend", "resume"]
    assert platform_calls["extend_path"] == 1
    assert "boom" in capsys.readouterr().out


def test_run_command_prints_the_command_and_runs_it_without_a_shell(monkeypatch, capsys):
    seen = []

    def fake_run(argv, **kwargs):
        seen.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(installer.subprocess, "run", fake_run)

    assert installer.run_command(["brew", "install", "a b"]) is True
    assert capsys.readouterr().out == "$ brew install 'a b'\n"
    ((argv, kwargs),) = seen
    assert argv == ["brew", "install", "a b"]
    assert kwargs.get("shell", False) is False
    assert kwargs["check"] is False


def test_run_command_reports_a_nonzero_exit_as_failure(monkeypatch):
    monkeypatch.setattr(
        installer.subprocess, "run", lambda argv, **kw: subprocess.CompletedProcess(argv, 1)
    )
    assert installer.run_command(["false"]) is False


def test_run_command_reports_an_oserror_as_failure(monkeypatch, capsys):
    def broken(argv, **kwargs):
        raise FileNotFoundError("sudo")

    monkeypatch.setattr(installer.subprocess, "run", broken)

    assert installer.run_command(["sudo", "x"]) is False
    assert "Could not run it: sudo" in capsys.readouterr().out


def test_join_names():
    assert installer.join_names([]) == ""
    assert installer.join_names(["a"]) == "a"
    assert installer.join_names(["a", "b"]) == "a and b"
    assert installer.join_names(["a", "b", "c"]) == "a, b and c"
