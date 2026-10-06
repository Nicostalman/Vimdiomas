from dataclasses import dataclass, field


@dataclass
class Entry:
    word: str
    reading: str
    translation: str
    note: str | None = None
    extra_fields: list[str] = field(default_factory=list)


@dataclass
class Subtitle:
    """A grammar-file-only third level, below a category and above its
    triads (Sprint 5 M5). A vocabulary `Category` never has any."""

    name: str
    entries: list[Entry] = field(default_factory=list)


@dataclass
class Category:
    name: str
    entries: list[Entry] = field(default_factory=list)
    subtitles: list[Subtitle] = field(default_factory=list)


@dataclass
class Deck:
    title: str
    uncategorized: list[Entry] = field(default_factory=list)
    categories: list[Category] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class Warning:
    line_number: int
    message: str
    raw_line: str
