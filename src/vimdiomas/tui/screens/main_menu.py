from pathlib import Path

from textual.widgets import OptionList

from vimdiomas.compile import CompileReport, compile_all
from vimdiomas.config import NotebookConfig
from vimdiomas.languages import get_language
from vimdiomas.store import ensure_tree
from vimdiomas.tui.screens.base import literal
from vimdiomas.tui.screens.browse import BrowseScreen
from vimdiomas.tui.screens.entry import EntryScreen
from vimdiomas.tui.screens.inspect import InspectTreeScreen
from vimdiomas.tui.screens.panels import MenuOption, MenuScreen
from vimdiomas.tui.screens.placeholder import PlaceholderScreen


class MainMenuScreen(MenuScreen):
    def __init__(self, language: str) -> None:
        super().__init__()
        self.language = language

    def on_mount(self) -> None:
        super().on_mount()
        # A tree made before its folders were automatic, or by hand, is
        # completed the next time its notebook is opened (Sprint 6 M6).
        ensure_tree(self.app.config.tree_root(self.language))

    def menu_options(self) -> list[MenuOption]:
        return [
            MenuOption(
                "Enter vocabulary",
                "Add a word or a grammar point to a file, under a category.",
                id="enter_vocabulary",
            ),
            MenuOption(
                "Inspect tree",
                "Walk your files: preview them, open in Neovim, rename, delete.",
                id="inspect_tree",
            ),
            MenuOption(
                "Browse",
                "Fuzzy-find a file by name, or filter by tag.",
                id="browse",
            ),
            MenuOption(
                "Compile",
                "Rebuild the PDFs of files changed since their last compile.",
                id="compile",
            ),
        ]

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        handler = {
            "enter_vocabulary": self._enter_vocabulary,
            "inspect_tree": self._inspect_tree,
            "browse": self._browse,
            "compile": self._compile,
        }[event.option_id]
        handler()

    def _notebook_config(self) -> NotebookConfig:
        # Rebuilt per screen push rather than cached, so a change made in
        # Settings › Input methods reaches the next Entry screen without a
        # relaunch (Sprint 4 M6).
        entry = self.app.config.language(self.language)
        return NotebookConfig(
            tree_root=self.app.config.tree_root(self.language),
            language=self.language,
            kind=get_language(self.language).kind,
            input_method=entry.input_method if entry else "",
            translation_input_method=entry.translation_input_method if entry else "",
        )

    def _enter_vocabulary(self) -> None:
        self.app.push_screen(EntryScreen(self._notebook_config()))

    def _browse(self) -> None:
        config = self._notebook_config()
        self.app.push_screen(BrowseScreen(config.tree_root, kind=config.kind))

    def _compile(self) -> None:
        # Never forced: a forced rebuild is `vimdiomas compile --force` (Sprint 6 M4).
        config = self._notebook_config()
        report = compile_all(config.tree_root, kind=config.kind, force=False)
        # Literal: the paths are the user's, and the error tail is LaTeX.
        self.app.push_screen(PlaceholderScreen(literal(compile_summary(report))))

    def _inspect_tree(self) -> None:
        config = self._notebook_config()
        self.app.push_screen(InspectTreeScreen(config.tree_root, kind=config.kind))


def compile_summary(report: CompileReport) -> str:
    """What a Compile did, for its results screen: the PDFs written, then —
    if any file failed — each failed source with the tail of its error,
    indented below it (Sprint 6 M2, #12), then any file that compiled with a
    warning, the warning indented below it the same way (M3, #4)."""
    blocks = []
    if not report.compiled and not report.failed:
        blocks.append("Everything is up to date.")
    if report.compiled:
        blocks.append("Compiled:\n" + "\n".join(str(path) for path in report.compiled))
    if report.failed:
        failures = []
        for failure in report.failed:
            detail = "\n".join(f"    {line}" for line in failure.message.splitlines())
            failures.append(f"{failure.source}\n{detail}")
        blocks.append("Failed:\n" + "\n".join(failures))
    if report.warnings:
        # Grouped by file: a hand-edited file can earn several warnings, and
        # one path line each would repeat the path (Sprint 6 M9). Every line
        # of a message is indented, as the failures above are.
        by_source: dict[Path, list[str]] = {}
        for warning in report.warnings:
            by_source.setdefault(warning.source, []).append(warning.message)
        warnings = []
        for source, messages in by_source.items():
            detail = "\n".join(
                f"    {line}" for message in messages for line in message.splitlines()
            )
            warnings.append(f"{source}\n{detail}")
        blocks.append("Warnings:\n" + "\n".join(warnings))
    return "\n\n".join(blocks)
