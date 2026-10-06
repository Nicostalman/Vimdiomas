# M2 · compile_all and renderer staleness — plan

## 1. Cache primitives in `compile.py`

- Add `CACHE_PATH = Path.home() / ".cache" / "idiomas" / "compile_cache.json"`,
  a module-level constant (mirrors `config.py`'s `CONFIG_PATH`, and lets tests
  monkeypatch it the same way).
- Add `_load_cache() -> dict[str, str]`: read `CACHE_PATH`, `json.loads` it;
  on `FileNotFoundError`, `JSONDecodeError`, or `OSError`, return `{}`.
- Add `_save_cache(cache: dict[str, str]) -> None`: `CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)`,
  then write `cache` as JSON.
- Add `_template_bytes() -> bytes`: read `templates/xecjk.tex`'s raw bytes via
  `importlib.resources.files("idiomas") / "templates" / "xecjk.tex"`
  (`Traversable.read_bytes()` — no `as_file` needed, nothing is handed to a
  subprocess here).
- Add `_stamp_for(markdown: str, template_bytes: bytes) -> str`:
  `hashlib.sha256(markdown.encode("utf-8") + template_bytes).hexdigest()`.

## 2. Rewire `compile_all`

- New signature: `compile_all(tree_root: Path, force: bool = False) -> list[Path]`.
- Load the cache and the template bytes once per call, before the loop.
- For each source `.md` (sorted, as today's `rglob` order isn't guaranteed —
  keep output deterministic):
  - Parse it and call `render_markdown` to get `markdown` (same two calls
    `compile_file` makes internally).
  - Compute `stamp = _stamp_for(markdown, template_bytes)`.
  - Skip (no `compile_file` call) when **not** `force`, the notebook PDF
    exists, and `cache.get(str(source_path)) == stamp`.
  - Otherwise call `compile_file(source_path, notebook_path)`, append to
    `compiled`, and set `cache[str(source_path)] = stamp`.
- Save the cache once at the end, only if anything changed (avoids a write on
  the all-skipped fast path).
- Return `compiled`, same as today.

## 3. CLI: `idiomas compile --force`

- `__main__.py`: add `--force` (`action="store_true"`) to the `compile`
  subparser.
- `_compile()` takes a `force: bool` parameter and passes it through to
  `compile_all(tree_root, force=force)`.
- `main()` passes `args.force`.

## 4. Notebook menu: force option

- `main_menu.py`: add a second `Option("Compile (force)", id="compile_force")`
  to `menu_options()`, right after `"compile"`.
- Add `"compile_force": self._compile_force` to the handler dispatch.
- Add `_compile_force`, identical to `_compile` but calling
  `compile_all(self._notebook_config().tree_root, force=True)`.
- Factor the shared "build the message, push `PlaceholderScreen`" tail out of
  `_compile`/`_compile_force` only if it stays a one-liner each — otherwise a
  tiny private helper `_run_compile(force: bool)` that both call.

## 5. Tests

- `tests/test_compile.py`:
  - Replace `test_compile_all_skips_up_to_date_pdf` and
    `test_compile_all_recompiles_stale_pdf` with hash-based equivalents:
    monkeypatch `CACHE_PATH` to a `tmp_path` file, monkeypatch
    `_template_bytes` (or seed a real `templates/xecjk.tex` — it's a package
    resource, already on disk, no monkeypatch needed) so the stamp is
    computable without pandoc.
  - New: **first call to `compile_all` on a fresh cache always compiles**,
    even if the PDF file already exists on disk (no stamp recorded yet =
    stale by construction).
  - New: **second call with nothing changed skips**, and asserts
    `compile_file` was not called (monkeypatched) — the fast-path guarantee.
  - New: **the actual bug** — compile a file (real `compile_file`, or
    monkeypatched to just write a marker PDF and record what markdown it
    was given), then change the source so `render_markdown`'s output differs
    (or monkeypatch `_template_bytes` to return different bytes, simulating a
    template edit), run `compile_all` again, assert it recompiled.
  - New: **`force=True` recompiles unconditionally** even when the stamp
    matches.
  - New: **a missing cache file** and **a corrupt cache file** (garbage JSON)
    both behave like an empty cache — no exception, first run compiles
    everything.
  - New: **`compile_all` reports correctly when the cache write itself is
    exercised** — not a new test, covered by the above; no separate case
    needed.
- No new integration test: the existing
  `test_compile_file_produces_real_pdf_with_hanzi_and_tone_marks` already
  covers the real pandoc/xelatex path and is untouched by this milestone.

## 6. Docs

- `stack.md`: if it documents `compile_all`'s staleness behavior anywhere,
  update it to describe the hash mechanism instead of mtime comparison.
  (Check during implementation; only touch it if it's actually there.)
