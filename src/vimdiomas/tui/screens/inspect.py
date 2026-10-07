import os
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Callable, Literal

from rich.text import Text

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.geometry import Region
from textual.widgets import Input, Static, Tree
from textual.widgets._tree import TreeNode

from vimdiomas.compile import notebook_path_for
from vimdiomas.languages import LanguageKind
from vimdiomas.models import Warning
from vimdiomas.pdf_preview import RasterCache, extract_text, pdftoppm_available
from vimdiomas.store import DirNode, FileNode, is_grammar, validate_name, walk
from vimdiomas.terminal import (
    cell_pixel_size,
    clear_kitty_images,
    render_kitty_image,
    supports_kitty_graphics,
)
from vimdiomas.tui.screens.base import (
    ConfirmDialog,
    FooterHint,
    NoShiftArrowsTree,
    PromptDialog,
    autocompile_one,
    build_dir_tree,
    open_source_pdf,
    WARNING_MARKER,
    file_leaf_label,
    literal,
)
from vimdiomas.tui.screens.panels import Backpanel, Panel, PanelScreen

NodeKind = Literal["dir", "file"]


def is_taken(target: Path, source: Path) -> bool:
    """Whether renaming `source` to `target` would clobber another file.

    On a case-insensitive filesystem (macOS's default APFS) `food` → `Food`
    finds `Food.md` "existing" — it is the source itself under another
    spelling, so it is free (Sprint 6 M3, #17)."""
    if not target.exists():
        return False
    try:
        return not target.samefile(source)
    except OSError:
        return True


def move(source: Path, target: Path) -> None:
    """Rename `source` to `target`, through a unique temporary name in the
    same directory when `target` is the same file under another spelling —
    a direct case-only rename is not reliably a rename on a case-insensitive
    filesystem (#17). If the second step fails the original name is put
    back, and the error still raised for the caller to report."""
    if not target.exists():
        source.rename(target)
        return
    temporary = source.with_name(f".{source.name}.{uuid.uuid4().hex}")
    source.rename(temporary)
    try:
        temporary.rename(target)
    except OSError:
        temporary.rename(source)
        raise

FOOTER_HINT_PDF = (
    "Tab: switch to MD mode · Enter: open PDF"
    " · d/r/n/m: delete/rename/new dir/new file · u: undo delete"
)
FOOTER_HINT_MD = (
    "Tab: switch to PDF mode · Enter: open in nvim"
    " · d/r/n/m: delete/rename/new dir/new file · u: undo delete"
)

NVIM_COMMAND = ["nvim", "-c", "set noexpandtab"]

MODE_LABEL_PDF = "PDF MODE"
MODE_LABEL_MD = "MD MODE"


@dataclass
class NodeData:
    kind: NodeKind
    path: Path
    # A file node's warnings, so the preview can list them without re-reading
    # the file (Sprint 6 M9). Always empty for a directory.
    warnings: list[Warning] = field(default_factory=list)


@dataclass
class PendingDelete:
    """A deletion marked in this screen but not yet committed to disk.

    Carries the target's filesystem identity as well as its path (Sprint 6 M1,
    #1). A path is not a durable name for a file: between marking and
    committing, the path can be renamed out from under the deletion, or
    re-created holding something else entirely. `on_unmount` re-stats the path
    and only removes what still has this identity, so the file that goes is the
    one the user actually marked.
    """

    data: NodeData
    dev: int
    ino: int

    @classmethod
    def of(cls, data: NodeData) -> "PendingDelete | None":
        """`data` with its identity captured now, or `None` if it can't be
        stat'd — in which case there is nothing to mark."""
        try:
            stat = os.stat(data.path)
        except OSError:
            return None
        return cls(data=data, dev=stat.st_dev, ino=stat.st_ino)

    @property
    def path(self) -> Path:
        return self.data.path

    def still_the_same_file(self) -> bool:
        try:
            stat = os.stat(self.path)
        except OSError:
            return False
        return (stat.st_dev, stat.st_ino) == (self.dev, self.ino)

    def remap(self, old_root: Path, new_root: Path) -> None:
        """Move this pending path along with a rename of `old_root`.

        The deleted item is hidden from the tree, so refusing the rename would
        name something the user cannot see; remapping is what they already
        believe happened.
        """
        if self.path == old_root:
            self.data.path = new_root
        elif old_root in self.path.parents:
            self.data.path = new_root / self.path.relative_to(old_root)


class InspectTree(NoShiftArrowsTree[NodeData]):
    """Inspect Tree's tree: leaves are files themselves, not categories.

    Unlike `EntryTree`, no per-file selection semantics are added here — a
    file leaf is opened directly, in whichever mode the screen is in.
    """


def build_tree(tree: InspectTree, dir_node: DirNode) -> None:
    tree.root.data = NodeData(kind="dir", path=dir_node.path)
    build_dir_tree(
        tree.root, dir_node, lambda d: NodeData(kind="dir", path=d.path), _add_file_leaf
    )
    tree.root.expand()


def _add_file_leaf(tree_node: TreeNode[NodeData], file_node: FileNode) -> None:
    tree_node.add_leaf(
        file_leaf_label(file_node),
        data=NodeData(kind="file", path=file_node.path, warnings=file_node.warnings),
    )


def _retitle(text: str, new_title: str) -> str:
    """Replace the deck's `# Title` header line with `new_title`, leaving
    everything else untouched. Mirrors `parser.py`'s own header detection
    (the first line starting with `# ` but not `## `)."""
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            newline = "\n" if line.endswith("\n") else ""
            lines[index] = f"# {new_title}{newline}"
            break
    return "".join(lines)


def _node_for(tree: InspectTree, path: Path) -> TreeNode[NodeData] | None:
    """The displayed node for `path`, or `None` if it is no longer in the tree.

    Used to put the cursor back after a rebuild (Sprint 6 M9): the tree is
    rebuilt from disk when `nvim` exits, and landing back on the root would
    lose the file the user was just editing. Walks the tree's *lines* rather
    than its nodes, because reading them is also what assigns each node the
    line `move_cursor` needs — on a tree just built, every node's line is
    still unset until something asks for them.
    """
    for line in range(tree.last_line + 1):
        node = tree.get_node_at_line(line)
        if node is not None and node.data is not None and node.data.path == path:
            return node
    return None


def _prune(dir_node: DirNode, hidden_paths: set[Path]) -> DirNode:
    """A copy of `dir_node` with any dir/file in `hidden_paths` (and everything
    under a hidden directory) left out — used to visually hide a pending
    delete without touching the filesystem."""
    return DirNode(
        path=dir_node.path,
        dirs=[_prune(d, hidden_paths) for d in dir_node.dirs if d.path not in hidden_paths],
        files=[f for f in dir_node.files if f.path not in hidden_paths],
    )


# How many of a file's warnings the preview lists before summarising the rest
# (Sprint 6 M9): a file of nothing but prose has one per line, and the block
# shares the pane with the file's own content.
WARNINGS_SHOWN = 10


def warnings_text(warnings: list[Warning]) -> Text:
    """The preview pane's warnings block: a count, then each warning as
    `line N: message` with the offending line indented beneath it.

    A file-level warning (`line_number == 0`, a missing header) has no line to
    name and is shown as the message alone. Everything here quotes the file,
    so the whole block is built as a `Text` — a raw line is exactly the kind
    of text that holds brackets (M2, #16).
    """
    noun = "warning" if len(warnings) == 1 else "warnings"
    text = literal(f"{WARNING_MARKER} {len(warnings)} {noun}")
    for warning in warnings[:WARNINGS_SHOWN]:
        if warning.line_number:
            text.append(literal(f"\nline {warning.line_number}: {warning.message}"))
            text.append(literal(f"\n    {warning.raw_line}"))
        else:
            text.append(literal(f"\n{warning.message}"))
    remaining = len(warnings) - WARNINGS_SHOWN
    if remaining > 0:
        text.append(literal(f"\n… and {remaining} more"))
    return text


MSG_SELECT_FILE = "Select a file to preview."
MSG_NO_PDF = "No compiled PDF for this file."
MSG_NO_POPPLER = "poppler isn't installed, so there's no PDF preview."
MSG_NO_NVIM = "nvim isn't installed, so MD mode can't open files."


class PdfPreview(Static):
    """Thin wrapper around the kitty graphics protocol: Textual doesn't
    composite raw terminal graphics itself, so this widget writes the escape
    sequence directly to the terminal and holds no visible text of its own,
    just reserving the layout space.

    Positioning is given explicitly by the caller (`region`) rather than
    read off `self.region`: kitty images sit in their own layer above the
    text grid, entirely outside Textual's own layout/paint cycle, so nothing
    here can rely on Textual having already reflowed this widget by the time
    `show_image` runs — right after this widget's `display` flips to `True`,
    its own `region` can still be the stale, pre-layout one. The screen
    passes its preview panel's own (always-live) content region instead.
    """

    def _write(self, sequence: str) -> None:
        driver = getattr(self.app, "_driver", None)
        if driver is None:
            return
        driver.write(sequence)
        flush = getattr(driver, "flush", None)
        if flush is not None:
            flush()

    def clear_image(self) -> None:
        self._write(clear_kitty_images())

    def show_image(self, png_bytes: bytes, region: Region) -> None:
        self.update("")
        self.clear_image()
        if region.width <= 0 or region.height <= 0:
            return
        move_cursor = f"\x1b[{region.y + 1};{region.x + 1}H"
        self._write(move_cursor + render_kitty_image(png_bytes))


class InspectTreeScreen(PanelScreen):
    """Browse the tree directly: PDF mode (default) opens each file's PDF in
    the OS viewer, MD mode opens it in nvim inside the same terminal.

    The mode is screen-local state, reset to PDF every time the screen is
    constructed — leaving and re-entering always starts fresh, per the
    roadmap's "not persistent" requirement.
    """

    BINDINGS = [
        Binding("tab", "toggle_mode", "Toggle mode", show=False),
        Binding("d", "delete", "Delete", show=False),
        Binding("r", "rename", "Rename", show=False),
        Binding("n", "new_dir", "New directory", show=False),
        Binding("m", "new_file", "New file", show=False),
        Binding("u", "undo", "Undo delete", show=False),
    ]

    def __init__(self, tree_root: Path, *, kind: LanguageKind) -> None:
        super().__init__()
        self.tree_root = tree_root
        self.kind = kind
        self.mode: Literal["pdf", "md"] = "pdf"
        # Deletions are aesthetic while this screen is open — hidden from the
        # tree immediately, undoable with `u`, and only actually removed from
        # disk when the screen is unmounted (see `on_unmount`).
        self._pending_deletes: list[PendingDelete] = []
        self._raster_cache = RasterCache()
        # Bumped on every preview update; a worker's callback checks it still
        # matches before applying its result, so a stale in-flight render
        # from a cursor that has since moved on never overwrites what's
        # currently shown.
        self._preview_generation = 0
        self._preview_data: NodeData | None = None

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Horizontal():
                with Panel(id="inspect-panel"):
                    yield Static(MODE_LABEL_PDF, id="mode-badge", classes="mode-pdf")
                    yield InspectTree("Inspect tree", id="inspect-tree", classes="mode-pdf")
                    yield FooterHint(FOOTER_HINT_PDF, id="footer-hint")
                with Panel(id="preview-panel"):
                    yield Static("", id="preview-warnings")
                    # The message and the image share a container of their own
                    # so the warnings block takes its height from the panel
                    # and the raster is sized to what is left (M9).
                    with Vertical(id="preview-body"):
                        yield Static(MSG_SELECT_FILE, id="preview-message")
                        yield PdfPreview(id="preview-image")

    def on_mount(self) -> None:
        super().on_mount()
        self.query_one("#preview-image", PdfPreview).display = False
        self._rebuild_tree()
        # The preview panel's region is 0x0 until the first layout pass, so
        # a PDF-mode rasterisation attempted from here would ask for a
        # near-zero-size image — redo it once real dimensions exist.
        self.call_after_refresh(lambda: self._update_preview(self._preview_data))

    def on_resize(self, event: events.Resize) -> None:
        self._update_preview(self._preview_data)

    def action_back_or_quit(self) -> None:
        # A kitty image sits in its own layer above the text grid, outside
        # Textual's own repaint, so leaving it undeleted would leave it
        # visibly covering the menu underneath. Cleared here, while the
        # widget is still mounted, rather than in on_unmount: Textual
        # unmounts a screen's children before calling the screen's own
        # on_unmount, so by then #preview-image is already gone and a clear
        # attempted there is a silent no-op.
        if not isinstance(self.focused, Input):
            self.query_one("#preview-image", PdfPreview).clear_image()
        super().action_back_or_quit()

    def on_unmount(self) -> None:
        """Commit any pending deletes for real now that the screen is leaving."""
        # A kitty image sits in its own layer above the text grid, outside
        # Textual's own repaint — leaving it undeleted would leave it
        # visibly covering whatever screen comes next (the menu underneath).
        # By the time this fires, children may already be gone from the DOM
        # (Textual prunes them before the screen's own on_unmount runs), so
        # this is best-effort rather than a query_one that could raise.
        previews = self.query(PdfPreview)
        if previews:
            previews.first().clear_image()
        for pending in self._pending_deletes:
            if not pending.path.exists():
                # Already gone — nothing to do and nothing to report.
                continue
            if not pending.still_the_same_file():
                # Something else stands at this path now. Not deleting is
                # always the recoverable direction. The notification is the
                # app's, not this screen's: the screen is leaving.
                self.app.notify(
                    f"{pending.path.name} changed since it was deleted — left alone.",
                    severity="warning",
                    markup=False,
                )
                continue
            if pending.data.kind == "dir":
                shutil.rmtree(pending.path)
            else:
                pending.path.unlink()
                pdf_path = notebook_path_for(pending.path)
                if pdf_path.exists():
                    pdf_path.unlink()
        self._pending_deletes.clear()

    def _rebuild_tree(self, select_path: Path | None = None) -> None:
        tree = self.query_one("#inspect-tree", InspectTree)
        tree.clear()
        hidden_paths = {pending.path for pending in self._pending_deletes}
        dir_node = _prune(walk(self.tree_root, kind=self.kind), hidden_paths)
        build_tree(tree, dir_node)
        tree.focus()
        node = _node_for(tree, select_path) if select_path is not None else None
        if node is not None:
            tree.move_cursor(node)
        self._update_preview(
            node.data if node is not None
            else (tree.cursor_node.data if tree.cursor_node else None)
        )

    def action_toggle_mode(self) -> None:
        self.mode = "md" if self.mode == "pdf" else "pdf"
        is_pdf = self.mode == "pdf"

        tree = self.query_one("#inspect-tree", InspectTree)
        tree.set_class(is_pdf, "mode-pdf")
        tree.set_class(not is_pdf, "mode-md")

        badge = self.query_one("#mode-badge", Static)
        badge.set_class(is_pdf, "mode-pdf")
        badge.set_class(not is_pdf, "mode-md")
        badge.update(MODE_LABEL_PDF if is_pdf else MODE_LABEL_MD)

        self.query_one("#footer-hint", FooterHint).update(
            FOOTER_HINT_MD if self.mode == "md" else FOOTER_HINT_PDF
        )
        self._update_preview(self._preview_data)

    @on(Tree.NodeHighlighted)
    def _on_node_highlighted(self, event: Tree.NodeHighlighted[NodeData]) -> None:
        self._update_preview(event.node.data)

    def _show_warnings(self, warnings: list[Warning]) -> None:
        block = self.query_one("#preview-warnings", Static)
        block.display = bool(warnings)
        block.update(warnings_text(warnings) if warnings else "")

    def _show_preview_message(self, text: str | Text) -> None:
        # A `str` is the app's own message; anything quoting the user's tree
        # (file content, an error naming a file) arrives as `literal()`.
        # Always clear, even if no image was showing — harmless when there's
        # nothing to clear, and this is the one path every non-image state
        # (directory, no-PDF, no-poppler, MD mode) funnels through.
        self.query_one("#preview-image", PdfPreview).clear_image()
        self.query_one("#preview-image", PdfPreview).display = False
        message = self.query_one("#preview-message", Static)
        message.display = True
        message.update(text)

    def _show_preview_image(self, png_bytes: bytes, region: Region) -> None:
        self.query_one("#preview-message", Static).display = False
        image = self.query_one("#preview-image", PdfPreview)
        image.display = True
        image.show_image(png_bytes, region)

    def _apply_if_current(self, generation: int, callback: Callable[[], None]) -> None:
        if generation == self._preview_generation:
            callback()

    def _preview_content_region(self) -> Region:
        """The preview panel's own content area (inside its border).

        Read off `#preview-body`, not `#preview-image` itself: the container
        is always displayed, so its region is always current, while the image
        widget's `display` is flipped on and off and its `region` can still
        be the stale, pre-layout one right after `display` turns `True`.
        It is the body rather than the whole panel so that a warnings block
        above it shrinks the image instead of pushing it past the border (M9).
        """
        return self.query_one("#preview-body", Vertical).content_region

    def _update_preview(self, data: NodeData | None) -> None:
        self._preview_data = data
        self._preview_generation += 1
        generation = self._preview_generation

        # Before the mode branch, and MD mode only: in PDF mode the block would
        # displace the rendered page, so the mode shows the page and the
        # file's `⚠` in the tree alone (M9).
        self._show_warnings(data.warnings if data is not None and self.mode == "md" else [])

        if data is None or data.kind == "dir":
            self._show_preview_message(MSG_SELECT_FILE)
            return

        if self.mode == "md":
            try:
                text = data.path.read_text(encoding="utf-8")
            except OSError as exc:
                self._show_preview_message(literal(f"Could not read {data.path.name}: {exc}"))
                return
            self._show_preview_message(literal(text))
            return

        pdf_path = notebook_path_for(data.path)
        if not pdf_path.exists():
            self._show_preview_message(MSG_NO_PDF)
            return

        if not pdftoppm_available():
            self._show_preview_message(MSG_NO_POPPLER)
            return

        if not supports_kitty_graphics():
            self._run_extract_text(generation, pdf_path)
            return

        region = self._preview_content_region()
        cell_w, cell_h = cell_pixel_size()
        width_px = max(region.width * cell_w, 1)
        height_px = max(region.height * cell_h, 1)
        self._run_rasterise(generation, pdf_path, width_px, height_px, region)

    def _run_extract_text(self, generation: int, pdf_path: Path) -> None:
        def _worker() -> None:
            try:
                text = extract_text(pdf_path)
            except (subprocess.CalledProcessError, OSError) as exc:
                self.app.call_from_thread(
                    self._apply_if_current,
                    generation,
                    partial(self._show_preview_message, literal(f"Preview failed: {exc}")),
                )
                return
            self.app.call_from_thread(
                self._apply_if_current,
                generation,
                partial(self._show_preview_message, literal(text)),
            )

        self.app.run_worker(_worker, thread=True, exclusive=True, group="preview")

    def _run_rasterise(
        self, generation: int, pdf_path: Path, width_px: int, height_px: int, region: Region
    ) -> None:
        def _worker() -> None:
            try:
                png_bytes = self._raster_cache.get_or_rasterise(pdf_path, width_px, height_px)
            except (subprocess.CalledProcessError, OSError) as exc:
                self.app.call_from_thread(
                    self._apply_if_current,
                    generation,
                    partial(self._show_preview_message, literal(f"Preview failed: {exc}")),
                )
                return
            self.app.call_from_thread(
                self._apply_if_current,
                generation,
                partial(self._show_preview_image, png_bytes, region),
            )

        self.app.run_worker(_worker, thread=True, exclusive=True, group="preview")

    @on(Tree.NodeSelected)
    def _on_node_selected(self, event: Tree.NodeSelected[NodeData]) -> None:
        data = event.node.data
        if data is None or data.kind != "file":
            return
        if self.mode == "pdf":
            open_source_pdf(self.app, data.path, tree_root=self.tree_root, kind=self.kind)
        else:
            self._open_md(data.path)

    def _open_md(self, source_path: Path) -> None:
        # nvim is optional (`doctor` says so), so its absence is a message —
        # checked before suspending, so the screen never goes away at all
        # (Sprint 6 M2, #9).
        if shutil.which("nvim") is None:
            self.app.notify(MSG_NO_NVIM, severity="warning")
            return
        try:
            mtime_before = source_path.stat().st_mtime
            with self.app.suspend():
                # Real tabs: a row's columns are tab-separated, and an `nvim`
                # configured with `expandtab` would turn a hand-typed Tab into
                # spaces the parser cannot read as columns (M9).
                subprocess.run(NVIM_COMMAND + [str(source_path)])
            mtime_after = source_path.stat().st_mtime
        except (OSError, subprocess.SubprocessError) as exc:
            # `which` succeeding doesn't guarantee the exec does. The editor
            # never ran, so there is nothing to recompile.
            self.app.notify(f"Could not open nvim: {exc}", severity="error", markup=False)
            return

        if mtime_after != mtime_before:
            notebook_path = notebook_path_for(source_path)
            self.app.run_worker(
                partial(
                    autocompile_one,
                    self.app,
                    source_path,
                    notebook_path,
                    kind=self.kind,
                    grammar=is_grammar(source_path, self.tree_root),
                ),
                thread=True,
                exclusive=False,
                group="autocompile",
            )
            # The file the user just edited is re-read, and the whole tree
            # with it (Sprint 6 M9): this is the moment the app "enters
            # through" a hand edit. A non-trivial change — a category renamed,
            # added or removed — is on screen because the tree is rebuilt from
            # disk, and a trivial one redraws the same thing, which is what
            # makes it trivial. No before/after comparison is kept.
            self._rebuild_tree(select_path=source_path)
            self._notify_warnings(source_path)

    def _notify_warnings(self, source_path: Path) -> None:
        """Say how many warnings the file now has, if any. The list itself is
        in the preview pane — a notification expires, and a raw line from a
        file is not something to read in one."""
        node = _node_for(self.query_one("#inspect-tree", InspectTree), source_path)
        count = len(node.data.warnings) if node is not None and node.data is not None else 0
        if count:
            noun = "warning" if count == 1 else "warnings"
            self.app.notify(
                f"{source_path.name}: {count} {noun} — see the preview.",
                severity="warning",
                markup=False,
            )

    def _target_dir_for_new_file(self) -> Path:
        """The directory `m` creates into: the cursor's own dir, or its file's parent."""
        tree = self.query_one("#inspect-tree", InspectTree)
        node = tree.cursor_node
        if node is None or node.data is None:
            return self.tree_root
        if node.data.kind == "dir":
            return node.data.path
        return node.data.path.parent

    def action_delete(self) -> None:
        tree = self.query_one("#inspect-tree", InspectTree)
        node = tree.cursor_node
        if node is None or node.data is None or node is tree.root:
            self.app.notify("Nothing to delete here.", severity="warning")
            return

        data = node.data
        if data.kind == "dir":
            file_count = sum(1 for _ in data.path.rglob("*.md"))
            noun = "file" if file_count == 1 else "files"
            message = f"Delete {data.path.name}/ and its {file_count} {noun}?"
        else:
            message = f"Delete {data.path.name}?"

        def _handle(confirmed: bool | None) -> None:
            if not confirmed:
                return
            pending = PendingDelete.of(data)
            if pending is None:
                self.app.notify(
                    f"Could not read {data.path.name} — not deleted.",
                    severity="error",
                    markup=False,
                )
                return
            self._pending_deletes.append(pending)
            self._rebuild_tree()
            self.app.notify(f"Deleted {data.path.name}. Press u to undo.", markup=False)

        self.app.push_screen(ConfirmDialog(message), _handle)

    def action_undo(self) -> None:
        if not self._pending_deletes:
            self.app.notify("Nothing to undo.", severity="warning")
            return
        pending = self._pending_deletes.pop()
        self._rebuild_tree()
        self.app.notify(f"Restored {pending.path.name}.", markup=False)

    def action_rename(self) -> None:
        tree = self.query_one("#inspect-tree", InspectTree)
        node = tree.cursor_node
        if node is None or node.data is None or node is tree.root:
            self.app.notify("Nothing to rename here.", severity="warning")
            return

        data = node.data
        current_name = data.path.name if data.kind == "dir" else data.path.stem

        def _handle(new_name: str | None) -> None:
            if not new_name or new_name == current_name or self._refuse_name(new_name):
                return
            try:
                if data.kind == "dir":
                    self._rename_dir(data, new_name)
                else:
                    self._rename_file(data, new_name)
            except OSError as exc:
                self._report_os_error(f"Could not rename {current_name}", exc)
            self._rebuild_tree()

        self.app.push_screen(PromptDialog("New name:", current_name), _handle)

    def _refuse_name(self, name: str) -> bool:
        """Notify and return `True` if `name` can't be a name in the tree —
        before anything touches the filesystem (Sprint 6 M2, #14)."""
        problem = validate_name(name)
        if problem is None:
            return False
        self.app.notify(problem, severity="error", markup=False)
        return True

    def _report_os_error(self, what: str, exc: OSError) -> None:
        """Validation can't rule out a permissions error, a full disk or a
        race; the screen stays up and says what happened instead."""
        reason = exc.strerror or str(exc)
        self.app.notify(f"{what}: {reason}.", severity="error", markup=False)

    def _rename_dir(self, data: NodeData, new_name: str) -> None:
        new_path = data.path.parent / new_name
        if is_taken(new_path, data.path):
            self.app.notify(f"{new_name} already exists.", severity="error", markup=False)
            return
        old_path = data.path
        move(old_path, new_path)
        self._remap_pending_deletes(old_path, new_path)

    def _rename_file(self, data: NodeData, new_name: str) -> None:
        parent = data.path.parent
        new_md = parent / f"{new_name}.md"
        new_pdf = parent / f"{new_name}.pdf"
        old_pdf = notebook_path_for(data.path)
        if is_taken(new_md, data.path) or is_taken(new_pdf, old_pdf):
            self.app.notify(f"{new_name} already exists.", severity="error", markup=False)
            return

        had_pdf = old_pdf.exists()

        # Move first, retitle after: a rename that fails must leave the header
        # matching the filename the file still has (Sprint 6 M2, #14).
        old_path = data.path
        move(old_path, new_md)
        self._remap_pending_deletes(old_path, new_md)
        retitled = _retitle(new_md.read_text(encoding="utf-8"), new_name)
        new_md.write_text(retitled, encoding="utf-8")

        if had_pdf:
            old_pdf.unlink()
            self.app.run_worker(
                partial(
                    autocompile_one,
                    self.app,
                    new_md,
                    new_pdf,
                    kind=self.kind,
                    grammar=is_grammar(new_md, self.tree_root),
                ),
                thread=True,
                exclusive=False,
                group="autocompile",
            )

    def _remap_pending_deletes(self, old_path: Path, new_path: Path) -> None:
        """Follow a rename with every pending delete at or under `old_path`.

        Without this, a rename un-deletes the file in the tree and leaves the
        pending path aimed at whatever later occupies it — so the wrong file is
        the one that goes on leaving the screen (Sprint 6 M1, #1).
        """
        for pending in self._pending_deletes:
            pending.remap(old_path, new_path)

    def action_new_dir(self) -> None:
        def _handle(name: str | None) -> None:
            if not name or self._refuse_name(name):
                return
            new_path = self.tree_root / name
            if new_path.exists():
                self.app.notify(f"{name} already exists.", severity="error", markup=False)
                return
            try:
                new_path.mkdir()
            except OSError as exc:
                self._report_os_error(f"Could not create {name}", exc)
                return
            self._rebuild_tree()

        self.app.push_screen(PromptDialog("New directory name:"), _handle)

    def action_new_file(self) -> None:
        target_dir = self._target_dir_for_new_file()

        def _handle(name: str | None) -> None:
            if not name or self._refuse_name(name):
                return
            new_md = target_dir / f"{name}.md"
            new_pdf = target_dir / f"{name}.pdf"
            if new_md.exists() or new_pdf.exists():
                self.app.notify(f"{name} already exists.", severity="error", markup=False)
                return
            try:
                new_md.write_text(f"# {name}\n", encoding="utf-8")
            except OSError as exc:
                self._report_os_error(f"Could not create {name}", exc)
                return
            self.app.run_worker(
                partial(
                    autocompile_one,
                    self.app,
                    new_md,
                    new_pdf,
                    kind=self.kind,
                    grammar=is_grammar(new_md, self.tree_root),
                ),
                thread=True,
                exclusive=False,
                group="autocompile",
            )
            self._rebuild_tree()

        self.app.push_screen(PromptDialog("New file name:"), _handle)
