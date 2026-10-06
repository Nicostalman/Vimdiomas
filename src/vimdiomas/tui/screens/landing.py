from textual.widgets import OptionList

from vimdiomas.languages import is_functional
from vimdiomas.tui.screens.main_menu import MainMenuScreen
from vimdiomas.tui.screens.panels import MenuOption, MenuScreen
from vimdiomas.tui.screens.placeholder import PlaceholderScreen
from vimdiomas.tui.screens.settings import SettingsScreen


class LandingMenuScreen(MenuScreen):
    def menu_options(self) -> list[MenuOption]:
        return [
            *(
                MenuOption(
                    f"{language.name} notebook",
                    f"Add words, explore and compile your {language.name} notes."
                    if is_functional(language.name)
                    else "Not available yet.",
                    id=f"language:{language.name}",
                )
                for language in self.app.config.languages
            ),
            MenuOption(
                "Settings",
                "Input methods, and adding or removing a language."
                if self.app.config.languages
                else "Add a language to start a notebook.",
                id="settings",
            ),
        ]

    def action_back_or_quit(self) -> None:
        self.app.exit()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id == "settings":
            self.app.push_screen(SettingsScreen())
            return

        language = event.option_id.removeprefix("language:")
        if is_functional(language):
            self.app.push_screen(MainMenuScreen(language))
        else:
            self.app.push_screen(
                PlaceholderScreen(f"{language} notebook is not implemented yet.")
            )

