# M3 · New category on its own — validation

Grounded in the roadmap's done-when condition, made concrete below.

## Automated

Run the full suite:

```sh
pytest
```

All existing tests pass, including the ones updated by plan.md's task 6, plus
the new tests added by tasks 4 and 6:

- [ ] A test asserts that highlighting `(new category)` hides (not merely
      disables) hanzi, pinyin, translation and note, leaving only
      category-name and Create visible/enabled.
- [ ] A test asserts Create does nothing when the category-name field is
      empty or whitespace-only: no `Category` is appended to the deck, no
      `Entry` is created anywhere (not even in `uncategorized`), the source
      file on disk is unchanged, and no new tree node appears.
- [ ] A test asserts Create with a non-empty name still appends an empty
      `Category` with the entry, saves the file, and moves the cursor to the
      new category node (this already works and must keep working —
      regression check, not new behavior).
- [ ] The same test asserts focus lands on the hanzi field right after
      Create, not left on the Create button (dev hands-on feedback).
- [ ] A `parser.py`/`writer.py` round-trip test: a zero-entry category
      survives parse → write unchanged.
- [ ] A `compile.py` test: `render_markdown` on a deck with an empty category
      emits the heading and no `longtable`, and raises nothing.
- [ ] A test asserts Entry's file nodes start collapsed and expand in place
      (revealing children, cursor staying put) on `enter`.

## Manual (dev sign-off)

- [ ] Open Entry against a real notebook file. Highlighting `(new category)`
      shows only the name field and Create — no hanzi/pinyin/translation/note
      visible at all.
- [ ] Leave the name field empty (or spaces only) and press Create (or hit
      enter on the button): nothing happens — no new category appears, no
      notification, the tree is unchanged.
- [ ] Type a name, press Create: an empty category appears in the tree at the
      right spot, the cursor lands on it, and the normal five-field form is
      now available to add the first word.
- [ ] Compile the file containing the freshly-created empty category
      (`idiomas compile` or the app's autocompile) — the PDF is produced with
      no error, and the empty category shows as a heading with nothing under
      it.
- [ ] Reopen Entry: file nodes appear collapsed; pressing `enter` on one
      expands it to show its categories/uncategorized/new-category leaves,
      with the cursor still on the file node.
- [ ] `pytest` passes in full.
