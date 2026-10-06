# M2 · compile_all and renderer staleness — requirements

## Anchor (from the roadmap)

Backlog (*Fix compile_all*): "compile_all does not detect changes to the
renderer, so a renderer change leaves already compiled pdfs falsely looking up
to date."

**Deliverable**, per `roadmap-sprint-5.md`: a renderer change makes every
affected PDF recompile with nothing for the dev to remember to do; the
staleness check accounts for `templates/xecjk.tex` as well as Python code; a
manual override exists; the fast path (nothing changed) stays fast and skips
pandoc entirely; both callers (`idiomas compile`, the notebook menu's
*Compile*) keep their "here's what was rebuilt" reporting; a test covers the
actual bug (change the renderer, run `compile_all`, assert the PDF rebuilds).

**Done when**, per the roadmap: changing `_render_table` and running compile
rebuilds every PDF; changing `templates/xecjk.tex` does the same; running
twice with nothing changed rebuilds nothing and takes no noticeable time;
deleting the cache is safe; a forced recompile is available; the dev confirms
against their real tree; the full test suite passes.

## No interview this round

The dev asked to skip the spec conversation for this milestone ("do m2. i
wont test so do it yourself"): the decisions below are the agent's own,
made from the roadmap's "Open for the spec conversation" section rather than
settled with the dev turn by turn, and the dev is not going to hand-test the
result. Everything the roadmap left open is decided here instead of asked.

## Decisions

- **Mechanism: content hash, not a version constant or mtime.** The roadmap's
  own leading candidate — hash what the renderer would actually produce (the
  intermediate markdown plus the template's bytes) and compare against a
  stored stamp — is adopted as-is. It's automatic (nothing to bump by hand),
  precise (catches the template for free, unlike a hand-bumped
  `RENDERER_VERSION`), and cheap next to pandoc + xelatex. `render_markdown`
  is already parse-and-render, not parse-only, so nothing new has to be
  computed to get the stamp — the same call `compile_file` already makes.
- **Stamp = `sha256(markdown.encode("utf-8") + template_bytes)`**, hex digest.
  `markdown` is `render_markdown(deck)`'s output for the source file, exactly
  what `compile_file` would pass to pandoc; `template_bytes` is
  `templates/xecjk.tex`'s raw bytes, read once per `compile_all` call via
  `importlib.resources`.
- **The cache lives at `~/.cache/idiomas/compile_cache.json`**, a single JSON
  file mapping each source `.md`'s absolute path (string) to its last-known
  stamp (string) — the roadmap's own suggested home, chosen over a sidecar
  file specifically because a sidecar would show up in Inspect Tree's own
  tree, which is a file browser over the dev's notebook, not somewhere to
  leak implementation state into.
- **A missing or corrupt cache is treated as empty**, never an error: no file,
  a `JSONDecodeError`, or an unreadable file all fall back to `{}`, which
  makes every file look stale and recompiles the whole tree once. This is
  what makes "deleting the cache is safe" true by construction rather than by
  a special case.
- **A stale-cache false positive is always acceptable.** If the cache and the
  renderer's actual output ever disagree in a way that causes an unnecessary
  recompile, that costs time, not correctness — never the other direction
  (a false negative, silently keeping a wrong PDF, is the bug this milestone
  exists to close). This is also why the cache can be deleted freely.
- **The manual override is both a CLI flag and a menu option** — the
  roadmap left this open as "whether that's a flag on `idiomas compile`, a
  key in the notebook menu, or both". Both, because the two callers
  (`__main__.py`'s subcommand, the notebook menu's *Compile*) are already
  kept in sync by sharing `compile_all`, and a dev working from the terminal
  and a dev working from the TUI both plausibly want the escape hatch
  without switching contexts.
  - CLI: `idiomas compile --force`.
  - Menu: the main menu's *Compile* option gains a sibling, *Compile
    (force)* — a second `Option`, not a hidden key binding, because
    `MainMenuScreen` is an option-list menu (`MenuScreen`) with no other
    keybinding surface, unlike Inspect Tree's tree-based `d`/`r`/`n`/`m`/`u`.
    Both call the same `compile_all`, one with `force=True`.
  - `force=True` skips the cache **check** but still updates the cache
    afterward, so a forced run leaves the cache consistent for the next
    ordinary run rather than leaving it stale.
- **The fast path stays fast**: nothing changed means every file still gets
  parsed, rendered, and hashed (cheap, pure Python), but `compile_file` — the
  pandoc/xelatex subprocess — is never invoked when the stamp matches and the
  PDF already exists. This satisfies "no noticeable time" without needing a
  cheaper pre-check than the hash itself.
- **`compile_file`'s own signature and behavior are unchanged.** It still
  parses and renders its own file rather than accepting a precomputed
  markdown string — a small duplication of work against `compile_all`'s own
  parse, but parsing is cheap and this keeps `compile_file`'s existing direct
  caller (`inspect.py`'s `_open_pdf`, compiling a stray uncompiled file on the
  spot) untouched. That direct call does not update the cache; the next
  `compile_all` run may recompile that file once more than strictly
  necessary, which is the accepted false-positive case above, not a bug.
- **Test coverage for the actual bug**: compile a file once, change what
  `render_markdown`/`_render_table` produces (or the template's contents),
  run `compile_all` again with nothing else touched, and assert the PDF was
  rebuilt. The existing mtime-based tests
  (`test_compile_all_skips_up_to_date_pdf`,
  `test_compile_all_recompiles_stale_pdf`) are rewritten against the hash
  mechanism rather than kept alongside it — mtime is no longer what
  `compile_all` looks at.

## Out of scope

- `TagCache`'s own persistence (`store.py`) — unrelated cache, mentioned only
  as a "not this sprint" item in `notes-sprint-5.md`.
- Any change to what a PDF looks like — that's M3 and M6, which this
  milestone exists to make *visible* once they land, not to implement.
- `idiomas doctor` — no new dependency, nothing to check for.
