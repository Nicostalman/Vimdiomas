import argparse
import sys
from pathlib import Path

from vimdiomas import doctor
from vimdiomas.compile import compile_all
from vimdiomas.config import CONFIG_PATH, ConfigNotFoundError, load_config, migrate_legacy_paths
from vimdiomas.languages import get_language, is_functional
from vimdiomas.platform import extend_path
from vimdiomas.tui.app import VimdiomasApp
from vimdiomas.tui.screens.wizard import WizardApp

NO_CONFIG_MESSAGE = f"""\
No config found at {CONFIG_PATH}.

Example:

    user_name = "Your Name"
    root = "/Users/you/Documents/Vimdiomas"

    [[languages]]
    name = "Chinese"
"""


def _run_wizard() -> None:
    config = WizardApp().run()
    if config is None:
        return
    VimdiomasApp(config).run()


def _tui() -> None:
    if not CONFIG_PATH.exists():
        _run_wizard()
        return
    VimdiomasApp(load_config()).run()


def _compile(force: bool = False) -> None:
    config = load_config()
    any_failed = False
    for language in config.languages:
        if not is_functional(language.name):
            continue
        report = compile_all(
            config.tree_root(language.name), kind=get_language(language.name).kind, force=force
        )
        if report.compiled:
            print(f"{language.name}: compiled {len(report.compiled)} file(s):")
            for path in report.compiled:
                print(f"  {path}")
        elif not report.failed:
            print(f"{language.name}: everything is up to date.")
        if report.failed:
            # Sprint 6 M2, #12: reported, not a traceback — and a non-zero
            # exit, so a script can tell.
            any_failed = True
            print(f"{language.name}: {len(report.failed)} file(s) failed:", file=sys.stderr)
            for failure in report.failed:
                print(f"  {failure.source}", file=sys.stderr)
                for line in failure.message.splitlines():
                    print(f"    {line}", file=sys.stderr)
        if report.warnings:
            # Sprint 6 M3, #4 and M9: the file compiled, so the exit code is
            # unaffected. Grouped by file, as the Compile screen groups them.
            print(f"{language.name}: {len(report.warnings)} warning(s):", file=sys.stderr)
            by_source: dict[Path, list[str]] = {}
            for warning in report.warnings:
                by_source.setdefault(warning.source, []).append(warning.message)
            for source, messages in by_source.items():
                print(f"  {source}", file=sys.stderr)
                for message in messages:
                    for line in message.splitlines():
                        print(f"    {line}", file=sys.stderr)
    if any_failed:
        raise SystemExit(1)


def _doctor() -> None:
    checks = doctor.run()
    for check in checks:
        if check.ok:
            status = "ok"
        else:
            status = f"missing: {check.detail}" if check.detail else "missing"
        print(f"[{doctor.label(check)}] {check.name}: {status}")

    # What blocks depends on the languages: with a config, those it
    # registers; without one, only what every install needs (Sprint 6 M7).
    try:
        languages = [language.name for language in load_config().languages]
    except ConfigNotFoundError:
        languages = []
    if doctor.missing_for(checks, languages):
        raise SystemExit(1)


def main() -> None:
    migrate_legacy_paths()
    # Before anything dispatches, so the TUI, `compile` and `doctor` all see
    # the package manager's tools, even from a shell that never put them on
    # PATH (Sprint 8 M3).
    extend_path()
    # Dev-only escape hatch, checked before argparse rather than registered
    # as a subparser: opens the wizard even with a config already in place,
    # without moving it aside first. Kept out of `argparse` entirely (not
    # just `help=argparse.SUPPRESS`, which still leaks "wizard" into
    # `--help`'s usage/choices line) so it stays fully invisible to
    # `--help` — the wizard's real, documented trigger stays "no config
    # exists". Finishing it still overwrites CONFIG_PATH via save_config,
    # so testing against a real config means backing out with `q` before
    # the last step rather than finishing it.
    if sys.argv[1:2] == ["wizard"]:
        _run_wizard()
        return

    parser = argparse.ArgumentParser(prog="vimdiomas")
    subparsers = parser.add_subparsers(dest="command")
    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("--force", action="store_true")
    subparsers.add_parser("doctor")

    args = parser.parse_args()

    try:
        if args.command == "compile":
            _compile(force=args.force)
        elif args.command == "doctor":
            _doctor()
        else:
            _tui()
    except ConfigNotFoundError:
        print(NO_CONFIG_MESSAGE)
        raise SystemExit(1)
