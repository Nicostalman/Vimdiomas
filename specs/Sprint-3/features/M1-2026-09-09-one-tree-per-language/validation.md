# M1 · One tree per language — validation

Grounded in the roadmap's done-when condition, made concrete.

## Automated

- [ ] `pytest` passes in full, including the updated `test_config.py`,
      `test_compile.py`, `test_tui_browse_screen.py`,
      `test_tui_entry_screen.py`, `test_tui_main_menu.py`.
- [ ] A `test_config.py` case confirms that loading an old-format
      `.idiomas.toml` (with `source_root`/`notebook_root` keys) silently
      produces a `Config` with the correct `tree_root` and rewrites the file
      to the new format, with no prompt.
- [ ] A `test_compile.py` case confirms `notebook_path_for()` maps a `.md`
      path to the `.pdf` path beside it (same directory, suffix swap only).

## Manual (dev)

- [ ] On the dev's machine, `.idiomas.toml` migrates silently on next
      launch — no re-prompt, `tree_root` present afterward pointing at
      `tree-Chinese/`.
- [ ] The dev's real notebook lives in one `tree-Chinese/` at the project
      root, with `.md` and `.pdf` beside each other for every entry (e.g.
      `tree-Chinese/Vocabulary/Food.md` and `Food.pdf`).
- [ ] `source/` and `notebook/` no longer exist.
- [ ] `git status` shows nothing from `tree-Chinese/` (untracked and
      ignored).
- [ ] Entering vocabulary writes into `tree-Chinese/` correctly.
- [ ] Browse reads from `tree-Chinese/` correctly.
- [ ] Compile regenerates `.pdf`s into `tree-Chinese/` correctly.
- [ ] The entry screen's tree is visually indistinguishable from before the
      change — `.md` files with their categories as leaves, root labeled
      "Chinese notebook" — confirmed by the dev's own eye.

## Done when

All automated checks pass, and the dev confirms every manual item above
against their real notebook.
