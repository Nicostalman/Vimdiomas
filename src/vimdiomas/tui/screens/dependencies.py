"""What to do when a language needs a dependency the machine doesn't have
(Sprint 6 M7): the wizard's languages step and Settings' *Add a language* both
meet it, so both route through here and cannot word it differently
(`design.md`'s *A language's missing dependencies*).

Only the dependencies a language itself needs — xeCJK and the CJK font — are
offered from here. Anything every install needs (`pandoc`, `xelatex`) is only
reported: the wizard's first step already offered to install it (Sprint 8 M3).
Nothing here shows a command or says how to install anything.
"""

from collections.abc import Callable

from textual.app import App

from vimdiomas import doctor, installer, platform
from vimdiomas.tui.screens.base import ConfirmDialog


def _needs(names: list[str]) -> str:
    return "needs" if len(names) == 1 else "need"


def _languages_needing(check: doctor.Check, languages: list[str]) -> list[str]:
    return [name for name in check.needed_for if name in languages]


def refusal(missing: list[doctor.Check], languages: list[str]) -> str:
    """One line per missing dependency: who needs it, or what is missing. No
    command and no hint on how to get it."""
    lines = []
    for check in missing:
        needers = _languages_needing(check, languages)
        if needers:
            lines.append(f"{installer.join_names(needers)} {_needs(needers)} {check.name}, which is missing.")
        elif check.detail:
            lines.append(f"{check.name} missing: {check.detail}.")
        else:
            lines.append(f"{check.name} is missing.")
    return "\n".join(lines)


def _installable(missing: list[doctor.Check]) -> bool:
    """Whether the platform can install every missing dependency, and each is
    a language's own: the others are step 1's to install."""
    return all(check.needed_for and platform.installable(check.key) for check in missing)


def _offer_text(missing: list[doctor.Check], languages: list[str]) -> str:
    needing = [name for name in languages if any(name in check.needed_for for check in missing)]
    needers = installer.join_names(needing)
    names = installer.join_names([check.name for check in missing])
    plural = len(missing) > 1
    return (
        f"{needers} {_needs(needing)} {names}, which {'are' if plural else 'is'} missing. "
        f"Install {'them' if plural else 'it'} now? "
        "Your password may be asked for in the terminal."
    )


def ensure_dependencies(
    app: App, languages: list[str], on_done: Callable[[str | None], None]
) -> None:
    """Make sure `languages` have what they need, then call `on_done(None)`;
    or call `on_done(reason)` with the line explaining what is still missing.

    Nothing missing: `on_done(None)` at once. Something missing and installable:
    ask first, then install, then check again — the recheck decides, not the
    exit code of a command. Not installable, no package manager, declined, or
    still missing: refused. Never raises (`design.md`'s *Failures are reported,
    never fatal*).
    """
    missing = doctor.missing_for(doctor.run(), languages)
    if not missing:
        on_done(None)
        return
    if not _installable(missing):
        on_done(refusal(missing, languages))
        return
    if not platform.package_manager_available():
        pronoun = "them" if len(missing) > 1 else "it"
        on_done(
            f"{refusal(missing, languages)}\n{platform.PACKAGE_MANAGER} isn't installed, "
            f"so Vimdiomas can't install {pronoun}."
        )
        return

    def _answered(confirmed: bool | None) -> None:
        if not confirmed:
            on_done(refusal(missing, languages))
            return
        installer.run(app, missing)
        still_missing = doctor.missing_for(doctor.run(), languages)
        on_done(refusal(still_missing, languages) if still_missing else None)

    app.push_screen(ConfirmDialog(_offer_text(missing, languages)), _answered)
