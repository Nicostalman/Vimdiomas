from typing import Literal

from textual.actions import SkipAction
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.events import Blur, DescendantFocus
from textual.message import Message
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option, OptionDoesNotExist

from vimdiomas.tui.screens.base import MenuLegend, VimOptionList, literal

Direction = Literal["left", "right", "up", "down"]


def _focus_first_content(container: Widget) -> None:
    """Focus `container`'s first focusable, enabled, displayed descendant in
    the screen's focus chain, or `container` itself if it has none.

    Shared by `Panel.focus_content()` and `Backpanel.focus_content()` (the
    latter only when the backpanel has no `Panel` children — a flat menu,
    where the backpanel's direct content plays the role a panel's content
    plays elsewhere).
    """
    for widget in container.screen.focus_chain:
        if widget is not container and container in widget.ancestors:
            widget.focus()
            return
    container.focus()


def sanitise_field_text(value: str) -> str:
    """`value` with every control character replaced by a single space.

    A tab pasted into a field would be written straight into a triad row and
    silently shift its columns — `苹果<TAB>apple` pasted from a spreadsheet
    became a five-column row (Sprint 6 M1, #15). A newline or any other C0
    control character (and DEL) would corrupt the file in its own way.

    A space, not a deletion: the report's own case is a spreadsheet row, and
    deleting the tab would glue two cells into `苹果apple`, whereas a space
    keeps the boundary visible for the user to fix. One character for one, so
    the cursor never moves under the typist. Leading and trailing whitespace is
    left alone — trimming as the user types would fight them mid-word, and both
    parser and writer already handle edge spaces.
    """
    return "".join(" " if ch < " " or ch == "\x7f" else ch for ch in value)


class TextField(Input):
    """The app's text field for screens built on `PanelScreen`.

    Sanitises its own value as it changes (see `sanitise_field_text`), so the
    user *sees* the cleaned text before pressing Create rather than having it
    silently altered at save time — `mission.md`'s "never silently discard".
    Done here rather than per-screen so every field in the app is covered,
    including ones added later.

    No `escape` binding of its own: it bubbles past this widget to the
    `Panel` it sits in (see `Panel`). shift+left/shift+right are bound to a
    no-op, overriding `Input`'s own default (extend the text selection) —
    dev feedback, hands-on: shift-arrows should mimic the letter panel-move
    keys (H/L/J/K) exactly, including doing nothing on content, rather than
    keep a widget-specific default alive underneath them. A class of its
    own anyway, so every field's look and any future shared behaviour live
    in one place.
    """

    BINDINGS = [
        Binding("shift+left", "nothing", "Nothing", show=False),
        Binding("shift+right", "nothing", "Nothing", show=False),
    ]

    def action_nothing(self) -> None:
        pass

    def validate_value(self, value: str) -> str:
        # The reactive's own validation hook, which runs before `Changed` is
        # posted — so every listener (Entry's word -> reading auto-fill among
        # them) sees the cleaned value, and a programmatic assignment is
        # covered as well as a keystroke or a paste.
        return sanitise_field_text(value)


class _SelectList(VimOptionList):
    """The list a `SelectField` deploys.

    `escape` collapses back to the field and is **not** allowed to bubble any
    further: this is the content → field rung of the nesting ladder
    (`design.md`), and only the field's own `escape` — inherited, unbound,
    falling through to the `Panel` — climbs past it.
    """

    BINDINGS = [
        Binding("escape", "collapse", "Collapse", show=False),
    ]

    def action_collapse(self) -> None:
        self.select_field.collapse()

    def _on_blur(self, event: Blur) -> None:
        super()._on_blur(event)
        # Focus can leave an open list directly — `tab` from here, or
        # another widget being focused outright — without ever passing
        # through the field, so the field's own blur handler would never
        # fire. Same deferred check, for the same reason.
        self.select_field.collapse_if_focus_left()

    @property
    def select_field(self) -> "SelectField":
        return self.ancestors_with_self[1]  # type: ignore[return-value]


class SelectField(Vertical):
    """A field whose value is chosen from a list that deploys below it.

    The dev's own description of the input-method question (Sprint 4 M6):
    "inside each field a list will deploy with all available input methods
    and the user will be able to choose the corresponding". It is a field
    rather than a menu because it has a value the screen reads back, and it
    deploys rather than sitting open because a screen asks two of these at
    once and two permanently open lists would bury the button underneath
    them.

    It nests exactly as `design.md`'s model expects, adding one rung:
    **list → field → panel → backpanel**. `enter` on the focused field
    deploys the list and focuses it; `enter` on an option takes it; `escape`
    on the list collapses without changing anything; `escape` on the
    collapsed field falls through to the `Panel`, unbound here, like
    `TextField`'s.

    Guarded on `self.has_focus` with `SkipAction` on failure, same as
    `Panel`'s own bindings and for the same reason: a screen with its own
    `enter`/`tab` handling must still see the key when this field isn't the
    thing focused.
    """

    can_focus = True
    DEFAULT_CLASSES = "select-field"

    BINDINGS = [
        Binding("enter", "expand", "Open", show=False),
        Binding("shift+left", "nothing", "Nothing", show=False),
        Binding("shift+right", "nothing", "Nothing", show=False),
    ]

    class Changed(Message):
        """Posted when the user picks an option from the deployed list —
        not when `value` is set from code (e.g. by `set_choices`). Entry's
        grammar subtitle field (Sprint 5 M5) uses this to show or hide the
        new-subtitle name field as the selection changes."""

        def __init__(self, select_field: "SelectField", value: str) -> None:
            self.select_field = select_field
            self.value = value
            super().__init__()

        @property
        def control(self) -> "SelectField":
            return self.select_field

    def __init__(
        self,
        label: str,
        choices: list[tuple[str, str]],
        value: str = "",
        empty_text: str = "(none available)",
        short_labels: dict[str, str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.label = label
        self.choices = choices
        self.empty_text = empty_text
        # The collapsed line has the field's label in front of it and a
        # panel's width around it, so it can want a shorter form than the
        # list does — input methods show their raw ID while choosing and
        # only their name once chosen. Defaults to the list's own label.
        self.short_labels = short_labels or {}
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, new_value: str) -> None:
        self._value = new_value
        if self.is_mounted:
            self._render_display()

    def set_choices(self, choices: list[tuple[str, str]], value: str = "") -> None:
        """Replace the deployed list's options and reset the field's value.

        Used where a field's choices depend on what's currently selected
        elsewhere on the screen (Entry's grammar subtitle field, Sprint 5
        M5: the subtitle list is per-category) rather than being fixed at
        construction the way Settings' input-method lists are.
        """
        self.choices = choices
        self.value = value
        if self.is_mounted:
            option_list = self.query_one(_SelectList)
            option_list.clear_options()
            for choice_value, label in choices:
                option_list.add_option(Option(literal(label), id=choice_value))

    def _label_for(self, value: str) -> str:
        if value in self.short_labels:
            return self.short_labels[value]
        for choice_value, choice_label in self.choices:
            if choice_value == value:
                return choice_label
        return self.empty_text if not value else value

    def compose(self) -> ComposeResult:
        yield Static(id=self._display_id, classes="select-display")
        yield _SelectList(
            *(Option(literal(label), id=value) for value, label in self.choices),
            id=self._list_id,
            classes="select-list",
        )

    @property
    def _display_id(self) -> str:
        return f"{self.id}-display" if self.id else "select-display"

    @property
    def _list_id(self) -> str:
        return f"{self.id}-list" if self.id else "select-list"

    def on_mount(self) -> None:
        self.query_one(_SelectList).display = False
        self._render_display()

    def _render_display(self) -> None:
        # Choices can be user text — Entry's subtitle names (Sprint 6 M2, #16).
        self.query_one(f"#{self._display_id}", Static).update(
            literal(f"{self.label}: {self._label_for(self._value)}")
        )

    @property
    def expanded(self) -> bool:
        return self.query_one(_SelectList).display

    def expand(self) -> None:
        if not self.choices:
            return
        option_list = self.query_one(_SelectList)
        option_list.display = True
        if self._value:
            for index, (choice_value, _) in enumerate(self.choices):
                if choice_value == self._value:
                    option_list.highlighted = index
                    break
        option_list.focus()

    def collapse(self) -> None:
        self.query_one(_SelectList).display = False
        self.focus()

    def action_expand(self) -> None:
        if not self.has_focus:
            raise SkipAction()
        self.expand()

    def action_nothing(self) -> None:
        pass

    def _on_blur(self, event: Blur) -> None:
        super()._on_blur(event)
        # Tabbing away from a field whose list is open would otherwise leave
        # it deployed over the widgets below it. Deferred, because focusing
        # the list itself also blurs this container: where focus actually
        # landed isn't settled until after the refresh.
        self.collapse_if_focus_left()

    def collapse_if_focus_left(self) -> None:
        self.call_after_refresh(self._collapse_if_focus_left)

    def _collapse_if_focus_left(self) -> None:
        if not self.is_mounted:
            return
        focused = self.screen.focused
        if focused is not None and (focused is self or self in focused.ancestors):
            return
        self.query_one(_SelectList).display = False

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        event.stop()
        if event.option.id is not None:
            self.value = event.option.id
            self.post_message(self.Changed(self, self.value))
        self.collapse()


class _ScrollsFocusIntoView:
    """Mixin for a scrollable container that keeps whatever gains focus
    inside it visible (M1, screen real estate).

    `DescendantFocus` bubbles to every ancestor of a widget that gains
    focus, so handling it once here — on `Panel` and `Backpanel` — covers
    every way focus can land inside one (tab-cycling, shift+hjkl panel
    moves, `enter`/`focus_content()`, a screen's own landing focus) without
    a hook at each call site. `scroll_visible()` is a no-op when the widget
    is already visible, and walks up through every scrollable ancestor
    (including this container's own `overflow-y: auto`), so it's safe to
    call unconditionally.
    """

    def _on_descendant_focus(self, event: DescendantFocus) -> None:
        event.widget.scroll_visible()


class Panel(_ScrollsFocusIntoView, Vertical):
    """A bordered region of a screen, holding the content composed inside it.

    `can_focus = True`: a panel with no enabled content (Entry's form with
    no target selected) still needs somewhere to rest focus. The `panel`
    CSS class carries the accent/dim border in `app.tcss` — accent while
    the panel or anything inside it has focus (`:focus, :focus-within`),
    dim otherwise.

    Bindings here bubble up from whatever content has focus (Textual
    bubbles from the focused widget through its ancestors), which is how
    `escape`, `enter` and `tab` reach the panel without content having to
    bind them itself. Guarding on `self.has_focus` — and raising
    `SkipAction` rather than silently returning when it's false — is what
    keeps this safe: they must act only when the panel *itself* is
    focused, not when its content is, and `SkipAction` tells Textual's
    bubbling to keep looking rather than treating the key as handled. That
    matters for `tab`: a screen with its own field-cycling `tab` binding
    (Entry does) needs to still see the key when content, not the panel,
    has focus.

    `escape` on an already-focused panel only reaches the backpanel when
    `Backpanel.reachable()` says so — dev feedback, hands-on: a screen with
    only one panel (Browse, Inspect Tree) has nothing to gain by climbing
    further, the same reasoning that keeps a flat menu's `escape` from
    reaching the backpanel at all. See `Backpanel.reachable`.
    """

    can_focus = True
    DEFAULT_CLASSES = "panel"

    BINDINGS = [
        Binding("escape", "defocus", "Defocus", show=False),
        Binding("enter,tab", "focus_content", "Focus content", show=False),
        Binding("H,shift+left", "move('left')", "Panel left", show=False),
        Binding("L,shift+right", "move('right')", "Panel right", show=False),
        Binding("K,shift+up", "move('up')", "Panel up", show=False),
        Binding("J,shift+down", "move('down')", "Panel down", show=False),
    ]

    @property
    def backpanel(self) -> "Backpanel":
        return self.screen.query_one(Backpanel)

    def focus_content(self) -> None:
        """Focus this panel's first focusable, enabled, displayed content
        widget, or the panel itself if it has none."""
        _focus_first_content(self)

    def action_focus_content(self) -> None:
        if not self.has_focus:
            raise SkipAction()
        self.focus_content()

    def action_defocus(self) -> None:
        if self.has_focus:
            if self.backpanel.reachable():
                self.backpanel.focus()
        else:
            self.focus()

    def action_move(self, direction: Direction) -> None:
        if not self.has_focus:
            raise SkipAction()
        neighbour = self.backpanel.neighbour(self, direction)
        if neighbour is not None:
            neighbour.focus_content()


class Backpanel(_ScrollsFocusIntoView, Container):
    """The screen's outermost container, holding every panel.

    `can_focus = True` so it's a real resting place — one level above every
    panel, reached by `esc` from a panel and nowhere further up: `esc` on the
    backpanel itself is a no-op, deliberately swallowing the key rather than
    letting it bubble to the screen. Bordered (`.backpanel` in `app.tcss`)
    with a border that's **always accent, regardless of focus** — dev
    feedback, hands-on (Sprint 4 M5): unlike `Panel`, the backpanel is the
    one place where a focus change produced no visible change of its own,
    since every panel going dim already shows that focus left them. `H`/
    `L`/`J`/`K` and their shift-arrow equivalents jump straight to
    the edge-most panel in that direction — dev feedback, hands-on: `enter`
    already reached the first panel from here, and not being able to reach
    the *last* one directly, or move vertically, felt like a gap once there
    was a border making the backpanel a real place to be.

    A screen with no `Panel` children at all — a flat menu, Sprint 4 M2 —
    puts its content directly inside the backpanel instead. There being no
    panels already makes `focus_edge`/`neighbour` no-ops, with no
    special-casing needed.

    **The backpanel is only reachable via `escape` when the screen has more
    than one panel** (`reachable()`) — dev feedback, hands-on: with zero
    panels (a menu) or exactly one (Browse, Inspect Tree), there's nothing
    to gain by climbing there — no second panel to jump to, nothing else to
    see — so `escape` from the lone panel, or from a menu's content
    directly, does nothing instead. `Panel.action_defocus` and this class's
    own `action_defocus` both check `reachable()` before focusing the
    backpanel. Only a screen with two or more panels (Entry, and any future
    multi-panel screen) ever actually reaches it this way.

    `enter`/`tab` and the edge-jump actions guard on `self.has_focus` the
    same way `Panel`'s do, raising `SkipAction` rather than returning when
    it's false — otherwise `tab` bubbling up from a screen's content (Inspect
    Tree's tree, whose own `tab` binding toggles PDF/MD mode) would be
    silently swallowed here instead of reaching that binding.
    """

    can_focus = True
    DEFAULT_CLASSES = "backpanel"

    BINDINGS = [
        Binding("escape", "defocus", "Defocus", show=False),
        Binding("enter,tab", "focus_content", "Focus content", show=False),
        Binding("H,shift+left", "focus_edge('left')", "Leftmost panel", show=False),
        Binding("L,shift+right", "focus_edge('right')", "Rightmost panel", show=False),
        Binding("K,shift+up", "focus_edge('up')", "Topmost panel", show=False),
        Binding("J,shift+down", "focus_edge('down')", "Bottommost panel", show=False),
    ]

    def panels(self) -> list[Panel]:
        return list(self.query(Panel))

    def reachable(self) -> bool:
        """Whether `escape` should ever be able to focus this backpanel.

        Only true with more than one panel — with zero (a flat menu) or
        exactly one (Browse, Inspect Tree), there's no second panel to
        jump to and nothing else to see here.
        """
        return len(self.panels()) > 1

    def first_panel(self) -> Panel | None:
        """The leftmost, then topmost, panel by on-screen region."""
        return self.edge_panel("left")

    def edge_panel(self, direction: Direction) -> Panel | None:
        """The extreme panel in `direction`, by on-screen region.

        Ties are broken by the other axis: leftmost for a vertical
        direction, topmost for a horizontal one — the same secondary
        criterion "leftmost, then topmost" already uses for `first_panel`.
        """
        panels = self.panels()
        if not panels:
            return None
        key = {
            "left": lambda p: (p.region.x, p.region.y),
            "right": lambda p: (-p.region.right, p.region.y),
            "up": lambda p: (p.region.y, p.region.x),
            "down": lambda p: (-p.region.bottom, p.region.x),
        }[direction]
        return min(panels, key=key)

    def neighbour(self, panel: Panel, direction: Direction) -> Panel | None:
        """The nearest panel strictly on `direction`'s side of `panel`.

        "Strictly on that side" means the candidate's region doesn't
        overlap `panel`'s along the axis of movement. Ties (equal edge
        distance) are broken by how close the two panels' centres are on
        the other axis. No wraparound: with no candidate, `None`.
        """
        region = panel.region
        candidates: list[tuple[int, float, Panel]] = []
        for other in self.panels():
            if other is panel:
                continue
            other_region = other.region
            if direction == "left" and other_region.right <= region.x:
                distance = region.x - other_region.right
                tie = abs(other_region.center[1] - region.center[1])
            elif direction == "right" and other_region.x >= region.right:
                distance = other_region.x - region.right
                tie = abs(other_region.center[1] - region.center[1])
            elif direction == "up" and other_region.bottom <= region.y:
                distance = region.y - other_region.bottom
                tie = abs(other_region.center[0] - region.center[0])
            elif direction == "down" and other_region.y >= region.bottom:
                distance = other_region.y - region.bottom
                tie = abs(other_region.center[0] - region.center[0])
            else:
                continue
            candidates.append((distance, tie, other))
        if not candidates:
            return None
        candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
        return candidates[0][2]

    def focus_content(self) -> None:
        """Focus the first panel's content — or, with no panels at all (a
        flat menu), this backpanel's own first focusable content directly."""
        first = self.first_panel()
        if first is not None:
            first.focus_content()
        else:
            _focus_first_content(self)

    def action_defocus(self) -> None:
        if not self.reachable():
            return
        if not self.has_focus:
            self.focus()

    def action_focus_content(self) -> None:
        if not self.has_focus:
            raise SkipAction()
        self.focus_content()

    def action_focus_edge(self, direction: Direction) -> None:
        if not self.has_focus:
            raise SkipAction()
        panel = self.edge_panel(direction)
        if panel is not None:
            panel.focus_content()


class PanelScreen(Screen):
    """The screen base for the backpanel/panel/content model.

    `AUTO_FOCUS = ""` turns off Textual's own "focus the first focusable
    widget" behaviour. `App.AUTO_FOCUS` defaults to `"*"`, and a *screen's*
    `AUTO_FOCUS` only overrides that default when it's falsy but not `None`
    — `None` means "unset", which falls back to the app-level default rather
    than disabling it (verified against Textual 8.2.8's
    `Screen._update_auto_focus`). So `on_mount`'s own landing logic, not
    Textual's default, is what sets initial focus. Regions aren't known
    until the first layout pass, so landing in the first panel's content is
    deferred with `call_after_refresh` rather than done inline here.

    A subclass with its own `on_mount` (to build a tree, say) must call
    `super().on_mount()` to still get this.
    """

    AUTO_FOCUS = ""

    BINDINGS = [
        Binding("q", "back_or_quit", "Back", show=False),
    ]

    def action_back_or_quit(self) -> None:
        if isinstance(self.focused, Input):
            return
        self.app.pop_screen()

    def on_mount(self) -> None:
        self.call_after_refresh(self._focus_first_panel_content)

    def _focus_first_panel_content(self) -> None:
        self.query_one(Backpanel).focus_content()


class FormScreen(PanelScreen):
    """A `PanelScreen` whose panel holds several focusable widgets in a
    known order, cycled by `tab`.

    Left to Textual's default focus-chain cycling, `tab` would visit the
    `Panel` and the `Backpanel` themselves as extra stops, both being
    `can_focus=True` — the same bug class `MenuScreen` guards against with
    its `tab` no-op, and `BrowseScreen`/`EntryScreen` with their own
    field-cycling overrides. A subclass lists its content in tab order via
    `content_ids()`; nothing else is cycled.

    Extracted from the wizard's `_WizardStep` (Sprint 4 M5) when Settings'
    input-method screen needed exactly the same thing (M6).
    """

    BINDINGS = [
        Binding("tab", "next_field", "Next field", show=False),
    ]

    def content_ids(self) -> list[str]:
        raise NotImplementedError

    def action_next_field(self) -> None:
        ids = self.content_ids()
        focused = self.focused
        focused_id = focused.id if focused is not None else None
        if focused_id not in ids:
            return
        next_index = (ids.index(focused_id) + 1) % len(ids)
        self.query_one(f"#{ids[next_index]}").focus()


class MenuOption(Option):
    """A menu row that carries the sentence the menu's legend shows while the
    row is highlighted (Sprint 6 M4). The description is required: a menu
    cannot be built from a plain `Option`, so a new menu can't leave its
    options undescribed (`MenuScreen.compose`)."""

    def __init__(self, prompt, description: str, id: str | None = None) -> None:
        super().__init__(prompt, id=id)
        self.description = description


class MenuScreen(PanelScreen):
    """A screen whose whole content is one centered `OptionList`, directly
    inside the backpanel with no `Panel` in between — the flat model
    `Backpanel` supports for a screen with no panels at all (see its
    docstring). Shared by every menu (landing, main menu, settings) so their
    look moves together from one place, the same rationale as `VimTree` for
    tree styling — the `backpanel-flat` CSS class carries this screen's
    layout (`app.tcss`); the border itself is just `Backpanel`'s own
    always-accent one, nothing extra needed for a flat menu. The list
    itself has no border of its own (dev's call: the backpanel's own
    border is enough, unlike Browse's results list, which keeps one).

    `tab` is bound to a no-op — a bug caught in dev hands-on testing: with
    the `OptionList` as the only focusable content, Textual's default
    focus-chain cycling for `tab` moved focus off it and onto the
    `Backpanel` itself (also `can_focus=True`, and part of that chain),
    visibly defocusing the list for no reason — the same class of bug
    `BrowseScreen`/`EntryScreen`/the wizard's `_WizardStep` already guard
    against with their own `action_next_field` overrides, here with
    nothing to cycle *to* since there's only ever the one widget.

    Every option is a `MenuOption`, and the list is followed by a
    `MenuLegend` showing the highlighted option's description. The legend
    is always two lines tall, so moving the cursor never shifts the menu.

    A subclass implements `menu_options()` instead of `compose()`.
    """

    BINDINGS = [
        Binding("tab", "nothing", "Nothing", show=False),
    ]

    def action_nothing(self) -> None:
        pass

    def menu_options(self) -> list[MenuOption]:
        raise NotImplementedError

    def compose(self) -> ComposeResult:
        # `classes=` on a widget replaces `DEFAULT_CLASSES` rather than
        # adding to it, so "backpanel" (Backpanel.DEFAULT_CLASSES) has to be
        # named again alongside "backpanel-flat".
        with Backpanel(classes="backpanel backpanel-flat"):
            options = self.menu_options()
            for option in options:
                if not isinstance(option, MenuOption):
                    raise TypeError(
                        f"{type(self).__name__}.menu_options() must return "
                        f"MenuOptions (with a description), got {option!r}"
                    )
            yield VimOptionList(*options)
            yield MenuLegend(id="menu-legend")

    def on_mount(self) -> None:
        super().on_mount()
        option_list = self.query_one(VimOptionList)
        if option_list.option_count:
            index = option_list.highlighted or 0
            self._show_description(option_list.get_option_at_index(index))

    def on_screen_resume(self) -> None:
        """Rebuild the list from `menu_options()` when the screen is shown
        again, so a menu built from the running config follows a change made
        on a screen above it — a language added in Settings reaches the
        landing menu without a relaunch (Sprint 6 M7). Nothing happens, and
        nothing flickers, when the options are what they were."""
        option_list = self.query_one(VimOptionList)
        options = self.menu_options()

        def shape(items) -> list[tuple]:
            return [(item.id, str(item.prompt), item.description) for item in items]

        if shape(options) == shape(option_list.options):
            return
        highlighted = option_list.highlighted_option
        option_list.clear_options()
        option_list.add_options(options)
        if not options:
            self.query_one(MenuLegend).update("")
            return
        index = 0
        if highlighted is not None and highlighted.id is not None:
            try:
                index = option_list.get_option_index(highlighted.id)
            except OptionDoesNotExist:
                index = 0
        option_list.highlighted = index
        self._show_description(option_list.get_option_at_index(index))

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        self._show_description(event.option)

    def _show_description(self, option: Option) -> None:
        # Literal: a landing description carries a language name from the config.
        self.query_one(MenuLegend).update(literal(option.description))
