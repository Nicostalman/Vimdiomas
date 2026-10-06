from pathlib import Path

from rich.cells import cell_len
from rich.text import Text

from textual import events, on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Input, OptionList, Static
from textual.widgets.option_list import Option

from vimdiomas.languages import LanguageKind
from vimdiomas.pinyin import to_tone_marks
from vimdiomas.platform import open_file
from vimdiomas.store import ContentHit, ContentIndex, fuzzy, search_content, tag_index
from vimdiomas.tui.screens.base import FooterHint, VimOptionList, literal, open_source_pdf
from vimdiomas.tui.screens.panels import Backpanel, Panel, PanelScreen, TextField

EMPTY_MESSAGE = "No matches."
CONTENT_HINT = "Type to search entries and categories."

MODE_LABEL_FILENAME = "FILENAME MODE"
MODE_LABEL_CONTENT = "CONTENT MODE"

FOOTER_HINT_FILENAME = (
    "Tab: search by content · Enter: next field / open PDF"
    " · Esc then J/K: move between panels"
)
FOOTER_HINT_CONTENT = (
    "Tab: search by filename · Enter: next field / open PDF"
    " · Esc then J/K: move between panels"
)

PLACEHOLDER_FILENAME = "Filter by filename"
PLACEHOLDER_CONTENT = "Search entries and categories"

# A field cut for space never goes below one cell of real content plus the
# trailing "…" (M3, requirements.md §3.5).
MIN_FIELD_WIDTH = 2

MINIMUM_RESULTS_WIDTH = 8


def list_pdfs(tree_root: Path) -> list[Path]:
    """Every .pdf under tree_root, as paths relative to it."""
    return sorted(path.relative_to(tree_root) for path in tree_root.rglob("*.pdf"))


def paths_with_tag(tree_root: Path, tag: str, *, kind: LanguageKind) -> set[Path]:
    """Tree-relative .pdf paths whose source .md carries `tag`."""
    cache = tag_index(tree_root, kind=kind)
    tagged_source_paths = cache.files_for(tag)
    return {
        path.relative_to(tree_root).with_suffix(".pdf") for path in tagged_source_paths
    }


def open_pdf(path: Path) -> None:
    open_file(path)


# -- M3 · Content mode: row fields and location ------------------------------


def hit_fields(hit: ContentHit, kind: LanguageKind) -> list[str]:
    """The field strings `format_row` lays out for `hit` (requirements.md
    §3.5): a category/subtitle is its bare name; an entry is its word,
    reading (tone-marked, Chinese kinds only) and translation, with any
    empty one dropped."""
    if hit.kind in ("category", "subtitle"):
        return [hit.name]
    if kind.has_reading:
        fields = [hit.word, to_tone_marks(hit.reading), hit.translation]
    else:
        fields = [hit.word, hit.translation]
    return [field for field in fields if field]


def hit_style(hit: ContentHit) -> str:
    """The style `format_row` gives `hit`'s fields: a category or subtitle
    name is bold, which is what sets it apart from an entry (requirements.md
    §3.5). An entry has none."""
    return "bold" if hit.kind in ("category", "subtitle") else ""


def hit_location(hit: ContentHit) -> str:
    """`hit`'s location string: the file, then its category and subtitle as
    far as they apply, joined by ` › ` (requirements.md §3.5). A hit that
    *is* a category or subtitle row never repeats its own name here."""
    parts = [hit.file_label]
    if hit.category:
        parts.append(hit.category)
    if hit.subtitle:
        parts.append(hit.subtitle)
    return " › ".join(parts)


def _truncate_to_width(text: str, max_width: int) -> str:
    """The longest prefix of `text` whose cell width is at most `max_width`."""
    if max_width <= 0:
        return ""
    kept = []
    total = 0
    for ch in text:
        width = cell_len(ch)
        if total + width > max_width:
            break
        kept.append(ch)
        total += width
    return "".join(kept)


def _truncate_from_left(text: str, max_width: int) -> str:
    """`text` cut from the left with a leading "…", keeping its rightmost
    (deepest) part, so its cell width is at most `max_width`."""
    if cell_len(text) <= max_width:
        return text
    if max_width <= 0:
        return ""
    if max_width == 1:
        return "…"
    kept = []
    total = 0
    for ch in reversed(text):
        width = cell_len(ch)
        if total + width > max_width - 1:
            break
        kept.append(ch)
        total += width
    return "…" + "".join(reversed(kept))


def _shrink_widths(natural: list[int], budget: int, minimum: int) -> list[int]:
    """`natural` cell widths shrunk to fit within `budget`, by repeatedly
    capping the longest one — so short fields stay whole and the longest is
    always the first to give something up. A field's own natural width is
    its floor when that is already below `minimum`."""
    widths = list(natural)
    floors = [min(minimum, width) for width in natural]
    while sum(widths) > budget:
        shrinkable = [i for i in range(len(widths)) if widths[i] > floors[i]]
        if not shrinkable:
            break
        tallest = max(widths[i] for i in shrinkable)
        index = next(i for i in shrinkable if widths[i] == tallest)
        widths[index] -= 1
    return widths


def format_row(fields: list[str], location: str, width: int, *, style: str = "") -> Text:
    """One result row (requirements.md §3.5): `fields` joined by two spaces,
    in `style` if given, then `location` dim, separated by at least two
    spaces and aligned to the right edge of `width` cells.

    When the whole row doesn't fit: the fields are cut first, longest
    first, down to one cell plus "…" each; if that's still too wide, the
    location itself is cut from the left. A final hard clamp guarantees the
    result never exceeds `width` cells, whatever `width` is.
    """
    fields = [field for field in fields if field]
    sep = "  "
    num_seps = max(len(fields) - 1, 0)

    natural_widths = [cell_len(field) for field in fields]
    location_width = cell_len(location)
    min_gap = 2

    fields_natural = sum(natural_widths) + num_seps * len(sep)
    if fields_natural + min_gap + location_width <= width:
        left = sep.join(fields)
        pad = width - cell_len(left) - location_width
        return _assemble(left, " " * pad, location, style)

    return _format_cut_row(
        fields, natural_widths, location, location_width, width, sep, num_seps, min_gap, style
    )


def _format_cut_row(
    fields: list[str],
    natural_widths: list[int],
    location: str,
    location_width: int,
    width: int,
    sep: str,
    num_seps: int,
    min_gap: int,
    style: str,
) -> Text:
    budget_for_fields = width - min_gap - location_width - num_seps * len(sep)
    floor_sum = sum(min(MIN_FIELD_WIDTH, w) for w in natural_widths)

    if budget_for_fields >= floor_sum:
        shrunk_widths = _shrink_widths(natural_widths, max(budget_for_fields, 0), MIN_FIELD_WIDTH)
        field_texts = [
            text if shrunk == natural else _truncate_to_width(text, max(shrunk - 1, 0)) + "…"
            for text, natural, shrunk in zip(fields, natural_widths, shrunk_widths)
        ]
        left = sep.join(field_texts)
        pad = max(width - cell_len(left) - location_width, min_gap)
        result = _assemble(left, " " * pad, location, style)
    else:
        field_texts = [
            text if cell_len(text) <= MIN_FIELD_WIDTH
            else _truncate_to_width(text, MIN_FIELD_WIDTH - 1) + "…"
            for text in fields
        ]
        left = sep.join(field_texts)
        remaining = width - cell_len(left) - min_gap
        cut_location = _truncate_from_left(location, max(remaining, 0))
        result = _assemble(left, " " * min_gap, cut_location, style)

    if cell_len(str(result)) > width:
        result = _hard_clamp(result, width)
    return result


def _assemble(left: str, gap: str, location: str, style: str) -> Text:
    return Text.assemble((left, style), gap, (location, "dim"))


def _hard_clamp(text: Text, width: int) -> Text:
    """The absolute safety net behind `format_row`'s "never exceeds width"
    guarantee: a cell-width truncation of the whole assembled row, for
    whatever extreme case the cutting rules above didn't anticipate. It
    keeps the row's styles."""
    clamped = text.copy()
    clamped.truncate(width)
    return clamped


class BrowseScreen(PanelScreen):
    BINDINGS = [
        Binding("tab", "toggle_mode", "Toggle mode", show=False),
    ]

    def __init__(self, tree_root: Path, *, kind: LanguageKind) -> None:
        super().__init__()
        self.tree_root = tree_root
        self.kind = kind
        self.mode: str = "filename"
        self._content_index = ContentIndex()
        self._content_hits: list[ContentHit] = []

    def compose(self) -> ComposeResult:
        with Backpanel():
            with Panel(id="query-panel"):
                yield TextField(placeholder=PLACEHOLDER_FILENAME, id="query")
            with Panel(id="results-panel"):
                yield Static(MODE_LABEL_FILENAME, id="mode-badge", classes="mode-filename")
                yield VimOptionList(id="results")
                yield Static(EMPTY_MESSAGE, id="empty-state")
                yield FooterHint(FOOTER_HINT_FILENAME, id="footer-hint")
            with Panel(id="tag-panel"):
                yield TextField(placeholder="Filter by tag", id="tag-filter")

    def on_mount(self) -> None:
        super().on_mount()
        self._refresh_results()

    def on_resize(self, event: events.Resize) -> None:
        self._refresh_results()

    def action_toggle_mode(self) -> None:
        focused = self.focused
        focused_id = focused.id if focused is not None else None
        if focused_id not in ("query", "tag-filter", "results"):
            return
        self.mode = "content" if self.mode == "filename" else "filename"
        self._apply_mode()
        if focused_id == "results":
            results = self.query_one("#results", OptionList)
            if results.option_count == 0:
                self.query_one("#query", TextField).focus()

    def _apply_mode(self) -> None:
        is_filename = self.mode == "filename"
        query = self.query_one("#query", TextField)
        query.placeholder = PLACEHOLDER_FILENAME if is_filename else PLACEHOLDER_CONTENT

        badge = self.query_one("#mode-badge", Static)
        badge.set_class(is_filename, "mode-filename")
        badge.set_class(not is_filename, "mode-content")
        badge.update(MODE_LABEL_FILENAME if is_filename else MODE_LABEL_CONTENT)

        self.query_one("#footer-hint", FooterHint).update(
            FOOTER_HINT_FILENAME if is_filename else FOOTER_HINT_CONTENT
        )
        self._refresh_results()

    @on(Input.Submitted, "#query")
    def _on_query_submitted(self, event: Input.Submitted) -> None:
        results = self.query_one("#results", OptionList)
        if results.option_count:
            results.focus()
        else:
            self.query_one("#tag-filter", TextField).focus()

    @on(Input.Changed, "#query")
    @on(Input.Changed, "#tag-filter")
    def _on_filter_changed(self, event: Input.Changed) -> None:
        self._refresh_results()

    def _refresh_results(self) -> None:
        if self.mode == "filename":
            self._refresh_filename_results()
        else:
            self._refresh_content_results()

    def _set_empty_state(self, show: bool, message: str) -> None:
        empty = self.query_one("#empty-state", Static)
        empty.display = show
        if show:
            empty.update(message)

    def _refresh_filename_results(self) -> None:
        candidates = [str(path) for path in list_pdfs(self.tree_root)]

        query = self.query_one("#query", Input).value
        if query:
            candidates = fuzzy(query, candidates)

        tag_query = self.query_one("#tag-filter", Input).value
        if tag_query:
            tagged = {str(path) for path in paths_with_tag(self.tree_root, tag_query, kind=self.kind)}
            candidates = [c for c in candidates if c in tagged]

        results = self.query_one("#results", OptionList)
        results.clear_options()
        if candidates:
            results.add_options(Option(literal(c), id=c) for c in candidates)
            # `add_options` doesn't auto-highlight the first option the way
            # passing options to the constructor does (see `OptionList.__init__`,
            # which calls this same `action_first` only when built with
            # initial content) — the menus get it for free since their
            # options are passed to the constructor; results are added after
            # the fact on every filter change, so it's done explicitly here.
            results.action_first()

        self._set_empty_state(not candidates, EMPTY_MESSAGE)
        results.display = bool(candidates)

    def _refresh_content_results(self) -> None:
        query = self.query_one("#query", Input).value
        results = self.query_one("#results", OptionList)

        if not query.strip():
            self._content_hits = []
            results.clear_options()
            results.display = False
            self._set_empty_state(True, CONTENT_HINT)
            return

        self._content_index.refresh(self.tree_root, kind=self.kind)

        tag_query = self.query_one("#tag-filter", Input).value
        tagged = tag_index(self.tree_root, kind=self.kind).files_for(tag_query) if tag_query else None

        hits = search_content(
            self._content_index, query, tree_root=self.tree_root, kind=self.kind, tagged=tagged
        )
        self._content_hits = hits

        results.clear_options()
        if hits:
            width = self._results_content_width()
            for index, hit in enumerate(hits):
                row = format_row(
                    hit_fields(hit, self.kind), hit_location(hit), width, style=hit_style(hit)
                )
                results.add_option(Option(row, id=str(index)))
            results.action_first()

        self._set_empty_state(not hits, EMPTY_MESSAGE)
        results.display = bool(hits)

    def _results_content_width(self) -> int:
        # `#results-panel`'s own content size, not `#results`'s: the list is
        # only ever displayed once there are hits, so right when it first
        # becomes visible its own size can still be the stale pre-layout
        # one (0x0) — the panel around it is visible from the start.
        width = self.query_one("#results-panel", Panel).content_size.width
        return max(width, MINIMUM_RESULTS_WIDTH)

    @on(OptionList.OptionSelected, "#results")
    def _on_result_selected(self, event: OptionList.OptionSelected) -> None:
        if self.mode == "filename":
            open_pdf(self.tree_root / event.option_id)
            return
        hit = self._content_hits[int(event.option_id)]
        open_source_pdf(self.app, hit.source, tree_root=self.tree_root, kind=self.kind)
