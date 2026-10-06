# M3 · New category on its own — plan

## 1. Hide the four fields for `(new category)`

- In `EntryScreen._apply_target_state` (`src/idiomas/tui/screens/entry.py`),
  hide (`.display = False`), not merely disable, the hanzi, translation and
  note fields when the target's kind is `new_category`; show them (restoring
  today's behavior) for every other valid target. The category-name field's
  existing `display` rule (`kind == "new_category"`) is unchanged.
- Pinyin is read-only and driven by hanzi (`_on_hanzi_changed`); hide it under
  the same condition as hanzi so the four fields hide/show as one group.
- `_visible_field_ids()` already filters on `.display` and `.disabled`, so tab
  order (`action_next_field`) and `_clear_form`'s effective set fall out of
  this change with no separate edit — verify this by hand rather than adding
  new logic.
- Update the target-warning `Static`'s label if needed for clarity is out of
  scope — leave `"Choose a category"` as is; it's unrelated to this fix.

## 2. Required name, no fallback to uncategorized

- In `EntryScreen._create_entry`, when `target.kind == "new_category"` and
  `category_name` (already `.strip()`-ed) is empty, return early — no entry
  is built, no category is appended, no save happens, no cursor move, no
  `notify`. Remove the current `else: # new_category, empty name` branch that
  falls back to `deck.uncategorized.append(entry)`.
- The existing non-empty-name path (append the new `Category`, save, move the
  cursor to it) is unchanged — this is the behavior the backlog says already
  works and must be kept.

## 3. Empty categories compile without error

- In `compile.py::render_markdown`, guard each category's table the same way
  `deck.uncategorized` already is: always emit the `## {category.name}`
  heading, but only call `_render_table(category.entries)` (and the blank
  line after it) when `category.entries` is non-empty. An empty category
  becomes a bare heading with nothing under it.
- No change to `_render_table` itself or to `parser.py`/`writer.py` — the
  round trip already preserves an empty category (see task 4).

## 4. Round-trip test for an empty category

- Add a test (in `tests/test_parser.py` and/or `tests/test_writer.py`,
  whichever already covers category round-trips) that parses a `.md` file
  containing a category heading with zero entries, asserts the parsed `Deck`
  has a `Category` with `entries == []`, then writes it back and asserts the
  output matches (heading present, no entry lines).
- Add a `compile.py` test asserting `render_markdown` on a `Deck` containing
  an empty `Category` produces the heading with no `longtable`/entries under
  it, and does not raise.

## 5. Entry's file nodes start collapsed

- In `entry.py::_add_file_leaves`, drop the trailing `node.expand()` call so
  file nodes are added collapsed. `build_tree`'s `tree.root.expand()` is
  unchanged — the root (showing file nodes) still starts expanded.
- No new key binding: Textual's `Tree.action_select_cursor` already toggles
  expand/collapse for a non-leaf node on `enter` when `auto_expand` is `True`
  (the unmodified default; `NoShiftArrowsTree` doesn't touch it), alongside
  firing `NodeSelected`. Since a file node's `NodeData.kind == "file"` is not
  in `VALID_TARGET_KINDS`, `_on_node_selected` won't attempt to focus the
  form — the cursor stays on the now-expanded file node, matching the spec
  conversation's answer.
- Verify by hand that pressing `enter` a second time on an already-expanded
  file node collapses it again (Textual's default toggle), and that this is
  harmless (no target was active while collapsed).

## 6. Update existing tests for the new behavior

`tests/test_tui_entry_screen.py` tests that assumed file nodes start
expanded, or asserted the old hide/disable/fallback behavior, are updated in
place (not duplicated):

- Any test that calls `tree.move_cursor(<node under a file>)` without first
  expanding that file node needs an explicit expand step first — either
  `file_node.expand(); await pilot.pause()` or simulating `enter` on the file
  node — since `move_cursor` on a node hidden by a collapsed ancestor resets
  the cursor instead of moving it (`TreeNode._line == -1`). Candidates:
  `test_tree_structure`, `test_off_target_disables_form_and_shows_warning`,
  `test_valid_target_hides_warning_and_enables_form`,
  `test_enter_on_category_focuses_form`,
  `test_new_category_shows_category_name_field`, and any other test in this
  file that navigates straight to a leaf.
- `test_new_category_shows_category_name_field` and
  `test_tab_cycles_with_category_field_visible` gain assertions that hanzi,
  pinyin, translation and note are hidden (`.display is False`), not just
  enabled/disabled, while `new_category` is the target.
- `test_create_with_empty_category_name_becomes_uncategorized` is replaced
  with a test asserting Create is a no-op on an empty/whitespace name: no
  entry is added anywhere in the deck, the tree gains no new node, and no
  `notify` fires (or the notification isn't asserted either way — no
  observable state changes).
- Add a test for the collapsed-by-default file nodes: opening Entry shows
  file nodes without their children present in the tree's rendered lines
  until `enter` is pressed on a file node, after which the children are
  visible and the cursor is still on the file node.

## 7. Focus after creating a category

- Dev hands-on feedback: after Create adds the empty category and moves the
  cursor to it, focus was left on the Create button instead of moving into
  the newly-visible form, since nothing in `_create_category` re-focused
  after the button press that triggered it.
- `_create_category` now updates `self._active_target` to the new category's
  `NodeData` and calls `_apply_target_state`/`_focus_first_field` itself,
  synchronously, rather than waiting on the tree's own (deferred)
  `NodeHighlighted` from the `call_after_refresh`-scheduled cursor move. That
  highlight still fires once the move lands, but is a no-op by then since
  `_active_target` already equals the new target (dataclass equality).
- Covered by an assertion in
  `test_create_with_new_category_name_moves_cursor_and_accepts_followup`:
  focus is on `#hanzi` right after Create, not on `#create-button`.

## 8. Spec/design bookkeeping

- No change expected to `specs/current/design.md` — this milestone doesn't
  introduce a new cross-cutting convention, only an Entry-specific fix. If
  something surfaces during implementation that generalizes beyond Entry,
  flag it and update `design.md` then.
- After the dev signs off, fold this milestone's Decisions into
  `specs/Sprint-4/guidelines/notes-sprint-4.md` (settled form) and clear the
  Postponed-table row for the collapsed-tree idea, since it lands here.
