# M3 · Discovery and search — Validation

Roadmap's own "Done when": *`fd` ranks `Food` above `Fried noodles`, and `tag_index()` finds a file by a multi-word tag.*

## Checks

1. `pytest` passes, including:
   - `fuzzy("fd", ["Food", "Fried noodles"])` (or an equivalent candidate list including both) returns `Food` ranked above `Fried noodles`.
   - `fuzzy()` drops a candidate that doesn't contain `query` as a subsequence at all, rather than just ranking it last.
   - `fuzzy()` gives a measurable bonus to a word-start match over an equivalent mid-word match (a test asserting the relative ranking, not just that both appear).
   - `tag_index()` on a fixture tree containing a file tagged `#"C1 exam"` returns that file when queried by the key `"C1 exam"`.
   - `tag_index()` called twice with no filesystem changes between calls does not re-parse unchanged files (mtime-based short-circuit is actually exercised, not just present in code).
   - `tag_index()` reflects a tag change after a file's mtime changes (edit a fixture file, bump its mtime, confirm the index updates on the next call).
   - `walk()` on a fixture tree returns the expected directory → file → category structure, including a file with no categories (only uncategorized entries) and a file with several categories in source order.
2. No regressions: full `pytest` suite (M0–M2 tests included) still passes.
3. `python -m idiomas` still exits cleanly (no accidental wiring that requires files/args not yet available).

## Definition of done

- All of the above pass locally.
- `store.py` exports exactly `walk`, `tag_index`, and `fuzzy` (plus whatever tree/cache types they need) — no TUI or compile-step wiring, per `requirements.md`.
