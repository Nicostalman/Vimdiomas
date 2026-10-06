"""Discovery and search over a deck tree: walk(), tag_index(), fuzzy(),
search_content(), and what a name in it may be: validate_name()."""

import os
import re
import unicodedata
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from vimdiomas.languages import LanguageKind
from vimdiomas.models import Deck, Warning
from vimdiomas.parser import parse


@dataclass
class FileNode:
    path: Path
    categories: list[str] = field(default_factory=list)
    has_uncategorized: bool = False
    # Everything in the file the app would not have written (Sprint 6 M9).
    # Carried here rather than re-read per screen: both trees are built from
    # this shape and nothing else, so the file is parsed once per tree build,
    # as it always has been.
    warnings: list[Warning] = field(default_factory=list)


@dataclass
class DirNode:
    path: Path
    dirs: list["DirNode"] = field(default_factory=list)
    files: list[FileNode] = field(default_factory=list)


def _parse_file(path: Path, tree_root: Path, kind: LanguageKind) -> FileNode:
    """One file as a tree node, with the warnings its text earned.

    `grammar=` matters here, not only in the compiler (Sprint 6 M9): without
    it every `### ` subtitle line of every grammar file is an "unrecognized
    line", which was invisible only for as long as these warnings were
    discarded. It is also what makes `categories`/`has_uncategorized` right
    for a grammar file.

    A file that cannot be read or decoded is still a node, carrying one
    warning that says so — M1's rule that one bad file never locks the user
    out of the whole tree applies to an unreadable one as much as to a
    malformed row.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return FileNode(path=path, warnings=[Warning(0, f"could not be read: {exc}", "")])
    deck, warnings = parse(
        text, path.stem, kind=kind, grammar=is_grammar(path, tree_root)
    )
    return FileNode(
        path=path,
        categories=[category.name for category in deck.categories],
        has_uncategorized=bool(deck.uncategorized),
        warnings=warnings,
    )


def is_grammar(path: Path, tree_root: Path) -> bool:
    """Whether `path` is a grammar file (Sprint 5 M5): under `tree_root`,
    with a top-level directory named `Grammar` (any case) somewhere before
    it. A `Grammar/` folder nested deeper than the top level does not count,
    and a path outside `tree_root` is never grammar."""
    try:
        relative = path.relative_to(tree_root)
    except ValueError:
        return False
    parts = relative.parts
    return len(parts) >= 2 and parts[0].lower() == "grammar"


# The two folders every notebook's tree has: vocabulary files, and the grammar
# files `is_grammar` recognises by their top-level `Grammar/` folder.
TREE_FOLDERS = ("Vocabulary", "Grammar")


def ensure_tree(tree_root: Path) -> None:
    """Create `tree_root` and, inside it, the `Vocabulary/` and `Grammar/`
    folders that are missing (Sprint 6 M6). Never touches what exists.

    A folder counts as present in any case, as `is_grammar` matches `Grammar`
    in any case: on a case-sensitive filesystem, creating `Grammar/` beside the
    user's `grammar/` would split one notebook's grammar in two.
    """
    tree_root.mkdir(parents=True, exist_ok=True)
    present = {child.name.lower() for child in tree_root.iterdir() if child.is_dir()}
    for name in TREE_FOLDERS:
        if name.lower() not in present:
            (tree_root / name).mkdir()


def validate_name(name: str) -> str | None:
    """Why `name` can't be a file or directory name typed into the tree, or
    `None` if it can (Sprint 6 M2, #14).

    Refuses exactly what makes `parent / name` mean something other than "a
    child of parent": a separator, `.`/`..`, a control character (NUL raises
    inside `pathlib` rather than refusing cleanly), and edge whitespace, which
    is refused rather than trimmed so the file is always found under the name
    the user typed. Not shared with category names — see `design.md`'s *Names
    the app refuses*.
    """
    if not name.strip():
        return "A name can't be empty."
    if name != name.strip():
        return "A name can't start or end with a space."
    if name in (".", ".."):
        return f"{name} can't be a name."
    separators = {"/", "\\", os.sep} | ({os.altsep} if os.altsep else set())
    if any(separator in name for separator in separators):
        return "A name can't contain / or \\."
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in name):
        return "A name can't contain control characters."
    return None


def walk(root: Path, *, kind: LanguageKind) -> DirNode:
    """Build a directory -> file -> category tree rooted at `root`. `kind` is
    needed for a correct answer, not only for uniformity: `has_uncategorized`
    depends on which lines are entry rows.

    `root` is the notebook's tree root — both callers pass theirs — and is
    carried down the recursion so each file can be parsed as the grammar or
    vocabulary file it is (`is_grammar` answers that against the tree root,
    not against the directory being listed)."""
    return _walk(root, root, kind)


def _walk(root: Path, tree_root: Path, kind: LanguageKind) -> DirNode:
    node = DirNode(path=root)
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            node.dirs.append(_walk(entry, tree_root, kind))
        elif entry.suffix == ".md":
            node.files.append(_parse_file(entry, tree_root, kind))
    return node


def _iter_md_paths(root: Path) -> Iterator[Path]:
    """Every `.md` under `root`, in the same order `_walk` visits them:
    subdirectories recursed depth-first (sorted by name) before a
    directory's own files, so `Grammar/` comes before `Vocabulary/` the same
    way it does in the tree. Used by `search_content` (M3) to walk files
    without re-parsing them the way `walk` does — `ContentIndex` parses
    lazily, keyed by mtime, so this only has to name the files in order."""
    dirs: list[Path] = []
    files: list[Path] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.is_dir():
            dirs.append(entry)
        elif entry.suffix == ".md":
            files.append(entry)
    for child in dirs:
        yield from _iter_md_paths(child)
    yield from files


@dataclass
class TagCache:
    mtimes: dict[Path, float] = field(default_factory=dict)
    tags: dict[Path, list[str]] = field(default_factory=dict)

    def files_for(self, tag: str) -> set[Path]:
        return {path for path, file_tags in self.tags.items() if tag in file_tags}


def tag_index(root: Path, cache: TagCache | None = None, *, kind: LanguageKind) -> TagCache:
    """Map tags to the files carrying them, reusing `cache` for unchanged files.
    Tags do not depend on `kind`; it is taken so every `parse` call has one
    signature, and so the warnings Browse will surface (Sprint 6 M9) are not
    bogus ones for every row of an alphabetical file."""
    cache = cache or TagCache()
    new_mtimes: dict[Path, float] = {}
    new_tags: dict[Path, list[str]] = {}

    for path in root.rglob("*.md"):
        mtime = path.stat().st_mtime
        new_mtimes[path] = mtime
        if cache.mtimes.get(path) == mtime and path in cache.tags:
            new_tags[path] = cache.tags[path]
        else:
            deck, _ = parse(path.read_text(encoding="utf-8"), path.stem, kind=kind)
            new_tags[path] = deck.tags

    return TagCache(mtimes=new_mtimes, tags=new_tags)


_WORD_BOUNDARY_RE = re.compile(r"(?:^|[\s_-])(\w)")


def _word_start_positions(candidate: str) -> set[int]:
    return {m.start(1) for m in _WORD_BOUNDARY_RE.finditer(candidate)}


def _score(query: str, candidate: str) -> int | None:
    """Subsequence-match `query` in `candidate`; None if not a subsequence."""
    if not query:
        return 0

    lower_candidate = candidate.lower()
    lower_query = query.lower()
    word_starts = _word_start_positions(candidate)

    score = 0
    search_from = 0
    prev_matched_index = None
    for char in lower_query:
        index = lower_candidate.find(char, search_from)
        if index == -1:
            return None
        score += 1
        if prev_matched_index is not None:
            gap = index - prev_matched_index - 1
            score -= gap  # penalize skipped characters, rewarding tighter matches
            if gap == 0:
                score += 2  # extra bonus for a truly contiguous run
        if index in word_starts:
            score += 3  # word-start hit
        prev_matched_index = index
        search_from = index + 1

    return score


def fuzzy(query: str, candidates: list[str]) -> list[str]:
    """Rank `candidates` by subsequence match against `query`, best first."""
    scored = [(candidate, _score(query, candidate)) for candidate in candidates]
    matches = [(candidate, score) for candidate, score in scored if score is not None]
    matches.sort(key=lambda pair: pair[1], reverse=True)
    return [candidate for candidate, _ in matches]


# -- M3 · Search by content ---------------------------------------------


def fold(text: str) -> str:
    """`text` with case and accents normalised away, for substring matching
    (M3, `requirements.md` §3.2): NFKD, drop every combining mark (Unicode
    category `Mn`), `casefold()`, then NFC. `Über` -> `uber`, `nǐ` -> `ni`,
    `Straße` -> `strasse` (casefold's own special case for `ß`), hanzi and
    spaces pass through unchanged."""
    decomposed = unicodedata.normalize("NFKD", text)
    without_marks = "".join(
        ch for ch in decomposed if unicodedata.category(ch) != "Mn"
    )
    return unicodedata.normalize("NFC", without_marks.casefold())


_PINYIN_NOISE_RE = re.compile(r"[0-9\s:'’]")


def pinyin_key(text: str) -> str:
    """`text` as a key comparable regardless of tone marks, tone digits or
    `v`/`u:` spelling of ü (M3, `requirements.md` §3.2): `fold(text)` with
    ASCII digits, whitespace, `:`, `'` and `’` removed and `v` replaced by
    `u`. `ni3hao3` -> `nihao`, `nǐ hǎo` -> `nihao`, `lu:4`/`lv4` -> `lu`.
    Empty for a query with nothing but digits/punctuation (`3` -> ``), which
    is what keeps a bare `3` from matching every reading."""
    stripped = _PINYIN_NOISE_RE.sub("", fold(text))
    return stripped.replace("v", "u")


HitKind = Literal["entry", "category", "subtitle"]


@dataclass
class ContentHit:
    """One line `search_content` found: an entry (its three raw fields) or
    a category/subtitle (just its `name`). `source` is the file's absolute
    path; `file_label` is that path relative to the tree root, without
    `.md`. `category`/`subtitle` name the hit's ancestry as far as it has
    one, for `requirements.md` §3.5's location string — never the hit's own
    name when the hit *is* a category or subtitle row."""

    kind: HitKind
    source: Path
    file_label: str
    category: str | None = None
    subtitle: str | None = None
    word: str = ""
    reading: str = ""
    translation: str = ""
    name: str = ""


@dataclass
class ContentIndex:
    """`path -> (mtime, Deck)` for every `.md` under a tree root, parsed
    lazily and re-parsed only when a file's mtime changes (M3, like
    `TagCache`). One instance lives on `BrowseScreen`; nothing is persisted.
    """

    entries: dict[Path, tuple[float, Deck]] = field(default_factory=dict)

    def refresh(self, tree_root: Path, *, kind: LanguageKind) -> None:
        """Rebuild `entries` in tree order (`_iter_md_paths`), reusing
        whatever is already cached and still current. A file that is gone
        is dropped by simply not being carried into the rebuilt dict; one
        that can't be read or decoded contributes nothing and raises
        nothing, the same rule `_parse_file` follows."""
        rebuilt: dict[Path, tuple[float, Deck]] = {}
        for path in _iter_md_paths(tree_root):
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            cached = self.entries.get(path)
            if cached is not None and cached[0] == mtime:
                rebuilt[path] = cached
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            deck, _ = parse(text, path.stem, kind=kind, grammar=is_grammar(path, tree_root))
            rebuilt[path] = (mtime, deck)
        self.entries = rebuilt


def _entry_matches(entry, folded_query: str, key_query: str) -> bool:
    if folded_query and (folded_query in fold(entry.word) or folded_query in fold(entry.translation)):
        return True
    if key_query and key_query in pinyin_key(entry.reading):
        return True
    return False


def search_content(
    index: ContentIndex,
    query: str,
    *,
    tree_root: Path,
    kind: LanguageKind,
    tagged: set[Path] | None = None,
) -> list[ContentHit]:
    """Every hit for `query` across `index`'s decks, in tree order
    (`requirements.md` §3.1-§3.4): a file's categories, subtitles and
    entries, uncategorized entries first. A blank (or whitespace-only)
    query has no hits — the empty-query hint is the caller's job, not
    this function's. `tagged`, when given, limits hits to those files
    (uncompiled ones included — content mode searches sources)."""
    query = query.strip()
    if not query:
        return []
    folded_query = fold(query)
    key_query = pinyin_key(query)

    hits: list[ContentHit] = []
    for path, (_, deck) in index.entries.items():
        if tagged is not None and path not in tagged:
            continue
        file_label = str(path.relative_to(tree_root).with_suffix(""))

        def add_entry(entry, category: str | None, subtitle: str | None) -> None:
            if _entry_matches(entry, folded_query, key_query):
                hits.append(
                    ContentHit(
                        kind="entry",
                        source=path,
                        file_label=file_label,
                        category=category,
                        subtitle=subtitle,
                        word=entry.word,
                        reading=entry.reading,
                        translation=entry.translation,
                    )
                )

        for entry in deck.uncategorized:
            add_entry(entry, None, None)

        for category in deck.categories:
            if folded_query in fold(category.name):
                hits.append(
                    ContentHit(
                        kind="category",
                        source=path,
                        file_label=file_label,
                        name=category.name,
                    )
                )
            for entry in category.entries:
                add_entry(entry, category.name, None)
            for subtitle in category.subtitles:
                if folded_query in fold(subtitle.name):
                    hits.append(
                        ContentHit(
                            kind="subtitle",
                            source=path,
                            file_label=file_label,
                            category=category.name,
                            name=subtitle.name,
                        )
                    )
                for entry in subtitle.entries:
                    add_entry(entry, category.name, subtitle.name)

    return hits
