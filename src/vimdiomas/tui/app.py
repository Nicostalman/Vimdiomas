from pathlib import Path

from textual.app import App

from vimdiomas.config import Config
from vimdiomas.tui.screens.landing import LandingMenuScreen


class VimdiomasApp(App):
    CSS_PATH = Path(__file__).parent / "app.tcss"

    def __init__(self, config: Config) -> None:
        super().__init__()
        self.config = config

    def on_mount(self) -> None:
        self.push_screen(LandingMenuScreen())
