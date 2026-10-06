# M5.2 · Entry screen — Requirements

## Roadmap anchor

**M5.2 deliverable.** A horizontal split: tree on the left, form on the right.

- The tree is at most three levels — directory → file → category. A file's children are `(uncategorized)` (present only when the file actually holds loose entries), then the real categories in file order, then `(new category)` always last.
- Directories and files are navigable but are **not** entry targets. The valid targets are a category, `(uncategorized)`, and `(new category)`.
- Selecting `(new category)` reveals a category-name field at the top of the form, hinting *"leave empty for no category"*. On create: a non-empty name creates the category and moves the cursor onto the new node; an empty name files the entry as uncategorized and moves the cursor to `(uncategorized)`. Either way the field disappears, because it is shown if and only if the cursor sits on `(new category)`.
- Fields are fixed-width and scroll internally — borders never move while typing.
- `Tab` cycles the fields and then the create button, wrapping back to the first. Creating clears the fields, shows `牛肉 added successfully!`, and **keeps the selection**, so consecutive words in one category need no re-navigation.
- Typing hanzi prefills pinyin, but only while the pinyin field is still untouched for that entry.

**M5's overall Done when** (checked here, since M5.2 is where entry-writing actually happens): *Twenty words can be entered into one category without touching the tree; a new category can be created and immediately filled; an empty category name produces an uncategorized entry above the first `##`; and the resulting file's formatting and tag placement survive inspection.*

## Scope

In scope:

- `src/idiomas/tui/screens/entry.py` — `EntryScreen`, replacing M5.1's `Enter vocabulary` placeholder.
- **Left: a `Tree` widget** built from `store.walk()` (M3) over `config.source_root`: directory → file → category, with each file's children ordered `(uncategorized)` (only if the parsed `Deck.uncategorized` is non-empty) → real categories (file order) → `(new category)` (always last).
- **Right: a form** — a conditional **category name** field (shown only when the tree cursor is on `(new category)`, hint text *"leave empty for no category"*), then **Hanzi**, **Pinyin**, **Gloss**, **Note** (confirmed with the user: Note is included), then a **Create** button. Fields are fixed-width `Input`s that scroll their content internally rather than growing.
- **Tree → form focus.** Confirmed with the user: `Enter`/`Right` on a valid target (category, `(uncategorized)`, `(new category)`) moves focus into the form's first visible field. Selecting a directory or file just expands/collapses it — no form interaction (per "not entry targets"). `Escape` from the form returns focus to the tree.
- **A visible key-hint footer/help bar** (confirmed with the user, added as a minimal note beyond the roadmap's own text) listing the active commands, e.g. `Enter/→ focus form · Esc back to tree · Tab next field · Enter on Create: save`, so the controls are discoverable without reading the spec.
- **Tab cycling**: `Tab` moves through the form's currently-visible fields in order (category name if visible, then Hanzi, Pinyin, Gloss, Note), then the Create button, then wraps back to the first field.
- **Hanzi → pinyin prefill**: typing in Hanzi calls M2's `guess()` and fills Pinyin, but only while Pinyin is "untouched" for the entry currently being built. Pinyin becomes "touched" the moment the user edits it directly; the touched flag resets whenever the form's fields are cleared (after a successful create, or when the tree selection changes to a different target, since that starts a fresh entry).
- **Create**, wired for real:
  - Reads the target file's current content, calls M1's `parse()`, appends the new `Entry` to the right place (the selected category's entries, or `deck.uncategorized` for `(uncategorized)`/an empty-name new-category case), calls M1's `write()`/`save()` to persist atomically.
  - `(new category)` with a non-empty name: creates the `Category` (appended at the end of `deck.categories`, matching the writer's "categories in existing order" invariant — a *new* category is necessarily last in that order), adds the entry to it, and the tree gains a new category node (positioned before `(new category)`) with the cursor moved onto it.
  - `(new category)` with an empty name: entry goes to `deck.uncategorized` instead; if the file didn't already have an `(uncategorized)` tree node, one is created (positioned first among the file's children) and the cursor moves onto it.
  - On success: clears the form's fields (resetting the prefill-touched flag), shows `<hanzi> added successfully!`, and **keeps the tree selection** on the same category/`(uncategorized)` node — so entering many words into one category needs no re-navigation, per the roadmap's own framing.
- Automated Textual `Pilot` tests (confirmed earlier for M5 generally) for: Tab cycling/wrapping (including with/without the category-name field visible), `(new category)` → non-empty name → new node + cursor move, `(new category)` → empty name → `(uncategorized)` node + cursor move, hanzi→pinyin prefill and its "stops once touched" behavior, and a real (fixture-directory) write-then-reparse round trip confirming the file's formatting/tag placement survive.

Explicitly deferred (per the roadmap's own "Later" section, unchanged by this phase):

- Editing or deleting existing entries — this screen only appends.
- Renaming/deleting categories, or creating directories/files from the app.
- Editing tags from the TUI.
- The Browse screen (M5.3) — untouched by this phase.

## Decisions

- **Note field included in the form.** Confirmed with the user, despite `compile.py`/`store.py` framing entries around Hanzi/Pinyin/Gloss elsewhere — M1's `Entry.note` is a first-class field and there's no reason the entry screen can't write it.
- **Tree→form transition: `Enter`/`Right` on a valid target, `Escape` to return.** Confirmed with the user over an alternative "focus follows selection automatically" design — an explicit confirm step avoids accidentally opening the form while just browsing the tree with arrow keys.
- **A key-hint footer is added**, at the user's explicit request, beyond what the roadmap text itself specifies — the roadmap describes behavior, not discoverability, and a first-time user has no other way to learn the controls.
- **New categories are appended at the end of `deck.categories`.** This isn't a free design choice — M1's writer already enforces "categories in existing order" as a structural invariant, and a category that didn't exist before is definitionally last in that order the moment it's created.
- **The prefill-touched flag is per entry-in-progress, resetting on clear/selection-change**, not per keystroke or per session — matches the roadmap's "untouched *for that entry*" wording precisely.
- **Tree data comes from `store.walk()`** (M3), not a separate tree-building routine — `walk()` already produces exactly the directory→file→category shape this screen needs; the screen only adds the TUI-specific `(uncategorized)`/`(new category)` leaf nodes on top of it.

## Context

- Builds on M1 (`parse`/`write`/`save`/models), M2 (`guess`), M3 (`walk`), and M5.1 (`IdiomasApp`, `MainMenuScreen`, replaces its `Enter vocabulary` placeholder).
- `stack.md`'s "TUI — Textual" section already named `Tree` and `Input` as the widgets this screen needs, and cited the focus chain (`Tab` cycling) as a reason Textual was chosen over `prompt_toolkit`/raw `curses` — this phase is where that reasoning gets cashed in.
- This is the first phase that writes to real files on disk from the TUI; all destructive/file-writing tests run against fixture directories under `tmp_path`, never the real `source/` tree.
