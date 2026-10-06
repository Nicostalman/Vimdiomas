# M5.2 · Entry screen — Validation

Roadmap's M5 "Done when" (checked here): *Twenty words can be entered into one category without touching the tree; a new category can be created and immediately filled; an empty category name produces an uncategorized entry above the first `##`; and the resulting file's formatting and tag placement survive inspection.*

## Checks

1. `pytest` passes, including Pilot-based tests for:
   - Tree structure (directory → file → category, `(uncategorized)` only when applicable, `(new category)` always last).
   - Directories/files are not entry targets; category/`(uncategorized)`/`(new category)` are.
   - Tab cycling and wrapping, with and without the category-name field.
   - Hanzi→pinyin prefill and its stop-once-touched behavior.
   - Real create: file on disk updated correctly, form clears, success message, selection kept.
   - New-category creation (name given): node + cursor move, immediate follow-up entry lands in the same category.
   - Empty-name new-category creation: entry becomes uncategorized, node + cursor move.
   - Twenty consecutive creates into one category with no tree navigation in between.
2. Manual, real-terminal check:
   - `python -m idiomas` → *Enter vocabulary* opens the real entry screen (no longer a placeholder).
   - Navigate the real `source/` tree, create a handful of real entries into `Food.md`'s `Meat` category, confirm the file on disk looks correct (tabs, ordering) and `python -m idiomas compile` still produces a correct PDF from it afterward.
   - Create a brand-new category and an uncategorized entry by hand once each, confirming the on-screen behavior matches the roadmap's description exactly (field appears/disappears, hint text, cursor movement).
   - Confirm the key-hint footer is visible and accurate throughout.
3. No regressions: full `pytest` suite (M0–M5.1 tests included) still passes; the main menu's other items (Compile, Notebook, Inspect tree, Browse placeholder, Quit) are unaffected.

## Definition of done

- All of the above pass.
- `EntryScreen` replaces the M5.1 `Enter vocabulary` placeholder in `MainMenuScreen`.
- No entry editing/deletion, category renaming/deletion, tag editing, or directory/file creation — all remain out of scope per the roadmap's "Later" section.
- M5.3 (Browse screen) remains to be started as its own branch/spec.
