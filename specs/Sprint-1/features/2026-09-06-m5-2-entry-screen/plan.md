# M5.2 · Entry screen — Plan

## 1. Tree construction

- A function (e.g. `build_tree(tree_widget, dir_node: DirNode)`) that walks a `store.DirNode` (from M3's `walk()`) and populates a Textual `Tree`, recursively adding directory and file nodes, and for each file node adding `(uncategorized)` (if `file_node.has_uncategorized`), then each category name (in `file_node.categories` order), then `(new category)`.
- Each tree node's `data` payload identifies its kind and what it refers to: `{"kind": "dir"|"file"|"category"|"uncategorized"|"new_category", "file_path": Path | None, "category_name": str | None}`.

## 2. Screen layout

- `EntryScreen(Screen)`: `compose()` yields a `Horizontal` containing the `Tree` (left) and a form container (right, initially without the category-name field).
- Form container: category-name `Input` (hidden/removed unless cursor is on `(new category)`), Hanzi `Input`, Pinyin `Input`, Gloss `Input`, Note `Input`, a `Button("Create")`, and a `Static` footer with the key-hint text.
- Fixed-width inputs: Textual `Input` already scrolls its content when it overflows a fixed `width`; set explicit widths in `app.tcss`.

## 3. Tree selection handling

- On tree node highlighted/selected: if the node's kind is `category`/`uncategorized`/`new_category`, treat it as a valid target; on `Enter`/`Right`, focus the form's first visible field, showing/hiding the category-name field based on whether the kind is `new_category`.
- Changing the tree's *target* selection resets the form: clears all fields and the prefill-touched flag.

## 4. Hanzi → pinyin prefill

- On the Hanzi field's `Changed` event: if the pinyin-touched flag is `False`, set the Pinyin field's value to `pinyin.guess(hanzi_value)`.
- On the Pinyin field's `Changed` event: if the change wasn't triggered by the prefill itself (guard with a flag while programmatically setting it), mark pinyin as touched.

## 5. Tab cycling

- Override the form container's focus chain (or rely on Textual's default `Tab` focus order across the currently mounted/visible widgets) so `Tab` moves category-name (if visible) → Hanzi → Pinyin → Gloss → Note → Create → back to the first field. Test this explicitly since Textual's default focus order depends on mount order and visibility, which is exactly the part worth pinning down with a test.

## 6. Create action

- On Create pressed (or Enter on the Create button): read the target file's `Path` from the tree node's data (for `(new category)`, it's the file node's own path, tracked when building the tree); `parse()` its current text; build the new `Entry` from the form fields (`note` is `None` if blank); append it:
  - `category` target → `deck.categories[...].entries.append(entry)`.
  - `uncategorized` target → `deck.uncategorized.append(entry)`.
  - `new_category` target, non-empty name → append a new `Category(name=..., entries=[entry])` to `deck.categories`.
  - `new_category` target, empty name → `deck.uncategorized.append(entry)`.
  - `write()`/`save()` back to the same path.
- Update the tree in place (no full re-walk): for a newly created category, insert a new `category`-kind child before the file's `(new category)` node and move the tree cursor there; for the empty-name case, insert an `uncategorized`-kind child as the file's first child (if one didn't already exist) and move the cursor there; otherwise keep the cursor where it was.
- Clear the form fields, reset the touched flag, show `f"{hanzi} added successfully!"` (e.g. via a transient `Static`/notification).

## 7. Tests

- `tests/test_tui_entry_screen.py`, `Pilot`-driven, against a fixture source tree under `tmp_path`:
  - Tree renders the expected directory→file→category(+`(uncategorized)`+`(new category)`) structure for a couple of fixture files (one with uncategorized entries, one without).
  - Selecting a directory/file does not open the form; selecting a category/`(uncategorized)`/`(new category)` and pressing Enter does.
  - Tab cycles through all visible fields and the Create button, wrapping back to the first, both with and without the category-name field visible.
  - Typing hanzi prefills pinyin; editing pinyin directly stops further prefill for that entry; clearing/starting a new entry resets the touched flag.
  - Creating an entry into an existing category: file is updated on disk, `parse()` on the result shows the new entry in the right place, form clears, success message shown, tree selection unchanged.
  - `(new category)` with a name: new category appears in the file and the tree, cursor lands on it, a second entry created immediately after lands in the same new category without re-navigating.
  - `(new category)` with an empty name: entry lands in `deck.uncategorized`, above the first `##` on disk; `(uncategorized)` tree node appears if it didn't exist, cursor lands on it.
  - Twenty consecutive creates into one category (the roadmap's own numeric bar) succeed without any tree navigation in between, and the resulting file still parses back to the expected `Deck`.
