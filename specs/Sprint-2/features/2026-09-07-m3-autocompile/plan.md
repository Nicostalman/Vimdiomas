# M3 · Autocompile — plan

See [`requirements.md`](requirements.md) for scope and decisions — in
particular, only the roadmap's condition 2 (compile on leaving the entry
screen) is implemented; condition 1 (compile on cursor move) is out of scope.

## 1. Factor the source→notebook path mapping out of `compile_all`

- In `src/idiomas/compile.py`, extract the relative-path computation
  currently inline in `compile_all` into
  `notebook_path_for(source_path: Path, source_root: Path, notebook_root: Path) -> Path`.
- Update `compile_all` to call it.
- This is the same mapping the entry screen needs to turn a dirty
  `source_path` into the `notebook_path` `compile_file` expects.

## 2. Track dirty files on `EntryScreen`

- Add `self._dirty_files: set[Path] = set()` in `EntryScreen.__init__`.
- In `_create_entry`, after `save(deck, path)` succeeds, add `path` to
  `self._dirty_files`.

## 3. Compile-on-exit

- Add `EntryScreen.on_unmount(self) -> None`, calling a new
  `_autocompile_dirty_files()` method.
- `_autocompile_dirty_files`:
  - snapshot `self._dirty_files` (e.g. `dirty = list(self._dirty_files)`,
    then clear the set — the screen is going away regardless, but clearing
    avoids any confusion if this method were ever called twice);
  - for each `source_path` in `dirty`, compute
    `notebook_path = notebook_path_for(source_path, self.config.source_root, self.config.notebook_root)`;
  - dispatch each compile via
    `self.app.run_worker(partial(_compile_one, self.app, source_path, notebook_path), thread=True, exclusive=False, group="autocompile")`
    — **`self.app.run_worker`, not `self.run_worker`** (see requirements.md
    decision 3 for why: screen-owned workers are cancelled on unmount).

## 4. The worker function and failure feedback

- Add a module-level helper in `entry.py` (or a small new module if it grows,
  but start here since it's entry-screen-specific glue):
  ```python
  def _compile_one(app: App, source_path: Path, notebook_path: Path) -> None:
      try:
          compile_file(source_path, notebook_path)
      except (subprocess.CalledProcessError, OSError) as exc:
          app.call_from_thread(
              app.notify,
              f"Autocompile failed for {source_path.name}: {exc}",
              severity="error",
          )
  ```
- Import `compile_file` from `idiomas.compile` in `entry.py` (module-level
  import, so tests can `monkeypatch.setattr("idiomas.tui.screens.entry.compile_file", ...)`
  the same way `test_compile.py` already patches `idiomas.compile.compile_file`
  for `compile_all`).
- No success-path notification — silent on success per requirements.md
  decision 4.

## 5. Tests

New cases in `tests/test_tui_entry_screen.py` (or a new
`tests/test_tui_entry_screen_autocompile.py` if that file is getting long —
check current length before deciding):

- Creating an entry adds its file to `screen._dirty_files`.
- Pressing `q` from the tree (no `Input` focused) with a dirty file:
  monkeypatch `idiomas.tui.screens.entry.compile_file` to a recording stub,
  press `q`, `await pilot.app.workers.wait_for_complete()`, assert the stub
  was called once with the expected `(source_path, notebook_path)` pair.
- Pressing `q` with **no** dirty files: assert the stub is never called.
- A dirty file compiled via a **stub that raises**
  `subprocess.CalledProcessError`: assert `app.notify` (mock it, or capture
  via `pilot.app._notifications` if that's how the test suite already
  inspects toasts — check for precedent first) was called with
  `severity="error"` and the file's name in the message.
- Multiple dirty files (entries added to two different files in one session)
  both get compiled on exit — confirms the whole `_dirty_files` set is
  drained, not just the most recently touched file.

New case in `tests/test_compile.py`:

- `notebook_path_for` returns the expected `.pdf` path for a nested
  `source_root`-relative `.md` file, and `compile_all`'s existing two tests
  (`test_compile_all_skips_up_to_date_pdf`,
  `test_compile_all_recompiles_stale_pdf`) still pass unchanged after the
  refactor (they patch `idiomas.compile.compile_file`, not the path mapping,
  so they shouldn't need edits — run them to confirm).

Optional, if pandoc/xelatex are available in the dev environment (guarded
with `@pytest.mark.integration`, matching `test_compile.py`'s existing real
compile test): an end-to-end case that creates an entry, presses `q`, waits
for workers, and asserts a real `.pdf` file now exists on disk with the
right content — the literal roadmap scenario, not just a mocked call.
