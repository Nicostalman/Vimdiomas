"""The Settings menu and what is real under it: input methods (Sprint 4 M6),
adding a language (Sprint 6 M7) and removing one (Sprint 6 M8).

Input methods are real on the dev's explicit call: getting them wrong in the
wizard is both easy (the right answer depends on keyboards the user may not
have added yet) and invisible until Entry doesn't switch, so it needed a fix
path that isn't hand-editing `~/.config/vimdiomas/config.toml`. Adding a
language is the wizard's languages and input-method steps again, for a
language not chosen at install time. Removing one unregisters it; its notes
are deleted only on a second, separate confirmation.
"""

import shutil
from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Button, OptionList, Static

from vimdiomas.compile import forget_tree
from vimdiomas.config import Config, LanguageConfig, save_config
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
from vimdiomas.tui.screens.panels import Backpanel, FormScreen, MenuOption, MenuScreen, Panel
from vimdiomas.tui.screens.placeholder import PlaceholderScreen


class SettingsScreen(MenuScreen):
    def menu_options(self) -> list[MenuOption]:
        return [
            MenuOption(
                "Input methods",
                "Choose which keyboard each language is typed with.",
                id="input_methods",
            ),
            MenuOption(
                "Add a language",
                "Start a notebook for another language.",
                id="add_language",
            ),
            MenuOption(
                "Remove a language",
                "Stop using a language. Its notes are kept unless you ask.",
                id="remove_language",
            ),
        ]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id == "input_methods":
            if self.app.config.languages:
                self.app.push_screen(InputMethodLanguagesScreen())
            else:
                self.app.push_screen(
                    PlaceholderScreen("There is no language to set up. Add one first.")
                )
        elif event.option_id == "add_language":
            if addable_languages(self.app.config):
                self.app.push_screen(AddLanguageScreen())
            else:
                self.app.push_screen(
                    PlaceholderScreen("Every supported language is already added.")
                )
        elif self.app.config.languages:
            self.app.push_screen(RemoveLanguageScreen())
        else:
            self.app.push_screen(PlaceholderScreen("There is no language to remove."))


def addable_languages(config: Config) -> list[str]:
    """The registry languages the config doesn't hold yet, in registry order."""
    registered = {entry.name for entry in config.languages}
    return [language.name for language in LANGUAGES if language.name not in registered]


class AddLanguageScreen(MenuScreen):
    """Which language to add — one option per registry language not yet in the
    config. Registered ones are hidden rather than shown disabled (Sprint 6
    M7). Rebuilt from the running config whenever it is shown again."""

    def menu_options(self) -> list[MenuOption]:
        return [
            MenuOption(name, f"Start a notebook for {name}.", id=f"language:{name}")
            for name in addable_languages(self.app.config)
        ]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        language = event.option_id.removeprefix("language:")
        self.app.push_screen(AddLanguageFormScreen(language))


class RemoveLanguageScreen(MenuScreen):
    """Which registered language to remove, in config order (the landing
    menu's), a name outside the registry included: a hand-edited config can
    hold one, and removing it is a way to clean up (Sprint 6 M8).

    Choosing one asks twice, separately: whether to unregister it, then —
    only if its tree folder exists — whether to delete that folder too. The
    second is the one that destroys the user's files, so declining it, by
    `n` or `esc`, is the safe reading and the way out. The config is saved
    (as a copy) before the folder is touched, so a failed save leaves the
    language registered with its folder intact."""

    def menu_options(self) -> list[MenuOption]:
        return [
            MenuOption(
                entry.name,
                f"Remove {entry.name}. You'll be asked about its notes.",
                id=f"language:{entry.name}",
            )
            for entry in self.app.config.languages
        ]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        language = event.option_id.removeprefix("language:")
        self.app.push_screen(
            ConfirmDialog(
                f"Remove {language} from Vimdiomas? It leaves the main menu and Settings."
            ),
            lambda confirmed: self._ask_about_notes(language) if confirmed else None,
        )

    def _ask_about_notes(self, language: str) -> None:
        folder = self.app.config.tree_root(language)
        if not folder.is_dir():
            self._remove(language, delete_notes=False)
            return
        self.app.push_screen(
            ConfirmDialog(_delete_notes_question(folder)),
            lambda delete: self._remove(language, delete_notes=bool(delete)),
        )

    def _remove(self, language: str, *, delete_notes: bool) -> None:
        config = self.app.config
        folder = config.tree_root(language)
        had_folder = folder.is_dir()
        try:
            save_config(
                Config(
                    user_name=config.user_name,
                    root=config.root,
                    languages=[entry for entry in config.languages if entry.name != language],
                )
            )
        except (OSError, ValueError) as exc:
            # Nothing past this point ran: the running config and the folder
            # are as they were, and the picker stays up.
            self.app.notify(
                f"Could not remove {language}: {exc}", severity="error", markup=False
            )
            return
        config.languages[:] = [entry for entry in config.languages if entry.name != language]
        self.app.pop_screen()
        if delete_notes:
            try:
                shutil.rmtree(folder)
            except OSError as exc:
                # Whatever rmtree removed before failing stays removed.
                self.app.notify(
                    f"{language} removed, but {folder} could not be deleted: {exc}",
                    severity="error",
                    markup=False,
                )
                return
            forget_tree(folder)
            message = f"{language} removed, and its notes deleted."
        elif had_folder:
            message = f"{language} removed. Its notes are still in {folder}."
        else:
            message = f"{language} removed."
        self.app.notify(message, markup=False)


def _delete_notes_question(folder: Path) -> str:
    files = sum(1 for path in folder.rglob("*") if path.is_file())
    if files == 0:
        return f"Also delete the empty folder {folder}? This cannot be undone."
    noun = "file" if files == 1 else "files"
    return f"Also delete {folder} and the {files} {noun} in it? This cannot be undone."


class InputMethodLanguagesScreen(MenuScreen):
    """Which language's input methods to edit — one option per registered
    language, German included: its answers are stored and unused while it's
    inert, and hiding them here would make the config and the UI disagree."""

    def menu_options(self) -> list[MenuOption]:
        return [
            MenuOption(
                language.name,
                f"Change the keyboards used for {language.name}.",
                id=f"language:{language.name}",
            )
            for language in self.app.config.languages
        ]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        language = event.option_id.removeprefix("language:")
        self.app.push_screen(InputMethodSettingsScreen(language))


class InputMethodSettingsScreen(FormScreen):
    """The wizard's input-method question again, prefilled from the config.

    Saving rewrites the whole config through `save_config` (atomic temp file
    + `os.replace`, the project's standing convention) **and** mutates the
    running `Config` in place, so Entry picks the change up without a
    relaunch — the point of having this screen at all.
    """

    def __init__(self, language: str) -> None:
        super().__init__()
        self.language = language

    def content_ids(self) -> list[str]:
        return [LANGUAGE_FIELD_ID, TRANSLATION_FIELD_ID, "save-button"]

    def compose(self) -> ComposeResult:
        entry = self.app.config.language(self.language)
        current = (entry.input_method, entry.translation_input_method) if entry else ("", "")
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static(
                    f"Input methods · {self.language}", classes="wizard-title"
                )
                yield Static(INPUT_METHOD_PROMPT, classes="wizard-prompt")
                yield from compose_fields(
                    self.language, available_sources(), current[0], current[1]
                )
                yield Button("Save", id="save-button")
                yield FooterHint(
                    "Enter open list · j/k move · Enter choose · Esc close · q back",
                    id="footer-hint",
                )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "save-button":
            return
        self._save()

    def _save(self) -> None:
        input_method, translation = read_fields(self)
        entry = self.app.config.language(self.language)
        if entry is not None:
            entry.input_method = input_method
            entry.translation_input_method = translation
            save_config(self.app.config)
        self.app.pop_screen()


class AddLanguageFormScreen(FormScreen):
    """The wizard's input-method question for a language being added, and the
    write that registers it (Sprint 6 M7).

    *Add* checks what the language needs, then creates its tree folder, saves
    a **copy** of the config with the language appended, and only once that
    save has succeeded appends it to the running config — so a failed save
    can't leave the running app ahead of the file, which `InputMethodSettings
    Screen` (save the live config in place) can't promise. Both this form and
    the picker under it close, and Settings notifies.
    """

    def __init__(self, language: str) -> None:
        super().__init__()
        self.language = language

    def content_ids(self) -> list[str]:
        return [LANGUAGE_FIELD_ID, TRANSLATION_FIELD_ID, "add-button"]

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(classes="wizard-panel"):
                yield Static(f"Add a language · {self.language}", classes="wizard-title")
                yield Static(INPUT_METHOD_PROMPT, classes="wizard-prompt")
                yield from compose_fields(self.language, available_sources())
                yield Static(id="add-language-error", classes="wizard-error")
                yield Button("Add", id="add-button")
                yield FooterHint(
                    "Enter open list · j/k move · Enter choose · Esc close · q back",
                    id="footer-hint",
                )

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#add-language-error", Static).display = False

    def _show_error(self, message: str) -> None:
        error_widget = self.query_one("#add-language-error", Static)
        error_widget.update(literal(message))
        error_widget.display = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "add-button":
            return
        self.query_one("#add-language-error", Static).display = False
        ensure_dependencies(self.app, [self.language], self._add)

    def _add(self, dependency_error: str | None) -> None:
        if dependency_error is not None:
            self._show_error(dependency_error)
            return
        config = self.app.config
        input_method, translation = read_fields(self)
        entry = LanguageConfig(
            name=self.language,
            input_method=input_method,
            translation_input_method=translation,
        )
        try:
            ensure_tree(config.tree_root(self.language))
            save_config(
                Config(
                    user_name=config.user_name,
                    root=config.root,
                    languages=[*config.languages, entry],
                )
            )
        except (OSError, ValueError) as exc:
            # Nothing past this point ran: the running config is as it was.
            # A tree folder made before the save failed stays, harmless — the
            # next add adopts it.
            self._show_error(f"Could not add {self.language}: {exc}")
            return
        config.languages.append(entry)
        self.app.pop_screen()
        self.app.pop_screen()
        self.app.notify(f"{self.language} added.")
