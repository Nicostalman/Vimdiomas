from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Literal

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Blur, Focus
from textual.widgets import Button, Input, Static, Tree
from textual.widgets._tree import TreeNode

from vimdiomas.compile import notebook_path_for
from vimdiomas.config import NotebookConfig
from vimdiomas.input_method import switch_to
from vimdiomas.models import Category, Deck, Entry, Subtitle
from vimdiomas.parser import parse
from vimdiomas.store import DirNode, FileNode, is_grammar, walk
from vimdiomas.tui.screens.base import (
    FooterHint,
    NoShiftArrowsTree,
    autocompile_one,
    build_dir_tree,
    file_leaf_label,
    literal,
)
from vimdiomas.tui.screens.panels import Backpanel, Panel, PanelScreen, SelectField, TextField
from vimdiomas.writer import save

NodeKind = Literal["dir", "file", "category", "uncategorized", "new_category"]

VALID_TARGET_KINDS = {"category", "uncategorized", "new_category"}

# `parser.py` reserves the literal heading `## Tags` and nothing else, so a
# category by this exact name would write a heading the parser reads back as
# the file's tag block instead (Sprint 6 M1, #8). Matched case-sensitively for
# the same reason: `## tags` parses as an ordinary category and works, so
# refusing it would reject a name that isn't broken.
RESERVED_CATEGORY_NAMES = {"Tags"}

# The sentinel value for the subtitle field's "create a new one" option
# (Sprint 5 M5) — mirrors the tree's own "(new category)" leaf, which is a
# label rather than a value but plays the same role.
NEW_SUBTITLE = "(new subtitle)"

FIELD_ORDER = [
    "category-name",
    "subtitle",
    "subtitle-name",
    "word",
    "reading",
    "translation",
    "note",
]

# The reading (pinyin, for Chinese) is auto-filled from the word and read-only;
# it never takes part in tab navigation between fields.
TAB_SKIP_IDS = {"reading"}

FOOTER_HINT = (
    "Enter go in · Esc go out · Shift+H/L switch panel · "
    "Tab next field · Enter on Create: save"
)


class WordInput(TextField):
    """The word field (hanzi, for Chinese): switches the system input source
    on focus/blur.

    Which sources it switches between comes from the config, read off the
    screen's own `NotebookConfig` at focus/blur time rather than captured at
    construction — so a change made in Settings › Input methods takes effect
    without relaunching (Sprint 4 M6). An unconfigured language switches
    nothing; see `input_method.switch_to`.

    In effect on macOS and Linux only (input_method.py no-ops elsewhere);
    see specs/Sprint-2/features/2026-09-07-m4-macos-input-method-switching/
    and Sprint 5 M7.

    Switching the input source itself makes the terminal briefly lose and
    regain OS-level focus (observed with `macism`, which simulates the
    input-switching hotkey rather than calling a silent API) — Textual
    reports that round trip as this widget's own Blur/Focus, which would
    otherwise re-trigger the switch and loop forever. `Focus.from_app_focus`
    and `App.app_focus` (both set by Textual before either event reaches a
    widget — see `App._watch_app_focus`) distinguish that OS-level blip from
    a real user-driven focus change and are used to ignore it.

    `macism` itself takes 80-300ms per call (it simulates a keypress, not a
    silent API call). Run synchronously, that stalls Textual's event loop —
    every keypress and redraw — for the same span, felt as a stutter right
    when the field gains or loses focus. Both switches run in a worker
    thread instead, owned by `self.app` (not `self`) so a switch started on
    blur still finishes even if leaving the screen right after unmounts this
    widget — see M3's identical `run_worker` ownership call in this same
    module.
    """

    def _switch(self, source_id: str) -> None:
        self.app.run_worker(
            partial(switch_to, source_id), thread=True, group="input-method"
        )

    def _on_focus(self, event: Focus) -> None:
        super()._on_focus(event)
        if not event.from_app_focus:
            self._switch(self.screen.config.input_method)

    def _on_blur(self, event: Blur) -> None:
        super()._on_blur(event)
        if self.app.app_focus:
            self._switch(self.screen.config.translation_input_method)


@dataclass
class NodeData:
    kind: NodeKind
    file_path: Path | None = None
    category_name: str | None = None
    # Whether the file this node belongs to lives under Grammar/ (Sprint 5
    # M5, `store.is_grammar`) — decided once per file when the tree is
    # built, and carried on every leaf under it so the form can tell without
    # re-deriving it from the path each time.
    grammar: bool = False


class EntryTree(NoShiftArrowsTree[NodeData]):
    """The entry screen's tree: categories/uncategorized/new-category leaves.

    Keys and aesthetic are inherited from `NoShiftArrowsTree`; this class
    only adds the category-selection semantics specific to the entry screen.
    """


def build_tree(tree: EntryTree, dir_node: DirNode, tree_root: Path) -> None:
    tree.root.data = NodeData(kind="dir")
    build_dir_tree(
        tree.root,
        dir_node,
        lambda _dir: NodeData(kind="dir"),
        partial(_add_file_leaves, tree_root=tree_root),
    )
    tree.root.expand()


def _add_file_leaves(
    tree_node: TreeNode[NodeData], file_node: FileNode, *, tree_root: Path
) -> None:
    grammar = is_grammar(file_node.path, tree_root)
    node = tree_node.add(
        file_leaf_label(file_node),
        data=NodeData(kind="file", file_path=file_node.path, grammar=grammar),
    )
    node.add_leaf(
        "(uncategorized)",
        data=NodeData(kind="uncategorized", file_path=file_node.path, grammar=grammar),
    )
    for category_name in file_node.categories:
        node.add_leaf(
            literal(category_name),
            data=NodeData(
                kind="category",
                file_path=file_node.path,
                category_name=category_name,
                grammar=grammar,
            ),
        )
    node.add_leaf(
        "(new category)",
        data=NodeData(kind="new_category", file_path=file_node.path, grammar=grammar),
    )


def _subtitle_choices(category: Category) -> list[tuple[str, str]]:
    """The grammar subtitle field's options for `category`: `(none)`, each
    existing subtitle by name, then `(new subtitle)`."""
    choices = [("", "(none)")]
    choices.extend((subtitle.name, subtitle.name) for subtitle in category.subtitles)
    choices.append((NEW_SUBTITLE, NEW_SUBTITLE))
    return choices


class EntryScreen(PanelScreen):
    BINDINGS = [
        Binding("tab", "next_field", "Next field", show=False),
    ]

    def __init__(self, config: NotebookConfig) -> None:
        super().__init__()
        self.config = config
        self.tree_root = config.tree_root
        self._active_target: NodeData | None = None
        self._dirty_files: set[Path] = set()

    def on_unmount(self) -> None:
        self._autocompile_dirty_files()

    def _autocompile_dirty_files(self) -> None:
        dirty_files = list(self._dirty_files)
        self._dirty_files.clear()
        for source_path in dirty_files:
            notebook_path = notebook_path_for(source_path)
            self.app.run_worker(
                partial(
                    autocompile_one,
                    self.app,
                    source_path,
                    notebook_path,
                    kind=self.config.kind,
                    grammar=is_grammar(source_path, self.tree_root),
                ),
                thread=True,
                exclusive=False,
                group="autocompile",
            )

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Horizontal():
                with Panel(id="tree-panel"):
                    yield EntryTree(f"{self.config.language} notebook", id="entry-tree")
                with Panel(id="entry-form"):
                    yield Static("Choose a category", id="target-warning")
                    yield TextField(placeholder="new category name", id="category-name")
                    yield SelectField("Subtitle", [], id="subtitle")
                    yield TextField(placeholder="new subtitle name", id="subtitle-name")
                    kind = self.config.kind
                    yield WordInput(placeholder=kind.word_label, id="word")
                    if kind.has_reading:
                        yield TextField(placeholder=kind.reading_label, id="reading", disabled=True)
                    yield TextField(placeholder="Translation", id="translation")
                    yield TextField(placeholder="Note", id="note")
                    yield Button("Create", id="create-button")
                    yield FooterHint(FOOTER_HINT, id="footer-hint")

    def on_mount(self) -> None:
        super().on_mount()
        tree = self.query_one("#entry-tree", EntryTree)
        build_tree(tree, walk(self.tree_root, kind=self.config.kind), self.tree_root)
        self._apply_target_state(None)

    # -- tree selection -----------------------------------------------

    @on(Tree.NodeHighlighted)
    def _on_node_highlighted(self, event: Tree.NodeHighlighted[NodeData]) -> None:
        data = event.node.data
        new_target = data if data is not None and data.kind in VALID_TARGET_KINDS else None

        if new_target != self._active_target:
            self._active_target = new_target
            self._clear_form()
            self._apply_target_state(new_target)

    def _apply_target_state(self, target: NodeData | None) -> None:
        is_valid = target is not None
        is_new_category = bool(target and target.kind == "new_category")
        is_grammar_category = bool(target and target.kind == "category" and target.grammar)

        self.query_one("#target-warning", Static).display = not is_valid
        self.query_one("#category-name", Input).display = is_new_category
        for reading in self.query("#reading"):
            reading.display = not is_new_category
        for field_id in ("word", "translation", "note"):
            field = self.query_one(f"#{field_id}", Input)
            field.display = not is_new_category
            field.disabled = not is_valid

        subtitle_field = self.query_one("#subtitle", SelectField)
        subtitle_field.display = is_grammar_category
        subtitle_field.disabled = not is_grammar_category
        if is_grammar_category:
            category = self._read_category(target)
            subtitle_field.set_choices(_subtitle_choices(category))
        self._sync_subtitle_name_field(is_grammar_category, subtitle_field.value)

        self.query_one("#create-button", Button).disabled = not is_valid

    def _sync_subtitle_name_field(self, is_grammar_category: bool, subtitle_value: str) -> None:
        subtitle_name_field = self.query_one("#subtitle-name", Input)
        subtitle_name_field.display = is_grammar_category and subtitle_value == NEW_SUBTITLE
        subtitle_name_field.disabled = not subtitle_name_field.display

    @on(SelectField.Changed, "#subtitle")
    def _on_subtitle_changed(self, event: SelectField.Changed) -> None:
        target = self._active_target
        is_grammar_category = bool(target and target.kind == "category" and target.grammar)
        self._sync_subtitle_name_field(is_grammar_category, event.value)
        if is_grammar_category:
            # Picking an option is a step forward in the form, not just a
            # value change (dev feedback) — land on the subtitle-name field
            # for (new subtitle), or straight on the word for (none)/an
            # existing subtitle, rather than leaving focus on the select.
            next_field_id = "subtitle-name" if event.value == NEW_SUBTITLE else "word"
            self.query_one(f"#{next_field_id}").focus()

    def _read_category(self, target: NodeData) -> Category:
        """Re-parse `target`'s file (grammar mode) and return the live
        `Category` object matching `target.category_name` — always freshly
        read from disk, same as every other create path in this screen."""
        deck = self._read_deck(target)
        return next(c for c in deck.categories if c.name == target.category_name)

    def _read_deck(self, target: NodeData) -> Deck:
        deck, _ = parse(
            target.file_path.read_text(encoding="utf-8"),
            target.file_path.stem,
            kind=self.config.kind,
            grammar=target.grammar,
        )
        return deck

    @on(Tree.NodeSelected)
    def _on_node_selected(self, event: Tree.NodeSelected[NodeData]) -> None:
        if self._active_target is not None:
            self._focus_first_field()

    # -- form fields ----------------------------------------------------

    def _visible_field_ids(self) -> list[str]:
        return [
            field_id
            for field_id in FIELD_ORDER
            if field_id not in TAB_SKIP_IDS
            and self.query_one(f"#{field_id}").display
            and not self.query_one(f"#{field_id}").disabled
        ]

    def _focus_first_field(self) -> None:
        fields = self._visible_field_ids()
        if fields:
            self.query_one(f"#{fields[0]}").focus()

    def action_next_field(self) -> None:
        # `Panel.action_focus_content` claims `tab` whenever a panel itself
        # (rather than its content) has focus, so this is only ever reached
        # with a field or the create button focused.
        chain = self._visible_field_ids()
        create_button = self.query_one("#create-button", Button)
        if not create_button.disabled:
            chain = chain + ["create-button"]
        focused = self.focused
        focused_id = focused.id if focused is not None else None
        if focused_id not in chain:
            return
        next_index = (chain.index(focused_id) + 1) % len(chain)
        self.query_one(f"#{chain[next_index]}").focus()

    def _clear_form(self) -> None:
        # "subtitle" is deliberately skipped: a Create leaves the field on
        # the subtitle just used (Sprint 5 M5), so several entries can be
        # added to it in a row without re-selecting it each time. It's only
        # reset by `_apply_target_state`, when the tree target itself
        # changes.
        for field_id in FIELD_ORDER:
            if field_id == "subtitle":
                continue
            for field in self.query(f"#{field_id}"):
                field.value = ""

    @on(Input.Changed, "#word")
    def _on_word_changed(self, event: Input.Changed) -> None:
        # The field's live value, not `event.value`: `TextField` sanitises
        # control characters out of its own value (Sprint 6 M1, #15), so
        # reading the widget makes this handler independent of which `Changed`
        # arrives first rather than able to guess a reading off a raw paste.
        guess_reading = self.config.kind.guess_reading
        if guess_reading is None:
            return
        word = self.query_one("#word", Input).value
        self.query_one("#reading", Input).value = guess_reading(word) if word else ""

    def _read_reading(self) -> str:
        """The reading field's value; `""` for a kind that has none."""
        for reading in self.query("#reading"):
            return reading.value
        return ""

    # -- create -----------------------------------------------------------

    @on(Button.Pressed, "#create-button")
    def _on_create_pressed(self, event: Button.Pressed) -> None:
        self._create_entry()

    def _create_entry(self) -> None:
        target = self._active_target
        if target is None or target.file_path is None:
            return

        if target.kind == "new_category":
            self._create_category(target)
            return

        if target.kind == "category" and target.grammar:
            self._create_grammar_entry(target)
            return

        word = self.query_one("#word", Input).value
        reading = self._read_reading()
        translation = self.query_one("#translation", Input).value
        note = self.query_one("#note", Input).value or None

        if not word:
            return

        entry = Entry(word=word, reading=reading, translation=translation, note=note)
        path = target.file_path
        deck = self._read_deck(target)

        if target.kind == "category":
            category = next(c for c in deck.categories if c.name == target.category_name)
            category.entries.append(entry)
        elif target.kind == "uncategorized":
            deck.uncategorized.append(entry)

        save(deck, path, kind=self.config.kind)
        self._dirty_files.add(path)

        self._clear_form()
        self.notify(f"{word} added successfully!", markup=False)
        self._focus_first_field()

    def _create_grammar_entry(self, target: NodeData) -> None:
        """Create on a grammar file's category target (Sprint 5 M5): the
        entry goes into the category directly (`(none)`), into an existing
        subtitle, or into a subtitle created on the spot via
        `(new subtitle)` — see requirements.md's Decisions."""
        path = target.file_path
        deck = self._read_deck(target)
        category = next(c for c in deck.categories if c.name == target.category_name)

        subtitle_field = self.query_one("#subtitle", SelectField)
        subtitle_value = subtitle_field.value

        word = self.query_one("#word", Input).value
        reading = self._read_reading()
        translation = self.query_one("#translation", Input).value
        note = self.query_one("#note", Input).value or None

        if subtitle_value == NEW_SUBTITLE:
            subtitle_name = self.query_one("#subtitle-name", Input).value.strip()
            if not subtitle_name:
                return

            subtitle = next((s for s in category.subtitles if s.name == subtitle_name), None)
            if subtitle is None:
                subtitle = Subtitle(name=subtitle_name)
                category.subtitles.append(subtitle)

            added_word = None
            if word:
                subtitle.entries.append(
                    Entry(word=word, reading=reading, translation=translation, note=note)
                )
                added_word = word

            save(deck, path, kind=self.config.kind)
            self._dirty_files.add(path)

            self._clear_form()
            subtitle_field.set_choices(_subtitle_choices(category), value=subtitle_name)
            self._sync_subtitle_name_field(True, subtitle_name)

            message = (
                f"{added_word} added successfully!"
                if added_word
                else f"{subtitle_name} added successfully!"
            )
            self.notify(message, markup=False)
            self._focus_first_field()
            return

        if not word:
            return

        entry = Entry(word=word, reading=reading, translation=translation, note=note)
        if subtitle_value:
            subtitle = next(s for s in category.subtitles if s.name == subtitle_value)
            subtitle.entries.append(entry)
        else:
            category.entries.append(entry)

        save(deck, path, kind=self.config.kind)
        self._dirty_files.add(path)

        self._clear_form()
        self.notify(f"{word} added successfully!", markup=False)
        self._focus_first_field()

    def _create_category(self, target: NodeData) -> None:
        # The name is required: an empty (or whitespace-only) name is a
        # no-op, so a category can't be created without one.
        category_name = self.query_one("#category-name", Input).value.strip()
        if not category_name:
            return

        if category_name in RESERVED_CATEGORY_NAMES:
            # Nothing is read and nothing written: unlike a duplicate there is
            # no existing category to fall back on, because the heading this
            # would emit is unreachable by construction.
            self.notify(
                f"{category_name} is reserved and can't be a category name.",
                severity="error",
                markup=False,
            )
            return

        path = target.file_path
        tree = self.query_one("#entry-tree", EntryTree)
        cursor_node = tree.cursor_node
        parent = cursor_node.parent

        existing_node = self._existing_category_leaf(parent, category_name)
        if existing_node is not None:
            # A second `## Food` would be a heading nothing can ever reach
            # (Sprint 6 M1, #18). Selecting the one already there is what
            # subtitle creation does with a duplicate subtitle name, so the two
            # creation paths stop differing — and nothing is written.
            self._select_category_leaf(
                tree, existing_node, path, category_name, target.grammar
            )
            self.notify(f"{category_name} already exists — selected.", markup=False)
            return

        deck = self._read_deck(target)
        deck.categories.append(Category(name=category_name, entries=[]))
        save(deck, path, kind=self.config.kind)
        self._dirty_files.add(path)

        new_node = parent.add_leaf(
            literal(category_name),
            data=NodeData(
                kind="category",
                file_path=path,
                category_name=category_name,
                grammar=target.grammar,
            ),
            before=cursor_node,
        )
        self._select_category_leaf(tree, new_node, path, category_name, target.grammar)
        self.notify(f"{category_name} added successfully!", markup=False)

    @staticmethod
    def _existing_category_leaf(
        file_node: TreeNode[NodeData], category_name: str
    ) -> TreeNode[NodeData] | None:
        """The `file_node` child already standing for `category_name`, if any.

        Compared exactly, not case-insensitively: two categories differing only
        in case are two headings the parser and every lookup treat as distinct,
        so neither is unreachable and there is nothing to refuse.
        """
        for child in file_node.children:
            data = child.data
            if data is not None and data.kind == "category" and data.category_name == category_name:
                return child
        return None

    def _select_category_leaf(
        self,
        tree: EntryTree,
        node: TreeNode[NodeData],
        path: Path,
        category_name: str,
        grammar: bool,
    ) -> None:
        """Land on `node` as the active target, form cleared and focused.

        Shared by the create and the already-exists paths, which differ only in
        whether anything is written and which leaf they land on.
        """
        # A freshly-added node's line number isn't resolved until the next
        # render pass, so move_cursor() must be deferred or it silently
        # fails (cursor jumps to the root instead).
        tree.call_after_refresh(tree.move_cursor, node)

        # Update the form state to match the category right away rather
        # than waiting on the tree's own (deferred) NodeHighlighted for the
        # move above — otherwise focus is left on the Create button instead
        # of moving into the now-visible form, same as landing on any other
        # valid target. `_on_node_highlighted` still fires once the cursor
        # move lands, but is a no-op then since the target already matches.
        self._active_target = NodeData(
            kind="category", file_path=path, category_name=category_name, grammar=grammar
        )
        self._clear_form()
        self._apply_target_state(self._active_target)
        self._focus_first_field()
