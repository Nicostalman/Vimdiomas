# M9 · Manual editing checks — plan

Task groups in dependency order; the section numbers refer to
[`requirements.md`](requirements.md).

## 1. The grammar fix (§Context)

The prerequisite: without it every grammar file in the tree is already warned
about.

1. Thread the tree root through `store.walk`: a private recursive helper takes
   `(root, tree_root, kind)`, the public `walk(root, *, kind)` seeds it with
   `root`.
2. `_parse_file(path, tree_root, kind)` passes
   `grammar=is_grammar(path, tree_root)` to `parse()`.
3. Test: a grammar file's `###` lines produce no warnings; the same line in a
   vocabulary file produces one.

## 2. The checks the parser is missing (§1, §2)

Each is a warning only — no deck, tag list or rendered output changes. One test
per row of §2's *Reported* table, plus one per row of *Not reported* asserting
silence.

1. An entry row with more than `N` fields, an extra field having content:
   `extra column(s) never rendered: <fields>`. An empty extra field stays
   silent.
2. An entry row with an empty word: `an entry with no word`.
3. A tag-block token that is not a `#tag`: `not a tag: <tokens>`.
4. A second `## Tags` heading: `the tag block appears more than once`.
5. No `# ` header line: `no '# <stem>' header line`, at `line_number = 0` with
   an empty `raw_line`.
6. A category name twice in a file, a subtitle name twice in a category:
   `category '<name>' appears more than once` / `subtitle '…'`.
7. A regression test that the deck, tags and `extra_fields` of every one of
   these files are byte-for-byte what they are today — the warnings are
   additive.

## 3. Warnings reach the trees (§5)

1. `FileNode` gains `warnings: list[Warning]`; `_parse_file` keeps them.
2. A file that cannot be read or decoded is still listed, with one synthetic
   warning, rather than taking the walk down (M1's rule: one file never locks
   you out of the tree).
3. A shared label helper in `tui/screens/base.py`: the stem as `literal()`,
   plus a dim `⚠` when the node has warnings. Used by
   `inspect._add_file_leaf` and `entry._add_file_leaves`.
4. Tests: the marker in both trees, absent for a clean file, and `[b]x` still
   shown as typed.

## 4. Inspect Tree's warnings block (§5)

1. A formatter for the block: heading with the count (singular for one), each
   warning as `line N: message` with its raw line indented beneath, a
   file-level warning without a line number, capped at ten with `… and N more`.
2. `compose`: `#preview-warnings` above a new `#preview-body` container wrapping
   `#preview-message` and `#preview-image`; `app.tcss` rules (dim,
   warning-coloured, auto height, not focusable).
3. `_preview_content_region` reads `#preview-body`, so the block shrinks the
   raster instead of overflowing the panel.
4. `_update_preview` sets or hides the block from the highlighted node's
   warnings before the mode-specific branch — shown in MD mode only (revised
   after hand-testing: in PDF mode it displaced the page).
5. Tests: the block's text in MD mode; hidden in PDF mode, for a directory, the
   root and a clean file; the cap; a file-level warning's line; the content is a
   `Text`.

## 5. MD mode's exit is the re-check (§4)

1. In `_open_md`, when the mtime changed: rebuild the tree, restore the cursor
   to the same path when it still exists, refresh the preview, and notify
   `"<name>: N warnings — see the preview."` (singular for one) when the file
   has warnings.
2. No rebuild and no notification when the mtime is unchanged.
   `nvim` is launched as `nvim -c "set noexpandtab" <file>` so that Tab writes
   the tab character the format's columns need (hand-testing, 2026-10-02).
3. Tests with a fake `nvim`: one that adds a category (tree rebuilt, category
   present), one that adds a table (marker, block, exactly one notification),
   one that changes nothing (neither).

## 6. Trivial and non-trivial changes, as tests (§3)

One test per row of §3's table — mostly verification of behaviour that already
works, which is the point. No differ: the TUI is rebuilt from the file, so the
tests assert the result, not a detected change.

1. `tests/test_parser.py` / `tests/test_writer.py`: a renamed category, an added
   or removed category, a moved entry, reordered categories and entries, an
   edited field or note, an added tag — each round-trips with no warnings.
2. `tests/test_tui_entry_screen.py`: a category renamed on disk is the create
   target's name the next time the screen is mounted; a create into a
   hand-edited file keeps the hand edits.
3. `tests/test_compile.py`: a renamed category changes the rendered markdown and
   so the stamp, and the next Compile rebuilds that file.

## 7. Compile and the CLI (§6)

1. `Render` gains `warnings`; `render_source` fills it from its existing
   `parse()` call.
2. `compile_all` appends one `CompileWarning` per parse warning, for every file
   it looks at, rebuilt or skipped.
3. `compile_summary` groups warnings by source and indents every line of a
   message; `__main__._compile` prints the same grouping to stderr, with no
   change to the exit status.
4. Tests in `tests/test_compile.py`, `tests/test_tui_main_menu.py` and
   `tests/test_main.py`: a file with a table is compiled **and** warned about;
   an up-to-date tree still reports its warnings; the exit status stays 0, and 1
   when a real failure is alongside; the summary's grouping and indentation.

## 8. Docs and the full suite (§7)

1. `specs/current/design.md`: the new section under *Failures are reported,
   never fatal* — the format, the lossy/lossless rule, the marker, the block,
   the re-read points.
2. `README.md`: the marker, the MD-mode re-check, and the format the app writes.
3. Run the whole suite; then hand off for the dev's own testing per
   [`validation.md`](validation.md).
