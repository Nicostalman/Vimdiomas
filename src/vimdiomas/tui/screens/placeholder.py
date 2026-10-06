from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static

from vimdiomas.tui.screens.panels import Backpanel, Panel, PanelScreen


class PlaceholderScreen(PanelScreen):
    def __init__(self, message: str | Text) -> None:
        # A `str` is the app's own text; a message quoting the user's tree or
        # a tool's output arrives as `literal()` (Sprint 6 M2, #16).
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel():
                yield Static(self.message)
