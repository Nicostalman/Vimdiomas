"""Runs the platform's install commands for the dependencies that are missing
(Sprint 8 M3). Step 1's *Install missing*, the wizard's languages step and
Settings' *Add a language* all install through here, so the sequence is the
platform's alone and no screen shows a command (`design.md`'s *Installing
missing dependencies*).

The commands run in the user's own terminal with the TUI suspended, so `sudo`
and the BasicTeX installer can ask for a password. Nothing about the run is
reported to the TUI: the caller's recheck decides what is still missing."""

import shlex
import subprocess

from textual.app import App

from vimdiomas import doctor, platform


def join_names(names: list[str]) -> str:
    """`a`, `a and b`, `a, b and c`."""
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + f" and {names[-1]}"


def run_command(argv: list[str]) -> bool:
    """Print `argv` as `$ <command>`, run it without a shell, and say whether
    it exited 0. A command that can't be started is reported in the terminal
    and counts as failed."""
    print(f"$ {shlex.join(argv)}")
    try:
        return subprocess.run(argv, check=False).returncode == 0
    except OSError as exc:
        print(f"Could not run it: {exc}")
        return False


def run(app: App, checks: list[doctor.Check]) -> None:
    """Install what `checks` report missing, with `app` suspended. Never
    raises."""
    with app.suspend():
        print(f"\nInstalling {join_names([check.name for check in checks])}.\n")
        try:
            platform.install(
                [check.key for check in checks], run_command, doctor.missing_latex_packages
            )
        except Exception as exc:  # the terminal shows it; the recheck decides
            print(f"Could not finish: {exc}")
        platform.extend_path()
        try:
            input("\nPress Enter to return to Vimdiomas.")
        except EOFError:
            pass
