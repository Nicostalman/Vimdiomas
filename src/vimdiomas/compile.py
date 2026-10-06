"""Render decks to PDF: intermediate markdown -> pandoc -> xelatex."""

import hashlib
import importlib.resources
import json
import re
import string
import subprocess
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path

from vimdiomas.languages import LanguageKind
from vimdiomas.models import Category, Deck, Entry, Warning
from vimdiomas.parser import parse
from vimdiomas.pinyin import is_hanzi, to_tone_mark_syllables, to_tone_marks
from vimdiomas.store import is_grammar

# Staleness cache for compile_all: maps each source .md's absolute path to a
# stamp of what the renderer produced for it last time (see _stamp_for).
# Missing or corrupt is treated as empty rather than an error, which is what
# makes deleting this file always safe.
CACHE_PATH = Path.home() / ".cache" / "vimdiomas" / "compile_cache.json"

# How much of a failed compile's stderr is kept for the user (Sprint 6 M2,
# #12). xelatex's useful part — the `! ...` error and the line it points at —
# is at the end; the whole log is hundreds of lines.
STDERR_TAIL_LINES = 10

# Extra space after a grammar entry's pinyin (before its translation) and
# after its last line (before the next entry's hanzi), M6 — passed as \\[...]
# line-break arguments, not standalone \vspace lines, whose trailing source
# newline would leave a space indenting the next line — except after a block's
# last entry, which ends the paragraph and so takes a plain \vspace.
GRAMMAR_PINYIN_GAP = "0.4em"
GRAMMAR_ENTRY_GAP = "1.8em"

# A vocabulary row that would not fit the table's aligned columns is an
# *exception* (Sprint 6 M6, every kind): set across the full text width and
# wrapped, with its continuation lines indented. The aligned first column is
# as wide as its longest word, so one long German compound would otherwise push
# every translation to the right, and a row too long for the page would run
# past the margin. Widths are estimated, in em of the 12pt body, because the
# table is sized by LaTeX and the decision has to be made here. First-pass
# values, tuned by eye like the gaps above.
TEXT_WIDTH_EM = 39  # 6.5in at 12pt
TABLE_PADDING_EM = 1  # \tabcolsep either side of the table
COLUMN_GAP_EM = 2  # the `@{\hspace{2em}}` between columns
WORD_CAP_EM = 12  # ten hanzi, or twenty Latin letters, in \Large
LARGE_SCALE = 1.2  # \Large against the body size
WIDE_CHAR_EM = 1.0  # East Asian wide and fullwidth characters
NARROW_CHAR_EM = 0.5  # everything else, a little generous
LONG_ROW_INDENT = "1.5em"

_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


_LATEX_SPECIAL_RE = re.compile("[" + re.escape("".join(_LATEX_ESCAPES)) + "]")


def _escape(cell: str) -> str:
    """Entry text to raw LaTeX, in one pass (Sprint 6 M3, #10): a
    replacement is never fed back through a later one, so `a\\b` is
    `a\\textbackslash{}b` and not `a\\textbackslash\\{\\}b`."""
    return _LATEX_SPECIAL_RE.sub(lambda match: _LATEX_ESCAPES[match.group()], cell)


# What a straight `"` may follow and still open a quote, besides whitespace
# and the start of the field.
_OPENS_A_QUOTE_AFTER = "([{<-–—/"


def _curl_quotes(text: str) -> str:
    """A straight `"` in entry text to a curly one (Sprint 7 M2): `“` at the
    start of the field or after whitespace or an opening bracket or dash,
    `”` anywhere else. Entry text is raw LaTeX, where TeX turns every `"`
    into `”`, so an opening quote came out closed.

    The exception is Chinese, typed with no space before a quote: right after
    a hanzi, with no quote open and something other than a space after it,
    `"` opens (`他说"你好"`). A typed `“` or `”` and every other character are
    left as they are."""
    out = []
    is_open = False
    for index, ch in enumerate(text):
        if ch == '"':
            before = text[index - 1] if index else " "
            after = text[index + 1] if index + 1 < len(text) else " "
            opens = (
                before.isspace()
                or before in _OPENS_A_QUOTE_AFTER
                or (not is_open and is_hanzi(before) and not after.isspace())
            )
            ch = "“" if opens else "”"
        if ch in "“”":
            is_open = ch == "“"
        out.append(ch)
    return "".join(out)


def _curl_entry(entry: Entry) -> Entry:
    """The entry with its prose fields curled, each whole and before it is
    escaped or split into units. The reading is pinyin and is left alone."""
    note = _curl_quotes(entry.note) if entry.note else entry.note
    return replace(
        entry, word=_curl_quotes(entry.word), translation=_curl_quotes(entry.translation), note=note
    )


# What a heading or the title leaves unescaped: the characters pandoc's
# `smart` extension turns into typography (’ “” – — …), which are never
# markup there. Escaping them would print `Don't` with a typewriter quote.
_MARKDOWN_SMART = "'\"-."
_MARKDOWN_SPECIAL_RE = re.compile(
    "[" + re.escape("".join(c for c in string.punctuation if c not in _MARKDOWN_SMART)) + "]"
)


def _escape_markdown(text: str) -> str:
    """A name the user chose, to literal markdown text (Sprint 6 M3, #13):
    backslash before every ASCII punctuation character pandoc could read as
    markup — `{#id}`, a trailing `#`, `*`, `_`, `$`, `\\`. A backslash before
    ASCII punctuation is always a literal escape in pandoc's markdown, so the
    whole class is safe without judging which characters are markup."""
    return _MARKDOWN_SPECIAL_RE.sub(lambda match: "\\" + match.group(), text)


_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")

# A title YAML and markdown both read as itself, emitted unquoted so that
# ordinary files' intermediate markdown — and so their stamps — are what they
# were before #5's fix: letters and single spaces, and not a YAML keyword.
_PLAIN_TITLE_RE = re.compile(r"[^\W\d_]+(?: [^\W\d_]+)*")
_YAML_KEYWORDS = {"true", "false", "null", "yes", "no", "on", "off", "y", "n"}


def _yaml_title(title: str) -> str:
    """The deck title as a YAML scalar (Sprint 6 M3, #5), so `Food: fruit`
    and `Food # drink` are a title and not a mapping or a comment.

    Anything but a plain title is double-quoted, markdown-escaped *first*:
    pandoc reads the unquoted value as markdown, and the backslashes that
    step adds must then themselves be escaped for YAML — `\\:` is not a
    legal YAML escape. Reversing the two steps produces YAML pandoc
    rejects."""
    if _PLAIN_TITLE_RE.fullmatch(title) and title.lower() not in _YAML_KEYWORDS:
        return title
    text = _CONTROL_RE.sub("", _escape_markdown(title))
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _pair_hanzi_pinyin(
    hanzi: str, pinyin: str, *, unsupported: list[str] | None = None
) -> list[tuple[str, str]]:
    """Pair each character of `hanzi` with its pinyin syllable, in order: a
    non-hanzi character (or one reached after the syllables run out) pairs
    with `""` (M6) — the rule behind `...` getting no pinyin underneath."""
    syllables = iter(to_tone_mark_syllables(pinyin, unsupported=unsupported))
    pairs = []
    for ch in hanzi:
        syllable = next(syllables, "") if is_hanzi(ch) else ""
        pairs.append((ch, syllable))
    return pairs


def _width_em(text: str) -> float:
    """What `text` is estimated to measure at body size, in em."""
    return sum(
        WIDE_CHAR_EM if unicodedata.east_asian_width(char) in "WF" else NARROW_CHAR_EM
        for char in text
    )


def _exception_rows(widths: list[list[float]]) -> set[int]:
    """The rows, by index, to set apart from the table's aligned columns.

    `widths` is each row's cell widths in em, word first, as printed. A row is
    an exception when its word alone is wider than `WORD_CAP_EM`, which would
    drag every other row's second column along; and then, for as long as the
    aligned rows make a table wider than the text, the row whose removal
    narrows it most is made one too, so a table that fits keeps every row.
    Only the row holding a column's widest cell can narrow the table, so only
    those are tried.
    """
    if not widths:
        return set()
    columns = len(widths[0])
    available = TEXT_WIDTH_EM - TABLE_PADDING_EM - COLUMN_GAP_EM * (columns - 1)
    exceptions = {index for index, row in enumerate(widths) if row[0] > WORD_CAP_EM}

    def table_width(skipping: set[int]) -> float:
        return sum(
            max((row[c] for index, row in enumerate(widths) if index not in skipping), default=0)
            for c in range(columns)
        )

    while table_width(exceptions) > available:
        remaining = [index for index in range(len(widths)) if index not in exceptions]
        if not remaining:
            break
        widest = {max(remaining, key=lambda index: widths[index][c]) for c in range(columns)}
        exceptions.add(
            min(widest, key=lambda index: (table_width(exceptions | {index}), -sum(widths[index])))
        )
    return exceptions


def _render_table(
    entries: list[Entry], kind: LanguageKind, unsupported: list[str] | None = None
) -> list[str]:
    """Render entries as a raw-LaTeX list: left-aligned, tight to content, no
    visible header or rules. The table is passed through pandoc untouched via
    the `raw_attribute` extension, since matching this look through pandoc's
    own markdown-table-to-longtable conversion isn't reliably controllable.

    A kind with a reading has three columns (word, reading, translation), one
    without has two: the same table minus the reading column (Sprint 6 M6).
    A row too long for them (`_exception_rows`) is one cell across every
    column instead, wrapping with a hanging indent."""
    columns = 3 if kind.has_reading else 2
    column_spec = r"@{\hspace{2em}}".join("l" * columns)
    lines = ["```{=latex}", rf"\begin{{longtable}}{{{column_spec}}}"]

    rows = []  # per entry: the cells as LaTeX, and as text for measuring
    for entry in map(_curl_entry, entries):
        translation_text = entry.translation + (f" ({entry.note})" if entry.note else "")
        translation = _escape(entry.translation)
        if entry.note:
            translation = f"{translation} \\textit{{({_escape(entry.note)})}}"
        texts = [entry.word]
        cells = [f"{{\\Large {_escape(entry.word)}}}"]
        if kind.has_reading:
            reading = to_tone_marks(entry.reading, unsupported=unsupported)
            texts.append(reading)
            cells.append(_escape(reading))
        texts.append(translation_text)
        cells.append(translation)
        rows.append((cells, texts))

    widths = [
        [_width_em(texts[0]) * LARGE_SCALE] + [_width_em(text) for text in texts[1:]]
        for _, texts in rows
    ]
    exceptions = _exception_rows(widths)

    for index, (cells, texts) in enumerate(rows):
        if index in exceptions:
            # `\tabcolsep` on both sides of the cell, as an ordinary row's
            # cells have, so the text starts where the other rows' words do
            # and ends at the right margin. An empty cell (a reading `...`
            # has none) adds no gap.
            body = r"\hspace{2em}".join(
                cell for cell, text in zip(cells, texts) if text != ""
            )
            lines.append(
                rf"\multicolumn{{{columns}}}{{p{{\dimexpr\linewidth-2\tabcolsep\relax}}}}"
                rf"{{\raggedright\hangindent={LONG_ROW_INDENT}\hangafter=1 {body}}} \\"
            )
        else:
            lines.append(" & ".join(cells) + " \\\\")
    lines.append(r"\end{longtable}")
    lines.append("```")
    return lines


def _render_grammar_table(
    entries: list[Entry], kind: LanguageKind, unsupported: list[str] | None = None
) -> list[str]:
    """Render entries as stacked hanzi/pinyin/translation(/note) units (M6):
    a run of `\\HanziPinyin` calls, then the translation, then the note on
    its own line if any — a small gap after the pinyin, a large one after
    the entry's last line. A kind with no reading has nothing to stack, so
    its head line is the word alone, through `\\GrammarWord`; the gap after
    it plays the pinyin's role (Sprint 6 M6).

    Unlike `_render_table`'s `longtable` (immune to paragraph indentation),
    this whole block is one LaTeX paragraph (line breaks via `\\\\`, no blank
    lines between entries) — an ordinary raw paragraph gets `\\parindent` on
    its first line, so `\\noindent` is explicit here rather than relying on
    the heading that (usually, but not always — e.g. `deck.uncategorized`)
    precedes it to suppress it."""
    lines = ["```{=latex}", r"\noindent%"]
    for entry in map(_curl_entry, entries):
        if kind.has_reading:
            pairs = _pair_hanzi_pinyin(entry.word, entry.reading, unsupported=unsupported)
            hanzi_line = "".join(
                f"\\HanziPinyin{{{_escape(hanzi)}}}{{{_escape(syllable)}}}"
                for hanzi, syllable in pairs
            )
        else:
            hanzi_line = f"\\GrammarWord{{{_escape(entry.word)}}}"
        entry_lines = [_escape(entry.translation)]
        if entry.note:
            entry_lines.append(f"\\textit{{({_escape(entry.note)})}}")
        lines.append(f"{hanzi_line} \\\\[{GRAMMAR_PINYIN_GAP}]")
        lines.extend(f"{line} \\\\" for line in entry_lines[:-1])
        lines.append(f"{entry_lines[-1]} \\\\[{GRAMMAR_ENTRY_GAP}]")
    # A line break right before the paragraph ends would add an empty line on
    # top of the gap, so the block's last entry ends the paragraph instead —
    # the gap before a following heading then matches the gap between entries.
    lines[-1] = f"{entry_lines[-1]}\\par\\vspace{{{GRAMMAR_ENTRY_GAP}}}"
    lines.append("```")
    return lines


def render_markdown(
    deck: Deck,
    *,
    kind: LanguageKind,
    grammar: bool = False,
    unsupported: list[str] | None = None,
) -> str:
    """Render a Deck to intermediate markdown. Vocabulary decks (`grammar=
    False`) get tone-marked pinyin in 3-column tables. Grammar decks
    (`grammar=True`, M6) get stacked hanzi/pinyin/translation triads instead.
    A category's subtitles (Sprint 5 M5, grammar files only — a vocabulary
    deck never has any) each render as a `### ` heading below the category's
    own entries, with their own table if they have entries; an empty
    subtitle is a bare heading, same as an empty category.

    Headings and the title are markdown-escaped, entry text LaTeX-escaped
    (Sprint 6 M3): a heading stays markdown so its level remains pandoc's
    and the template's decision. A pinyin syllable with nothing to carry
    its tone is appended to `unsupported`, when given (#4).

    `kind` (Sprint 6 M5) is required, with no default. A kind with a reading
    gets the tables above; one without gets the same layouts minus the
    pinyin (M6)."""
    render_group = _render_grammar_table if grammar else _render_table

    def render_entries(entries: list[Entry]) -> list[str]:
        return render_group(entries, kind, unsupported)

    lines = ["---", f"title: {_yaml_title(deck.title)}", "---", ""]

    if deck.uncategorized:
        lines.extend(render_entries(deck.uncategorized))
        lines.append("")

    for category in deck.categories:
        lines.append(f"## {_escape_markdown(category.name)}")
        lines.append("")
        if category.entries:
            lines.extend(render_entries(category.entries))
            lines.append("")
        for subtitle in category.subtitles:
            lines.append(f"### {_escape_markdown(subtitle.name)}")
            lines.append("")
            if subtitle.entries:
                lines.extend(render_entries(subtitle.entries))
                lines.append("")

    return "\n".join(lines)


@dataclass
class Render:
    """What the renderer produces for one source file: the intermediate
    markdown, its staleness stamp, and any pinyin syllables it could not
    tone-mark (Sprint 6 M3)."""

    markdown: str
    stamp: str
    unsupported: list[str]
    # What the file holds that the app would not have written (Sprint 6 M9).
    # Reported on every Compile, and never a reason not to compile.
    warnings: list[Warning] = field(default_factory=list)


def render_source(source_path: Path, *, kind: LanguageKind, grammar: bool = False) -> Render:
    """Parse and render one source file, and stamp the result. Computed once
    per file per run: `compile_all` needs it for the skip decision and hands
    it on to `compile_file` rather than rendering twice."""
    deck, warnings = parse(
        source_path.read_text(encoding="utf-8"), source_path.stem, kind=kind, grammar=grammar
    )
    unsupported: list[str] = []
    markdown = render_markdown(deck, kind=kind, grammar=grammar, unsupported=unsupported)
    return Render(
        markdown, _stamp_for(markdown, _template_bytes(), kind), unsupported, warnings
    )


def _run_pandoc(markdown: str, notebook_path: Path, kind: LanguageKind) -> None:
    notebook_path.parent.mkdir(parents=True, exist_ok=True)
    template_ref = importlib.resources.files("vimdiomas") / "templates" / "xecjk.tex"
    with importlib.resources.as_file(template_ref) as template_path:
        subprocess.run(
            [
                "pandoc",
                "-f",
                "markdown+raw_attribute",
                "-t",
                "pdf",
                "--pdf-engine=xelatex",
                f"--template={template_path}",
                "--shift-heading-level-by=-1",
                *(["-V", f"cjkfont={kind.cjk_font}"] if kind.cjk_font else []),
                "-o",
                str(notebook_path),
            ],
            input=markdown.encode("utf-8"),
            check=True,
            capture_output=True,
        )


def compile_file(
    source_path: Path,
    notebook_path: Path,
    *,
    kind: LanguageKind,
    grammar: bool = False,
    cache: dict[str, str] | None = None,
    render: Render | None = None,
) -> None:
    """Compile a single source .md file to a PDF at notebook_path, and record
    in the staleness cache what it rendered.

    `grammar=True` (Sprint 5 M5) parses `###` lines as subtitles; every
    caller that knows the file's path decides this via `store.is_grammar`.

    Recording lives here, not in `compile_all` (Sprint 6 M3, #11): this is
    the one function that produces a PDF, so no path can write one without
    its stamp. Given a `cache` (by `compile_all`, which saves once per run)
    the stamp goes into that dict; given none (autocompile, Inspect Tree),
    the cache file is loaded, updated and saved here. A failed compile
    raises before recording anything, so the next run retries it.
    """
    if render is None:
        render = render_source(source_path, kind=kind, grammar=grammar)
    _run_pandoc(render.markdown, notebook_path, kind)
    if cache is not None:
        cache[str(source_path)] = render.stamp
    else:
        own_cache = _load_cache()
        own_cache[str(source_path)] = render.stamp
        _save_cache(own_cache)


def notebook_path_for(source_path: Path) -> Path:
    """Map a .md path to its .pdf path: same tree, suffix swap only."""
    return source_path.with_suffix(".pdf")


def _load_cache() -> dict[str, str]:
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache), encoding="utf-8")


def forget_tree(tree_root: Path) -> None:
    """Drop the staleness-cache entries of every source under `tree_root`.

    Called once a language's folder has been deleted (Sprint 6 M8): the cache
    is keyed by absolute source path, so those entries would never match
    again. Saves only if something was dropped. Keys compare as path
    components, so `tree-Chinese2` is not under `tree-Chinese`.
    """
    cache = _load_cache()
    kept = {
        key: stamp
        for key, stamp in cache.items()
        if tree_root not in Path(key).parents
    }
    if kept != cache:
        _save_cache(kept)


def _template_bytes() -> bytes:
    template_ref = importlib.resources.files("vimdiomas") / "templates" / "xecjk.tex"
    return template_ref.read_bytes()


def _stamp_for(markdown: str, template_bytes: bytes, kind: LanguageKind) -> str:
    """Hash what the renderer would actually produce for a file: the
    intermediate markdown, the template's own bytes, and the kind's CJK font
    name (also passed to the template, but not part of its bytes; empty for a
    kind with none). This is what makes a template edit or a font change
    (M3, M6) count as a renderer change, not just a Python one."""
    return hashlib.sha256(
        markdown.encode("utf-8") + template_bytes + (kind.cjk_font or "").encode("utf-8")
    ).hexdigest()


@dataclass
class CompileFailure:
    """One file that did not compile, and why, in a form a user can read."""

    source: Path
    message: str


@dataclass
class CompileWarning:
    """Something in a file the renderer printed as best it could, rather
    than as written (Sprint 6 M3, #4): today, only pinyin with no letter to
    carry its tone. The file still compiles."""

    source: Path
    message: str


@dataclass
class CompileReport:
    """What a `compile_all` run did (Sprint 6 M2, #12): the PDFs it wrote and
    the sources it could not compile. A failure is per file — it never stops
    the rest of the run. `warnings` (M3) covers every file in the tree,
    rebuilt or not: they describe the source, not the run."""

    compiled: list[Path] = field(default_factory=list)
    failed: list[CompileFailure] = field(default_factory=list)
    warnings: list[CompileWarning] = field(default_factory=list)


def failure_message(exc: BaseException) -> str:
    """The last `STDERR_TAIL_LINES` non-empty lines of a failed subprocess's
    stderr, or the exception itself when there is none (pandoc not found)."""
    stderr = getattr(exc, "stderr", None)
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if stderr:
        lines = [line for line in stderr.splitlines() if line.strip()]
        if lines:
            return "\n".join(lines[-STDERR_TAIL_LINES:])
    return str(exc)


def unsupported_message(syllables: list[str]) -> str:
    return "printed without a tone mark: " + ", ".join(dict.fromkeys(syllables))


def parse_warning_message(warning: Warning) -> str:
    """One parse warning for the Compile report and the CLI (Sprint 6 M9):
    `line N: message`, then the offending line indented beneath it, the shape
    Inspect Tree's preview uses.

    Two lines rather than one because a message can end in a colon of its own
    (`extra column(s) never rendered: junk`), and `…: junk: 你\tni3` is not
    readable. Both surfaces indent every line of a message. A file-level
    warning has no line to name and no line to quote.
    """
    if not warning.line_number:
        return warning.message
    return f"line {warning.line_number}: {warning.message}\n    {warning.raw_line}"


def compile_all(tree_root: Path, *, kind: LanguageKind, force: bool = False) -> CompileReport:
    """Compile every .md under tree_root to a sibling .pdf, skipping files
    whose rendered output (markdown + template) hasn't changed since last
    time. `force=True` recompiles everything regardless, and still updates
    the cache so the next ordinary run stays fast.

    A file that fails to compile is recorded in the report and the run goes
    on; its cache entry is left alone, so the next run retries it. The cache
    is saved however the loop ends, so a stamp earned before a failure — or
    before anything unanticipated — is kept.
    """
    cache = _load_cache()
    report = CompileReport()
    before = dict(cache)

    try:
        for source_path in sorted(tree_root.rglob("*.md")):
            notebook_path = notebook_path_for(source_path)
            grammar = is_grammar(source_path, tree_root)
            render = render_source(source_path, kind=kind, grammar=grammar)
            # Reported for every file, rebuilt or skipped (M3's rule): a
            # warning describes the source, not the run, so one shown only on
            # a rebuild would never be seen again (M9).
            for warning in render.warnings:
                report.warnings.append(
                    CompileWarning(source_path, parse_warning_message(warning))
                )
            if render.unsupported:
                report.warnings.append(
                    CompileWarning(source_path, unsupported_message(render.unsupported))
                )

            if not force and notebook_path.exists() and cache.get(str(source_path)) == render.stamp:
                continue

            try:
                compile_file(
                    source_path,
                    notebook_path,
                    kind=kind,
                    grammar=grammar,
                    cache=cache,
                    render=render,
                )
            except (subprocess.CalledProcessError, OSError) as exc:
                report.failed.append(CompileFailure(source_path, failure_message(exc)))
                continue
            report.compiled.append(notebook_path)
    finally:
        if cache != before:
            _save_cache(cache)

    return report
