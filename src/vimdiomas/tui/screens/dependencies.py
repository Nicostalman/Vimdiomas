"""What to do when a language needs a dependency the machine doesn't have
(Sprint 6 M7): the wizard's languages step and Settings' *Add a language* both
meet it, so both route through here and cannot word it differently
(`design.md`'s *A language's missing dependencies*).

Only the dependencies a language itself needs — xeCJK and the CJK font — are
ever offered for installation. Anything every install needs (`pandoc`,
`xelatex`) is only reported: the wizard's first step already did.
"""

import shlex
import subprocess
from collections.abc import Callable

from textual.app import App

from vimdiomas import doctor
from vimdiomas.tui.screens.base import ConfirmDialog


def _join(names: list[str]) -> str:
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + f" and {names[-1]}"


def _needs(names: list[str]) -> str:
    return "needs" if len(names) == 1 else "need"


def _languages_needing(check: doctor.Check, languages: list[str]) -> list[str]:
    return [name for name in check.needed_for if name in languages]


def refusal(missing: list[doctor.Check], languages: list[str]) -> str:
    """One line per missing dependency: who needs it, and how to get it — the
    platform's command, or the check's own message when there is none."""
    lines = []
    for check in missing:
        needers = _languages_needing(check, languages)
        if needers:
            line = f"{_join(needers)} {_needs(needers)} {check.name}, which is missing."
        elif check.detail:
            line = f"{check.name} missing: {check.detail}."
        else:
            line = f"{check.name} is missing."
        if check.install:
            line += f" Install it with `{check.install}`."
        elif check.message:
            line += f" {check.message}"
        lines.append(line)
    return "\n".join(lines)


def _offerable(missing: list[doctor.Check]) -> bool:
    """An offer needs a command for every missing dependency, and only
    language dependencies are installed from here."""
    return all(check.needed_for and check.install for check in missing)


def _offer_text(missing: list[doctor.Check], languages: list[str]) -> str:
    needing = [name for name in languages if any(name in check.needed_for for check in missing)]
    needers = _join(needing)
    names = _join([check.name for check in missing])
    plural = len(missing) > 1
    head = (
        f"{needers} {_needs(needing)} {names}, which {'are' if plural else 'is'} missing. "
        f"Install {'them' if plural else 'it'} now?"
    )
    if plural:
        commands = "\n".join(f"`{check.install}`" for check in missing)
        return f"{head} This runs, in your terminal:\n{commands}"
    return f"{head} This runs `{missing[0].install}` in your terminal."


def _install(app: App, missing: list[doctor.Check]) -> list[str]:
    """Run each missing dependency's command in the user's terminal, with the
    TUI suspended so `sudo` can ask for a password. Returns what went wrong
    running them, one line each; a command failing is reported by the recheck,
    which is the real test."""
    problems = []
    with app.suspend():
        for check in missing:
            print(f"\n$ {check.install}")
            try:
                subprocess.run(shlex.split(check.install), check=False)
            except (OSError, ValueError) as exc:
                problems.append(f"Could not run `{check.install}`: {exc}")
                print(f"Could not run it: {exc}")
        try:
            input("\nPress Enter to return to Vimdiomas.")
        except EOFError:
            pass
    return problems


def ensure_dependencies(
    app: App, languages: list[str], on_done: Callable[[str | None], None]
) -> None:
    """Make sure `languages` have what they need, then call `on_done(None)`;
    or call `on_done(reason)` with the line explaining what is still missing.

    Nothing missing: `on_done(None)` at once. Something missing and installable:
    ask first, then install, then check again — the recheck decides, not the
    exit code of a command. Not installable, declined, or still missing:
    refused. Never raises (`design.md`'s *Failures are reported, never fatal*).
    """
    missing = doctor.missing_for(doctor.run(), languages)
    if not missing:
        on_done(None)
        return
    if not _offerable(missing):
        on_done(refusal(missing, languages))
        return

    def _answered(confirmed: bool | None) -> None:
        if not confirmed:
            on_done(refusal(missing, languages))
            return
        problems = _install(app, missing)
        still_missing = doctor.missing_for(doctor.run(), languages)
        if not still_missing:
            on_done(None)
            return
        reason = refusal(still_missing, languages)
        on_done("\n".join([*problems, reason]) if problems else reason)

    app.push_screen(ConfirmDialog(_offer_text(missing, languages)), _answered)
