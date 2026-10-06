# M3 · New category on its own — requirements

## Roadmap anchor

From [`../../roadmap-sprint-4.md`](../../roadmap-sprint-4.md):

**Deliverable.**

- Highlighting `(new category)` on Entry shows **only** a *new category name*
  field and **Create**. The hanzi, pinyin, translation and note fields are
  hidden.
- The name is **required**: Create does nothing with an empty (or
  whitespace-only) name.
- Create adds an **empty** category to the file and moves the cursor to it,
  where the normal add-word form takes over. Moving to the new node already
  works and is kept.
- **Compiling an empty category must not break.** Today `compile.py`'s
  `_render_table` would output a `longtable` with zero rows for it, which is a
  LaTeX error. Whether an empty category is left out of the PDF or shown as a
  bare heading is `plan.md`'s decision; failing to compile is not an option. A
  test covers the empty-category round trip through `parser.py`/`writer.py`.

**Done when.** A new category can be created with nothing but a name; an empty
name is refused; the cursor lands on the new category, ready for words; the
file compiles to a PDF with the empty category in it; and the full test suite
passes.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Enter vocabulary fixes* — "(new category) works perfectly in the sense that
creates a category correctly, but it only lets creating one while adding a
word simultaneously. The only fix needed here is that new category should
only have the text field for the name of the new category (and the create
button), not the other 4."

## Scope

**In scope.**

1. Highlighting `(new category)` in Entry's tree hides the hanzi, pinyin,
   translation and note fields entirely (not merely disables them) — only the
   category-name field and Create are visible. Selecting any other valid
   target (a category, uncategorized) restores the normal five-field form.
2. The category-name field's placeholder changes from "leave empty for no
   category" (now stale — it was written for the old "create a category
   alongside a word" flow) to "new category name", per the backlog's wording.
4. Create is a no-op when the category-name field is empty or
   whitespace-only: no category is added, no entry is created, the tree and
   form are left as they are.
5. An empty category (zero entries) renders in the compiled PDF as a bare
   heading with no table underneath it, instead of an empty `longtable` that
   fails to compile. This applies to `compile.py`'s `render_markdown`/
   `_render_table`, independent of how the category was created.
6. A test covers a zero-entry `Category` round-tripping through
   `parser.py`/`writer.py` unchanged (settles the Assumption logged in
   [`../../guidelines/notes-sprint-4.md`](../../guidelines/notes-sprint-4.md)).
7. **Added during the spec conversation, at the dev's request** (flagged as a
   candidate for this milestone in `notes-sprint-4.md`'s Postponed table):
   Entry's tree starts every file node collapsed. Pressing `enter` on a
   collapsed file node expands it in place, revealing its
   category/uncategorized/new-category leaves; the cursor stays on the file
   node rather than jumping to a child. The tree root itself still starts
   expanded, showing the file nodes. This is a pure `EntryTree`-construction
   change (`_add_file_leaves` no longer force-expands each file node);
   Textual's `Tree` with `auto_expand=True` (the default, unchanged by
   `NoShiftArrowsTree`) already toggles expansion on `enter` for a node with
   children, so no new key handling is needed.

**Explicitly out of scope** (unchanged from the roadmap):

- Whether the new-category name can collide with an existing category name —
  not raised by the backlog or the dev; not handled specially. (Existing
  behavior for `deck.categories.append` doesn't check for duplicates today
  either, on any category-creation path — untouched by this milestone.)
- Any change to how a category is *selected* once it exists, or to
  Uncategorized's own display rules.
- Any other panel/tree behavior beyond the collapsed-file-node change above.

## Decisions

| Decision | Rationale |
| --- | --- |
| Empty categories render as a bare heading (`## Name` with nothing under it), not left out of the PDF | Dev's choice during the spec conversation. A category the dev just created should be visibly present in the notebook, ready to be filled in, rather than silently absent until it has an entry. |
| Fields are *hidden* (`display = False`), not merely disabled, when `(new category)` is the target | This is the literal ask: "only have the text field for the name of the new category (and the create button), not the other 4" — disabling alone leaves them visible and grayed out, which the backlog doesn't ask for. |
| Empty/whitespace name: Create is a full no-op, not a fallback to "add to uncategorized" | Backlog: "not... allowed to be left empty." Today's code falls back to uncategorized when the name field is empty (`entry.py`'s `_on_create_pressed` → `_create_entry`'s `else` branch) — that fallback goes away for the `new_category` target. Note the hanzi field also still gates entry creation (`if not hanzi: return`) but that check is moot here since the hanzi field is hidden/unusable while `new_category` is the target. |
| Collapsed-file-node behavior lands in this milestone, not later | Dev's explicit call, given the option to leave it postponed. Justified by locality: `_add_file_leaves` is exactly the function this milestone already touches for the field-visibility change, and the tree it builds is what `(new category)`'s cursor-move lands on. |

## Context

- `EntryScreen._apply_target_state` (`src/idiomas/tui/screens/entry.py`)
  currently only toggles `.disabled`/`.display` for the category-name field;
  hanzi/translation/note are only ever `.disabled`, never hidden. This
  milestone changes that method (and `_visible_field_ids`, which already
  filters on `.display`, so tab-order falls out of the same field once
  hidden fields stop being included).
- `_create_entry`'s `new_category` branch currently has two paths: non-empty
  name → new category; empty name → falls through to the `uncategorized`
  append. The empty-name path is removed; Create becomes a no-op guard at the
  top of `_create_entry` (or equivalent) for `new_category` with a blank
  name.
- `compile.py::_render_table` is called unconditionally for every category in
  `render_markdown`, unlike `deck.uncategorized`, which is only rendered
  `if deck.uncategorized:`. The category loop needs the same emptiness guard,
  but must still print the heading — see Decisions above.
- Existing tests that assert current (soon-to-change) behavior:
  `test_new_category_shows_category_name_field`,
  `test_tab_cycles_with_category_field_visible`,
  `test_create_with_empty_category_name_becomes_uncategorized`, and anything
  asserting file nodes start expanded (`test_tree_structure`,
  `test_off_target_disables_form_and_shows_warning`, and others navigating
  straight to a leaf without an `enter` on the file node first). These are
  updated in place, not duplicated, per `plan.md`.
