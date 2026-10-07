"""The installation wizard: runs only when no config exists yet (Sprint 4
M5). A separate `App` from `VimdiomasApp` since it has no `Config` to hold
until it produces one — its screens are pushed/popped in order (`q` on a
non-first step goes back one step, `q` on the first aborts the whole
wizard) and it exits with the finished `Config`, or `None` if quit early.
"""

import time
from pathlib import Path

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Button, Checkbox, Input, Static

from vimdiomas import doctor, install
from vimdiomas.config import Config, LanguageConfig, save_config, validate_tree_root
from vimdiomas.languages import LANGUAGES
from vimdiomas.store import ensure_tree
from vimdiomas.tui.screens.base import ConfirmDialog, FooterHint, literal
from vimdiomas.tui.screens.dependencies import ensure_dependencies
from vimdiomas.tui.screens.input_methods import (
    INPUT_METHOD_PROMPT,
    LANGUAGE_FIELD_ID,
    TRANSLATION_FIELD_ID,
    available_sources,
    compose_fields,
    read_fields,
)
from vimdiomas.tui.screens.panels import Backpanel, FormScreen, Panel, TextField

LANGUAGE_CHOICES = [language.name for language in LANGUAGES]

DEFAULT_ROOT = str(Path.home() / "Documents" / "Vimdiomas")

ABORT_MESSAGE = "Quit the installation wizard? Nothing will be saved."

# A floor under how long Recheck's spinner stays up: doctor.run() usually
# finishes in a few milliseconds (shutil.which lookups, one subprocess
# call), too fast for the animation to read as intentional rather than a
# flash of glitch.
MIN_RECHECK_SECONDS = 0.4

SPINNER_FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
SPINNER_INTERVAL = 0.1


def _checkbox_id(language: str) -> str:
    return f"language-{language.lower()}"


def _name_width(checks: list[doctor.Check]) -> int:
    """The name column's width: 10, or the longest name when one runs
    longer — Linux's "Noto Serif CJK SC" and "fcitx5 or ibus" do (Sprint 5
    M7), while every macOS name fits in 10, so its layout is unchanged."""
    return max([10, *(len(check.name) for check in checks)])


def _label_width(checks: list[doctor.Check]) -> int:
    """The bracketed label column's width: 8 (`required`), or the longest
    label when one runs longer — a check needed for several languages shows
    their names instead (Sprint 6 M7)."""
    return max([8, *(len(doctor.label(check)) for check in checks)])


def _checks_text(checks: list[doctor.Check]) -> Text:
    """One line per check, aligned into columns, ok in green / failing in
    red — a glance should be enough to see what's missing.

    A failing check shows "missing" rather than `check.message` (which can
    run long enough to be cut off at the panel's width — the CLI's `vimdiomas
    doctor` still prints the full message, this is wizard-display only)
    plus an arrow to its `url`, when it has one (macOS's CJK font doesn't —
    it ships with the OS, nothing to link to)."""
    width = _name_width(checks)
    label_width = _label_width(checks)
    text = Text()
    for index, check in enumerate(checks):
        if index:
            text.append("\n")
        label = doctor.label(check)
        text.append(f"[{label:>{label_width}}] {check.name:<{width}} ", style="dim")
        if check.ok:
            text.append("ok", style="green")
        else:
            text.append("missing", style="red")
            if check.url:
                text.append(" <-- ", style="dim")
                text.append(check.url, style="red")
    return text


def _pending_checks_text(checks: list[doctor.Check], frame: int) -> Text:
    """The same aligned layout as `_checks_text`, but every status column
    replaced with a spinner frame — dev's request: the animation should
    sit inline per dependency, not as one big indicator replacing the
    whole list."""
    spinner = SPINNER_FRAMES[frame % len(SPINNER_FRAMES)]
    width = _name_width(checks)
    label_width = _label_width(checks)
    text = Text()
    for index, check in enumerate(checks):
        if index:
            text.append("\n")
        label = doctor.label(check)
        text.append(f"[{label:>{label_width}}] {check.name:<{width}} ", style="dim")
        text.append(spinner, style="dim")
    return text


def _path_report(status: install.LinkStatus) -> Text:
    """What linking would do, in plain words, plus whether the user still
    has to touch their shell config.

    Every branch is a statement of fact the user can act on — none of them
    stops the wizard finishing (Sprint 4 M7).
    """
    text = Text()
    state = status.state

    if state is install.LinkState.NO_SCRIPT:
        text.append(
            "Vimdiomas was started in a way that has no command to link "
            "(`python -m vimdiomas`).\n",
            style="dim",
        )
        text.append(
            "Installing it as the README describes creates one.", style="dim"
        )
        return text

    link = _tilde(status.link_path)

    if state is install.LinkState.ALREADY_LINKED:
        text.append("already linked  ", style="green")
        text.append(link, style="dim")
    elif state is install.LinkState.OCCUPIED:
        text.append("in the way  ", style="red")
        text.append(f"{link}\n", style="dim")
        text.append(
            "Something else is already there, so it will be left alone.\n",
            style="dim",
        )
        text.append("To replace it yourself:\n", style="dim")
        text.append(f"  ln -sf {_tilde(status.target)} {_tilde(status.link_path)}")
    else:
        text.append("will link  ", style="green")
        text.append(f"{link}\n", style="dim")
        text.append("  -> ", style="dim")
        text.append(_tilde(status.target), style="dim")

    text.append("\n\n")
    text.append(_path_note(status.link_path.parent))
    return text


def _path_note(bin_dir: Path) -> Text:
    """Whether `bin_dir` is on `PATH`, and what Finish will do about it if
    not: add one line to the shell config, checked against the file's own
    contents so a second wizard run never duplicates it (Sprint 4 M7)."""
    text = Text()
    if install.on_path(bin_dir):
        text.append(f"{_tilde(bin_dir)} is already on your PATH.", style="dim")
        return text

    config_path = install.shell_config_path()
    if install.directory_already_in_shell_config(bin_dir):
        text.append(
            f"{_tilde(bin_dir)} is already in {_tilde(config_path)}.\n",
            style="dim",
        )
        text.append("Open a new terminal to pick it up.", style="dim")
        return text

    text.append(f"{_tilde(bin_dir)} isn't on your PATH yet.\n", style="yellow")
    text.append(f"Finish will add this line to {_tilde(config_path)}:\n", style="dim")
    text.append(f"  {install.path_export_line(bin_dir)}")
    return text


def _tilde(path: Path) -> str:
    """`~/.local/bin` rather than `/Users/you/.local/bin` — shorter, and the
    form the user recognises."""
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


class EnterOnlyCheckbox(Checkbox):
    """A `Checkbox` toggled only by `enter`, not `space` — space stays
    reserved the way it already is elsewhere (typing into a field), and a
    single clear key removes any ambiguity about how to toggle a language
    on/off. Overrides `space` to a no-op the same way `NoShiftArrowsTree`
    overrides `Tree`'s own shift-arrow defaults, rather than replacing
    `Checkbox.BINDINGS` outright (Textual merges a subclass's `BINDINGS`
    with its parent's rather than replacing them)."""

    BINDINGS = [
        Binding("space", "nothing", "Nothing", show=False),
    ]

    def action_nothing(self) -> None:
        pass


class _WizardStep(FormScreen):
    """A single-panel wizard step: `FormScreen`'s `tab` cycling, which every
    step needs (each panel holds a field or checkboxes plus a button), and
    nothing else of its own — `q` back/quit comes from `PanelScreen`.
    """


class DependenciesScreen(_WizardStep):
    """Step 1: runs `doctor.run()`. A failing required check blocks `Next`;
    `Recheck` re-runs the checks in place, without restarting the wizard.

    A check a language needs (xeCJK and the CJK font, for Chinese) is listed
    here, labelled with the language, but never blocks: which languages are
    wanted isn't known until step 3, which checks them (Sprint 6 M7)."""

    def content_ids(self) -> list[str]:
        return ["recheck-button", "next-button"]

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static("Dependencies", classes="wizard-title")
                yield Static(
                    "Checking that everything Vimdiomas needs is installed:",
                    classes="wizard-prompt",
                )
                yield Static(id="dependencies-list")
                yield Static(id="dependencies-error", classes="wizard-error")
                yield Button("Recheck", id="recheck-button")
                yield Button("Next", id="next-button")
                yield FooterHint(
                    "Tab between buttons · Enter/Space activate · q quit",
                    id="footer-hint",
                )

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#dependencies-error", Static).display = False
        self._spinner_timer = None
        self._refresh_checks()

    def _refresh_checks(self) -> None:
        self._checks = doctor.run()
        self.query_one("#dependencies-list", Static).update(_checks_text(self._checks))

    def _blocking(self) -> bool:
        return any(not check.ok and check.required for check in self._checks)

    @on(Button.Pressed, "#recheck-button")
    def _on_recheck(self, event: Button.Pressed) -> None:
        self.query_one("#dependencies-error", Static).display = False
        self.query_one("#recheck-button", Button).disabled = True
        self._spinner_frame = 0
        self._render_pending()
        self._spinner_timer = self.set_interval(SPINNER_INTERVAL, self._tick_spinner)
        self.app.run_worker(self._recheck_worker, thread=True, group="doctor-recheck")

    def _tick_spinner(self) -> None:
        self._spinner_frame += 1
        self._render_pending()

    def _render_pending(self) -> None:
        self.query_one("#dependencies-list", Static).update(
            _pending_checks_text(self._checks, self._spinner_frame)
        )

    def _recheck_worker(self) -> None:
        started = time.monotonic()
        checks = doctor.run()
        remaining = MIN_RECHECK_SECONDS - (time.monotonic() - started)
        if remaining > 0:
            time.sleep(remaining)
        self.app.call_from_thread(self._apply_recheck, checks)

    def _apply_recheck(self, checks: list[doctor.Check]) -> None:
        if self._spinner_timer is not None:
            self._spinner_timer.stop()
            self._spinner_timer = None
        self._checks = checks
        self.query_one("#dependencies-list", Static).update(_checks_text(checks))
        self.query_one("#recheck-button", Button).disabled = False

    @on(Button.Pressed, "#next-button")
    def _on_next(self, event: Button.Pressed) -> None:
        error_widget = self.query_one("#dependencies-error", Static)
        if self._blocking():
            error_widget.update(
                "A required dependency is still missing; fix it and recheck."
            )
            error_widget.display = True
            return
        error_widget.display = False
        self.app.push_screen(NameScreen())

    def action_back_or_quit(self) -> None:
        # This is always the first wizard step, so there's never a
        # previous step to pop back to — `q` here aborts the whole wizard
        # instead. `PanelScreen`'s own `self.app.pop_screen()` would be
        # wrong for a different reason than a `ScreenStackError`: `Screen
        # Stack` always carries Textual's own implicit default screen
        # underneath every pushed one, so `len(self.app.screen_stack)`
        # is at least 2 even here and a naive length check never fires —
        # verified by hand, this silently popped back to that empty
        # default screen (an unresponsive blank app) instead of exiting.
        # Confirmed first — aborting loses all progress, the same
        # "are you sure" treatment Inspect Tree's delete already gets.
        if isinstance(self.focused, Input):
            return

        def _handle(confirmed: bool | None) -> None:
            if confirmed:
                self.app.exit(None)

        self.app.push_screen(ConfirmDialog(ABORT_MESSAGE), _handle)


class NameScreen(_WizardStep):
    """Step 2: the user's name, required non-empty (M3's new-category
    rule)."""

    def content_ids(self) -> list[str]:
        return ["name-field", "next-button"]

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static("Your name", classes="wizard-title")
                yield Static(
                    "What should Vimdiomas call you?", classes="wizard-prompt"
                )
                yield TextField(placeholder="Your name", id="name-field")
                yield Static(id="name-error", classes="wizard-error")
                yield Button("Next", id="next-button")
                yield FooterHint("Enter/Next continue · q back", id="footer-hint")

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#name-error", Static).display = False
        self.query_one("#name-field", TextField).value = self.app.user_name

    def _submit(self) -> None:
        name = self.query_one("#name-field", TextField).value.strip()
        error_widget = self.query_one("#name-error", Static)
        if not name:
            error_widget.update("A name is required.")
            error_widget.display = True
            return
        error_widget.display = False
        self.app.user_name = name
        self.app.push_screen(LanguagesScreen())

    @on(Input.Submitted, "#name-field")
    def _on_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    @on(Button.Pressed, "#next-button")
    def _on_next(self, event: Button.Pressed) -> None:
        self._submit()


class LanguagesScreen(_WizardStep):
    """Step 3: every registry language offered, at least one required.

    *Next* also checks that what the chosen languages need is installed, and
    offers to install it when it isn't (Sprint 6 M7)."""

    def content_ids(self) -> list[str]:
        return [_checkbox_id(language) for language in LANGUAGE_CHOICES] + ["next-button"]

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static("Languages", classes="wizard-title")
                yield Static(
                    "Which languages would you like to set up? Choose at least one.",
                    classes="wizard-prompt",
                )
                # One row each: six bordered checkboxes (three rows apiece)
                # push Next off an 80x24 terminal (Sprint 6 M7).
                for language in LANGUAGE_CHOICES:
                    yield EnterOnlyCheckbox(language, id=_checkbox_id(language), compact=True)
                yield Static(id="languages-error", classes="wizard-error")
                yield Button("Next", id="next-button")
                yield FooterHint(
                    "Enter toggle · Tab between checkboxes · q back",
                    id="footer-hint",
                )

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#languages-error", Static).display = False
        for language in LANGUAGE_CHOICES:
            checkbox = self.query_one(f"#{_checkbox_id(language)}", EnterOnlyCheckbox)
            checkbox.value = language in self.app.languages

    def _selected(self) -> list[str]:
        return [
            language
            for language in LANGUAGE_CHOICES
            if self.query_one(f"#{_checkbox_id(language)}", EnterOnlyCheckbox).value
        ]

    @on(Button.Pressed, "#next-button")
    def _on_next(self, event: Button.Pressed) -> None:
        selected = self._selected()
        error_widget = self.query_one("#languages-error", Static)
        if not selected:
            error_widget.update("Choose at least one language.")
            error_widget.display = True
            return
        error_widget.display = False

        def _checked(error: str | None) -> None:
            if error is not None:
                error_widget.update(literal(f"{error}\nOr untick the language that needs it."))
                error_widget.display = True
                return
            self.app.languages = selected
            self.app.push_screen(TreeLocationScreen())

        ensure_dependencies(self.app, selected, _checked)


class TreeLocationScreen(_WizardStep):
    """Step 4: the root folder every selected language's tree lives under.

    It only validates and remembers the root — creating folders and writing
    the config both moved to the last input-method step (Sprint 4 M6), so
    that quitting anywhere before the real end still writes nothing, which
    is M5's standing rule.
    """

    def content_ids(self) -> list[str]:
        return ["root-field", "next-button"]

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static("Tree location", classes="wizard-title")
                yield Static(
                    "Where should your language trees live?",
                    classes="wizard-prompt",
                )
                yield TextField(value=DEFAULT_ROOT, id="root-field")
                yield Static(id="root-error", classes="wizard-error")
                yield Button("Next", id="next-button")
                yield FooterHint("Enter/Next continue · q back", id="footer-hint")

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#root-error", Static).display = False
        if self.app.root is not None:
            self.query_one("#root-field", TextField).value = str(self.app.root)

    def _next(self) -> None:
        raw = self.query_one("#root-field", TextField).value.strip()
        error_widget = self.query_one("#root-error", Static)
        if not raw:
            error_widget.update("A tree location is required.")
            error_widget.display = True
            return

        # Resolved, not just expanded: a relative answer stored as typed is
        # re-interpreted against every future process's working directory, so
        # the same command finds a different tree — or none — depending on
        # where it was launched (Sprint 6 M1, #7). The user typed the path
        # relative to the directory they are standing in now, so resolving it
        # here is what they meant.
        root = Path(raw).expanduser().resolve()
        error = validate_tree_root(root)
        if error is not None:
            error_widget.update(error)
            error_widget.display = True
            return
        error_widget.display = False

        self.app.root = root
        self.app.push_screen(InputMethodScreen(0))

    @on(Input.Submitted, "#root-field")
    def _on_submitted(self, event: Input.Submitted) -> None:
        self._next()

    @on(Button.Pressed, "#next-button")
    def _on_next(self, event: Button.Pressed) -> None:
        self._next()


class InputMethodScreen(_WizardStep):
    """Step 5..n: one per chosen language, in the order they were chosen.

    Asks which source types the language and which types the translation,
    from the sources actually enabled on the machine. Never blocks on a thin
    or empty list — the dev's call: it warns, preselects what there is, and
    lets the wizard finish, since input switching degrades to a no-op
    exactly as it already does without `macism`.

    No longer the last step: `PathScreen` follows the final language's, and
    everything that writes moved there with it (Sprint 4 M7), for the same
    reason it moved here in M6 — the wizard gained a step after the one that
    used to finish it, and M5's "quitting before the end writes nothing"
    rule has to keep holding.
    """

    def __init__(self, index: int) -> None:
        super().__init__()
        self.index = index

    @property
    def language(self) -> str:
        return self.app.languages[self.index]

    @property
    def is_last(self) -> bool:
        return self.index == len(self.app.languages) - 1

    def content_ids(self) -> list[str]:
        return [LANGUAGE_FIELD_ID, TRANSLATION_FIELD_ID, "next-button"]

    def compose(self) -> ComposeResult:
        stored = self.app.input_methods.get(self.language, ("", ""))
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static(
                    f"Input methods · {self.language}", classes="wizard-title"
                )
                yield Static(INPUT_METHOD_PROMPT, classes="wizard-prompt")
                yield from compose_fields(
                    self.language, available_sources(), stored[0], stored[1]
                )
                yield Button("Next", id="next-button")
                yield FooterHint(
                    "Enter open list · j/k move · Enter choose · Esc close · q back",
                    id="footer-hint",
                )

    def _remember(self) -> None:
        self.app.input_methods[self.language] = read_fields(self)

    @on(Button.Pressed, "#next-button")
    def _on_next(self, event: Button.Pressed) -> None:
        self._remember()
        if not self.is_last:
            self.app.push_screen(InputMethodScreen(self.index + 1))
            return
        self.app.push_screen(PathScreen())

    def action_back_or_quit(self) -> None:
        # Keep what was chosen here, so `q` forward again re-shows it —
        # same as every other step's answers surviving a walk backwards.
        self._remember()
        super().action_back_or_quit()


class PathScreen(_WizardStep):
    """The last step: puts `vimdiomas` on the user's `PATH`, then writes.

    The README's install ends with a command that only works by its full
    path (`<clone>/.venv/bin/vimdiomas`) — the wizard can't be reached any
    other way before a config exists. This step closes that gap by
    symlinking the running console script into `~/.local/bin`, so every run
    after this one is plain `vimdiomas` (Sprint 4 M7).

    It is also where the wizard writes, inheriting that from the last
    input-method step: the root and each `tree-<Language>` folder, then the
    config. M5's rule holds unchanged and now covers the symlink too — `q`
    out of here and nothing has been linked, created or saved.

    A shell that doesn't already have `~/.local/bin` on `PATH` gets exactly
    one line appended to its config on Finish (`install.ensure_on_path`),
    checked against the file's own contents first so re-running the wizard
    never adds it twice. Nothing else in that file is touched. Anything
    already sitting at the link path itself is reported and left alone.
    """

    def content_ids(self) -> list[str]:
        return ["finish-button"]

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static("The vimdiomas command", classes="wizard-title")
                yield Static(
                    "So you can start Vimdiomas by typing `vimdiomas`, "
                    "instead of its full path:",
                    classes="wizard-prompt",
                )
                yield Static(id="path-report")
                yield Static(id="path-error", classes="wizard-error")
                yield Button("Finish", id="finish-button")
                yield FooterHint("Enter/Finish continue · q back", id="footer-hint")

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#path-error", Static).display = False
        self._saved = False
        self._status = install.link_status()
        self.query_one("#path-report", Static).update(_path_report(self._status))

    @on(Button.Pressed, "#finish-button")
    def _on_finish(self, event: Button.Pressed) -> None:
        if self._saved:
            # Second press, after a failure was reported: the config is
            # already on disk, so there's nothing left to do but leave.
            self.app.exit(self._config)
            return

        link_result = install.create_link(self._status)
        path_result = None
        if self._status.link_path is not None:
            bin_dir = self._status.link_path.parent
            if not install.on_path(bin_dir):
                path_result = install.ensure_on_path(bin_dir)

        self._config = self._write()
        self._saved = True

        problems = []
        if link_result.error is not None:
            problems.append(
                f"Couldn't create the link: {link_result.error}\n"
                "You can link it yourself later:\n"
                f"  ln -s {self._status.target} {link_result.link_path}"
            )
        if path_result is not None and path_result.error is not None:
            problems.append(
                f"Couldn't update {path_result.config_path}: {path_result.error}\n"
                "Add this line yourself:\n"
                f"  {install.path_export_line(self._status.link_path.parent)}"
            )

        if not problems:
            self.app.exit(self._config)
            return

        # Something failed but the config is written — the part the user
        # actually came for. Report it and let them leave on a second
        # press, rather than exiting over the top of the message.
        error_widget = self.query_one("#path-error", Static)
        error_widget.update("Your settings were saved.\n\n" + "\n\n".join(problems))
        error_widget.display = True
        self.query_one("#finish-button", Button).label = "Continue"

    def _write(self) -> Config:
        """Create the tree folders and save the config.

        An existing tree folder is left exactly as it is — `exist_ok=True`,
        never a rewrite — which is what lets the dev point the wizard at a
        notebook they already have.
        """
        root = self.app.root
        root.mkdir(parents=True, exist_ok=True)
        languages = []
        for language in self.app.languages:
            ensure_tree(root / f"tree-{language}")
            input_method, translation = self.app.input_methods.get(language, ("", ""))
            languages.append(
                LanguageConfig(
                    name=language,
                    input_method=input_method,
                    translation_input_method=translation,
                )
            )

        config = Config(
            user_name=self.app.user_name, root=root, languages=languages
        )
        save_config(config)
        return config


class WizardApp(App[Config | None]):
    """Runs the steps above and exits with the assembled `Config`, or `None`
    if quit before the last step (nothing is written on abort).

    Every answer lives here rather than on its screen, so walking backwards
    with `q` and forwards again re-shows what was chosen — the screens
    themselves are pushed and popped, and don't survive the trip.
    """

    CSS_PATH = Path(__file__).parent.parent / "app.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.user_name = ""
        self.languages: list[str] = []
        self.root: Path | None = None
        self.input_methods: dict[str, tuple[str, str]] = {}

    def on_mount(self) -> None:
        self.push_screen(DependenciesScreen())
