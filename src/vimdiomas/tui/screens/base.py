import subprocess
from pathlib import Path
from typing import Callable, TypeVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, Static, Tree
from textual.widgets._tree import TreeNode

from vimdiomas.compile import compile_file, failure_message, notebook_path_for
from vimdiomas.languages import LanguageKind
from vimdiomas.platform import open_file
from vimdiomas.store import DirNode, FileNode, is_grammar


def literal(text: str) -> Text:
    """`text` as literal content for a widget: the single route by which
    anything derived from the user's tree — a file or directory name, a
    category or subtitle, an entry's text, file content, an error message
    quoting any of those — reaches a Textual widget (Sprint 6 M2, #16).

    A `str` handed to `Static`, `Tree` or `Option` is parsed as markup, so
    `[/]` in a translation raises and `[b]x.md` draws as a bold `x`. This is a
    Rich `Text` rather than an escaped string because no string escape
    round-trips a backslash: `a\\[b]` and a name ending in `\\` both come out
    with the backslash doubled. A `Text` never reaches a markup parser at all.
    `app.notify` takes only a `str`, so a notification carrying user text
    passes `markup=False` instead.
    """
    return Text(text)


WARNING_MARKER = "⚠"


def file_leaf_label(file_node: FileNode) -> Text:
    """A file's label in either tree: its stem, plus a dim marker when the
    file holds something the app would not have written (Sprint 6 M9).

    The stem goes through `literal()` like every other piece of the user's
    text; the marker is the app's own, appended as a styled run so the two
    never mix. One helper for both trees, so a file marked in Inspect Tree is
    marked in Entry too.
    """
    label = literal(file_node.path.stem)
    if file_node.warnings:
        label.append(f" {WARNING_MARKER}", style="dim")
    return label


class VimOptionList(OptionList):
    """An OptionList with j/k aliases for the arrow keys it already binds."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]


TreeDataT = TypeVar("TreeDataT")


def build_dir_tree(
    tree_node: TreeNode[TreeDataT],
    dir_node: DirNode,
    make_dir_data: Callable[[DirNode], TreeDataT],
    on_file: Callable[[TreeNode[TreeDataT], FileNode], None],
) -> None:
    """Recursively add `dir_node`'s directories and files as children of
    `tree_node`, expanding each directory as it's added.

    Entry and Inspect Tree walk the same `DirNode`/`FileNode` shape but want
    different node data and different leaves per file (Entry adds
    category/uncategorized/new-category leaves under a file; Inspect Tree
    adds the file itself as a leaf) — `make_dir_data` and `on_file` are
    where that per-screen difference lives, so the walk itself is written
    once.
    """
    for child_dir in dir_node.dirs:
        child_node = tree_node.add(
            literal(child_dir.path.name), data=make_dir_data(child_dir), expand=True
        )
        build_dir_tree(child_node, child_dir, make_dir_data, on_file)

    for file_node in dir_node.files:
        on_file(tree_node, file_node)


def autocompile_one(
    app: App,
    source_path: Path,
    notebook_path: Path,
    *,
    kind: LanguageKind,
    grammar: bool = False,
) -> None:
    """Compile one file, reporting failure back to the UI thread.

    Runs inside a worker thread owned by `app` (not a screen — a switch to
    another screen must not cancel a compile already in flight), so any
    UI-touching call must go through `app.call_from_thread`. Shared by Entry
    and Inspect Tree, whose autocompile-on-change logic was identical apart
    from the notify message's wording. `grammar` (Sprint 5 M5) is decided by
    the caller from its own `tree_root` via `store.is_grammar`; `kind` (Sprint 6
    M5) is the notebook language's, which the caller already knows.
    """
    try:
        compile_file(source_path, notebook_path, kind=kind, grammar=grammar)
    except (subprocess.CalledProcessError, OSError) as exc:
        app.call_from_thread(
            app.notify,
            f"Compile failed for {source_path.name}: {exc}",
            severity="error",
            markup=False,
        )


def open_source_pdf(app: App, source_path: Path, *, tree_root: Path, kind: LanguageKind) -> None:
    """Open `source_path`'s compiled PDF, compiling it first if it has none
    (M3, `requirements.md` §3.6). Shared by Inspect Tree (PDF mode) and
    Browse (both modes) so the two can't drift apart — this is Inspect
    Tree's own `_open_pdf`, generalised only by taking `tree_root`/`kind`
    as arguments instead of reading them off `self`. A compile failure
    notifies with the same message Inspect Tree always has and opens
    nothing."""
    pdf_path = notebook_path_for(source_path)
    if not pdf_path.exists():
        try:
            compile_file(
                source_path, pdf_path, kind=kind, grammar=is_grammar(source_path, tree_root)
            )
        except (subprocess.CalledProcessError, OSError) as exc:
            app.notify(
                f"Compile failed for {source_path.name}:\n{failure_message(exc)}",
                severity="error",
                markup=False,
            )
            return
    open_file(pdf_path)


class VimTree(Tree[TreeDataT]):
    """The shared aesthetic and vim motion for every tree in the app.

    `Tree` has no default binding for plain left/right (only shift+left/
    right, for parent/ancestor jumps), so h/l — which should do "whatever the
    arrow key already does" per the key-map convention — have nothing to
    alias and are left unbound here.

    Generic over the node data type, the same way `Tree` itself is — a
    subclass declares its own data (`class EntryTree(VimTree[NodeData])`)
    and is free to add whatever tree-building/selection logic is specific to
    it. This base carries only what every tree in the app shares: j/k, and
    the bordered/content-sized/no-horizontal-scroll look in `app.tcss`'s
    `VimTree` rule.
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]


class NoShiftArrowsTree(VimTree[TreeDataT]):
    """`VimTree` with `Tree`'s own shift-arrow defaults (parent/ancestor/
    sibling jumps) overridden to a no-op, for a tree living inside a `Panel`,
    which claims shift-arrows for panel movement instead — dev feedback,
    hands-on during Sprint 4 M1: shift-arrows must mimic the letter
    panel-move keys (H/L/J/K) exactly, including doing nothing on content.
    Used by `EntryTree` and `InspectTree`, the app's two trees that live
    inside a panel.
    """

    BINDINGS = [
        Binding("shift+left", "nothing", "Nothing", show=False),
        Binding("shift+right", "nothing", "Nothing", show=False),
        Binding("shift+up", "nothing", "Nothing", show=False),
        Binding("shift+down", "nothing", "Nothing", show=False),
    ]

    def action_nothing(self) -> None:
        pass


class FooterHint(Static):
    """A muted, single-line reminder of a screen's keybindings.

    One place for every screen's footer hint to share its look
    (`.footer-hint` in `app.tcss`), the same rationale as `VimTree` for tree
    styling — introduced in Sprint 3 M4 when a second screen needed one.
    """

    def __init__(self, text: str, **kwargs) -> None:
        super().__init__(text, **kwargs)
        self.add_class("footer-hint")


class MenuLegend(FooterHint):
    """The line under a menu's option list that describes the highlighted
    option (Sprint 6 M4). A `FooterHint` for the muted look; the
    `menu-legend` class adds italic, the list's width and a fixed two-line
    height (`app.tcss`). Never focusable — `tab` on a menu has nothing to
    land on but the list.
    """

    can_focus = False

    def __init__(self, text: str = "", **kwargs) -> None:
        super().__init__(text, **kwargs)
        self.add_class("menu-legend")


class ConfirmDialog(ModalScreen[bool]):
    """A modal yes/no prompt. Dismisses with True (confirmed) or False.

    The app's one reusable shape for "are you sure" (Sprint 3, M5's `d`
    needed one and the roadmap asked that it not be invented per-keypress).
    Only `y` confirms and `n`/`escape` cancels — `enter` is deliberately left
    unbound (dev's explicit request) so it can never be a way to accidentally
    confirm a destructive action.
    """

    BINDINGS = [
        Binding("y", "confirm", "Yes", show=False),
        Binding("n,escape", "cancel", "No", show=False),
    ]

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            # Every caller's message names something in the user's tree.
            yield Static(literal(self.message))
            yield Static("y / n", classes="dialog-hint")

    def action_confirm(self) -> None:
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)


class PromptDialog(ModalScreen[str | None]):
    """A modal single-field text prompt. Dismisses with the submitted text,
    or None if cancelled (escape).

    The app's one reusable shape for "ask for a name" (Sprint 3, M5's
    `e`/`n`/`m` all need one) — a variant of the same dialog family as
    `ConfirmDialog` rather than a one-off per key. Uses a plain `Input`, not
    `vimdiomas.tui.screens.panels.TextField` — this modal has no `Panel` for a
    field to relate to, so the panel-model widgets have nothing to offer it.
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
    ]

    def __init__(self, label: str, initial: str = "") -> None:
        super().__init__()
        self.label = label
        self.initial = initial

    def compose(self) -> ComposeResult:
        with Vertical(classes="dialog"):
            yield Static(self.label)
            yield Input(value=self.initial, id="dialog-input")

    def on_mount(self) -> None:
        self.query_one("#dialog-input", Input).focus()

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value)
