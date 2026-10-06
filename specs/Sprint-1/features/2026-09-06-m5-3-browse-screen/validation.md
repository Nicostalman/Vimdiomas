# M5.3 · Browse screen — Validation

Roadmap's M5.3 text: *Fuzzy filename search plus a tag filter over `tag_index()`.* Scoped (confirmed with the user) to the `notebook/` PDF tree, opening the OS's default viewer on selection.

## Checks

1. `pytest` passes, including Pilot-based tests for:
   - Unfiltered listing of all notebook PDFs.
   - Filename fuzzy filter wired to M3's `fuzzy()`.
   - Tag filter restricting to PDFs whose source `.md` carries the tag, correctly excluding an untagged or not-yet-compiled match.
   - Combined filename + tag filtering (intersection).
   - Selecting a result invokes the (mocked) `open` call with the correct absolute path.
   - Empty-state message when nothing matches.
2. Manual, real-terminal check:
   - `python -m idiomas` → *Browse* opens the real browse screen (no longer a placeholder).
   - Against the real `notebook/` tree (after running `compile`), type a partial filename and confirm ranking/filtering feels right; type a real tag (e.g. `travel`) and confirm only the right PDF(s) show; select one and confirm it actually opens in Preview (or the system default).
3. No regressions: full `pytest` suite (M0–M5.2 tests included) still passes; the rest of the main menu (Enter vocabulary, Compile, Notebook, Inspect tree, Quit) is unaffected.

## Definition of done

- All of the above pass.
- `BrowseScreen` replaces the M5.1 `Browse` placeholder.
- With this phase merged, **M5 (and the entire roadmap through M6, folded into M4) is complete.**
