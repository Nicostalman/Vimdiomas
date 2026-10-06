# M2 · compile_all and renderer staleness — validation

Ground truth is the roadmap's done-when. Since the dev is not hand-testing
this milestone, every item below is made mechanically checkable and run by
the agent; nothing here depends on the dev's own tree.

- [x] **A renderer change rebuilds every affected PDF.** Test: compile a file
      to a PDF, monkeypatch `render_markdown` (or `_render_table`) to produce
      different output, run `compile_all` again with the source untouched,
      assert the file is in the returned `compiled` list.
- [x] **A template change rebuilds every affected PDF.** Test: same shape,
      but change what `_template_bytes()` returns between the two
      `compile_all` calls instead of changing the renderer.
- [x] **Running twice with nothing changed rebuilds nothing.** Test: run
      `compile_all` twice in a row with `compile_file` monkeypatched to a
      spy; assert the spy was called on the first run and not on the second,
      and that the second call takes no real time (no pandoc/xelatex
      subprocess reached — implied by the spy never firing).
- [x] **Deleting the cache is safe.** Test: run `compile_all` once, delete
      `CACHE_PATH`, run it again — no exception, and the run behaves like a
      fresh cache (recompiles, doesn't crash).
- [x] **A corrupt cache is safe.** Test: write garbage bytes to `CACHE_PATH`,
      run `compile_all` — no exception, treated as empty.
- [x] **A forced recompile is available**, from both surfaces:
  - `idiomas compile --force` recompiles even when nothing changed (CLI
    argument wired through to `compile_all(force=True)`, verified by a test
    on `_compile` or by inspecting `main.py`'s argument parsing).
  - The notebook menu's *Compile (force)* option is present and calls
    `compile_all(..., force=True)` (verified by a test on
    `MainMenuScreen`, monkeypatching `compile_all`).
- [x] **The existing bug is actually closed**: the exact scenario from the
      backlog — compile a file, change the renderer, run `compile_all`,
      assert the PDF is rebuilt — has a named test that fails against the
      pre-M2 code and passes against the post-M2 code (spot-checked by
      temporarily reverting `compile_all` and confirming the new test fails,
      then restoring it).
- [x] **Both callers still report what they rebuilt.** `idiomas compile`'s
      stdout still lists compiled files or says "everything is up to date";
      the menu's `_compile`/`_compile_force` still show the same message
      shape in `PlaceholderScreen`.
- [x] **The full test suite passes**: `python -m pytest` (non-integration
      subset; `-m integration` separately if pandoc/xelatex are available in
      this environment) is green.
- [x] **No dev hand-test.** Per the dev's instruction for this milestone,
      merge does not wait on manual confirmation against a real tree — the
      mechanical checks above are the acceptance bar this time.
