# M3 · Discovery and search — Plan

## 1. Tree data structures

- Define lightweight dataclasses (or reuse tuples/dicts if simpler) for the tree `walk()` returns: a directory node holding child directories and files; a file node holding its path and a list of category names (plus an `(uncategorized)`-style marker only if the file actually has loose entries — mirroring M1's `Deck.uncategorized`).
- Keep this shape minimal — just enough for M5's tree widget to consume later, not a speculative general-purpose tree API.

## 2. `walk(root)`

- Recursively scan `root` for `.md` files, preserving directory structure.
- For each file, call M1's `parse()` on its contents to get a `Deck`; record its categories (in file order) and whether it has uncategorized entries.
- Return the assembled tree rooted at `root`.

## 3. `tag_index(root, cache=None)`

- Walk `root` for `.md` files (reuse `walk()` or a lighter file-listing pass).
- For each file: compare its on-disk mtime against the mtime recorded in `cache` (if any); skip re-parsing if unchanged.
- For changed/new files, `parse()` and extract `Deck.tags`; update the cache's tag -> set-of-files mapping (removing stale entries for files whose tags changed).
- Return the updated cache (same type consumed by the next call).

## 4. `fuzzy(query, candidates)`

- Implement subsequence matching: `query`'s characters must appear in order in a candidate for it to match at all.
- Score bonuses: contiguous run of matched characters, and a match starting right after a word boundary (start of string, or after a space/separator).
- Filter out non-matching candidates entirely; sort the rest by score descending, stable on ties (preserve input order for equal scores).

## 5. Tests and fixtures

- Build a small fixture directory tree (e.g. `tests/fixtures/store_tree/`) with a couple of subdirectories, a few `.md` files with categories, uncategorized entries, and multi-word tags.
- `walk()`: assert the returned tree matches the expected directory → file → category shape for the fixture.
- `tag_index()`: assert a multi-word tag (e.g. `"C1 exam"`) resolves to the right file; assert a second call with the same cache and no filesystem changes does no re-parsing (e.g. via a call-count spy or mtime-based short-circuit check); assert touching a file's mtime and changing its tags updates the index on the next call.
- `fuzzy()`: assert the roadmap's own case — querying `"fd"` against `["Food", "Fried noodles"]` ranks `Food` first; include a case where a non-matching candidate is dropped, and a case testing the word-start bonus specifically.
