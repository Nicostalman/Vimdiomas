# M3 · Discovery and search — Requirements

## Roadmap anchor

**Deliverable.** `store.py`: `walk()` builds the tree (directory → file → category); `tag_index()` maps tags to files, cached by mtime; `fuzzy()` scores subsequence matches with bonuses for contiguous runs and word starts.

**Done when.** `fd` ranks `Food` above `Fried noodles`, and `tag_index()` finds a file by a multi-word tag.

## Scope

In scope for this phase:

- `src/idiomas/store.py` with three functions:
  - `walk(root: Path) -> Tree` — builds a directory → file → category tree by scanning the filesystem under `root` and parsing each `.md` file found (via M1's `parse()`) for its categories.
  - `tag_index(root: Path, cache: TagCache | None = None) -> TagCache` — maps each tag to the set of files carrying it, keyed by tag string (including multi-word tags like `"C1 exam"`, stored without the surrounding quotes/`#`). Recomputes only files whose mtime changed since the given cache, so repeated calls in one TUI session are cheap.
  - `fuzzy(query: str, candidates: list[str]) -> list[str]` — subsequence-matches `query` against each candidate, scores with bonuses for contiguous runs and word-start hits, and returns the candidates that matched at all, ranked best-first. Non-matches are dropped, not just ranked last.
- `root` is a caller-supplied `Path` in every function — nothing here hardcodes `source/`. The TUI (M5) is expected to pass `source/`, but `store.py` itself is agnostic to which directory it's pointed at (this also keeps it testable against small fixture trees rather than the real `source/`).
- Test fixtures (a small tree of a few directories/files/categories/tags) plus pytest tests for all three functions.

Explicitly deferred:

- Wiring `store.py` into the TUI (`Browse` screen, tree widget) — that's M5.
- Persisting the mtime cache to disk between process runs — see the caching decision below.
- Any notion of directory/file *creation* — `store.py` only reads what's already on disk (the roadmap's "Later" section defers creating directories/files from the app entirely).
- Search inside entries (hanzi/glosses) — the roadmap's "Later" section explicitly defers this; `fuzzy()`/`tag_index()` here only cover filenames and tags.

## Decisions

- **`walk()`/`tag_index()` take a `root: Path` parameter** rather than hardcoding `source/` — confirmed with the user: this keeps `store.py` reusable and unit-testable against fixture directories, independent of the real project layout. The TUI is what will bind it to `source/` in M5.
- **Tag cache is in-memory only, no disk persistence.** `tag_index()`'s cache is a plain value the caller holds onto (e.g. across TUI session lifetime) and passes back in on the next call; nothing is written to a dotfile or similar. Rationale: this is a single-process, single-user terminal app (per `mission.md`/`stack.md`'s minimalism) — a cache that needs to survive process restarts adds invalidation edge cases (deleted files, moved files, clock skew) for a rebuild that's cheap enough to redo from scratch each launch. If a later milestone finds cold-start `tag_index()` calls too slow in practice, that's a reason to revisit, not a reason to build it now.
- **`fuzzy(query, candidates) -> list[str]`** — takes the full candidate list and returns a ranked, filtered (matches-only) list; the caller never sees raw per-candidate scores or does its own sorting. This matches the roadmap's framing of `fuzzy()` as the thing that "ranks" `Food` above `Fried noodles`, not a scorer that leaves ranking to the caller.
- **Tag storage format.** Per M1's parser, tags are written as `#tag` or `#"multi word tag"` in the `## Tags` line. `tag_index()`'s keys are the bare tag text (no `#`, no surrounding quotes) so `"C1 exam"` and `travel` are both valid, comparable keys.

## Context

- Builds directly on M1's `Deck`/`Category`/`Entry` models and `parse()` — `walk()` calls `parse()` per file to get categories; `tag_index()` reads each file's `Deck.tags`.
- The tree shape `walk()` produces (directory → file → category) is the same three-level shape M5.2's tree widget will need (`(uncategorized)`, real categories, `(new category)` are TUI-only additions layered on top in M5 — not `store.py`'s concern here).
- `stack.md`'s "Search" section already fixed the algorithm choice: a local subsequence-with-bonuses scorer in about thirty lines, explicitly rejecting `fzf` as an external dependency. This phase implements exactly that, not a wrapper around a library.
