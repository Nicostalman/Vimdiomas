# M4 · Unreadable notebook files — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M4 · Unreadable
notebook files*:

> The local bug review of 2026-10-07 found that one `.md` file with invalid
> UTF-8 aborts a whole Compile run and raises during Browse's tag filter, even
> though tree discovery and content search already tolerate it.
>
> **Deliverable.**
>
> - Compile reports a read or decode failure for the affected source, continues
>   with other files, and keeps successful compile results and cache stamps.
>   The CLI and notebook menu show the failure without a traceback or a lost
>   TUI session.
> - Single-file compile paths used by Entry, Browse and Inspect Tree report the
>   same failure to the user without taking down the app.
> - Browse's tag filter skips unreadable source files and still returns results
>   from readable files, in both filename and content modes.
> - Inspect Tree's MD preview shows a read-error message for an undecodable
>   file; its tree warning remains visible.
>
> **Done when.** With an invalid UTF-8 `.md` before a valid one, Compile
> reports one failed source and compiles the valid file; the CLI exits nonzero
> without a traceback, and the TUI stays open. Tag filtering still finds tags in
> the valid file in both Browse modes. Opening or previewing the bad source
> gives a user-visible error without ending the session. The full test suite
> passes.

The source is the local, gitignored `bug-report.md` (review of 2026-10-07,
commit `9acfd9a`), findings 1 and 2 and its *Additional review note*. It is
never committed, so the link resolves only on the dev's machine. The sprint
backlog has nothing on M4; the notes
([`../../guidelines/notes-sprint-8.md`](../../guidelines/notes-sprint-8.md),
*M4 added after the 2026-10-07 bug review*) record why it exists.

**The bug in one line.** `store._parse_file`, `ContentIndex.refresh` and
`walk` already catch `OSError` and `UnicodeDecodeError` from
`path.read_text(...)`. Every other place that reads a notebook's `.md` does
not, so one file with a stray byte (`b'# Bad\n\xff\n'`) ends a Compile run, a
tag filter, a preview or an Entry action with a traceback.

## Decisions

Settled with the dev in the spec conversation, 2026-10-07.

| Decision | Rationale |
| --- | --- |
| **One failure text everywhere: the tree warning's existing wording**, `could not be read: <reason>`, where the reason is Python's own (`'utf-8' codec can't decode byte 0xff in position 7: invalid start byte`, or `[Errno 13] Permission denied: '…'`) | Dev's choice, over a friendlier sentence for invalid UTF-8. Compile, single-file compile, Inspect Tree's preview, Entry and the tree's `⚠` then say the same thing, with no second wording to keep in sync. The reason already tells the two causes apart. |
| **Browse omits an unreadable file silently**, in both modes | Dev's choice, over a notification. Matches `ContentIndex.refresh`, which already skips it without a word. Browse has no warning surface, and the `⚠` in Inspect Tree and Entry already tells the user about the file. |
| **Entry is included**: creating an entry, category or subtitle in a file that can't be read gives an error notification and writes nothing | Dev's choice. Same bug class (`Entry._read_deck`); without it the rule "one file never ends the session" would have a hole on the screen where users type. Not in the roadmap's list, added here. |
| **A file that becomes unreadable after it was listed is handled where it is read**, with the same text. No special state, and no tree rebuild | Dev's choice, over refreshing the tree to show a `⚠` at once. A late failure behaves exactly like one that was bad from the start; the next time a tree screen opens, the `⚠` is there. |

Proposed by the agent in this spec, for the dev to confirm in review:

| Decision | Rationale |
| --- | --- |
| **The one reader raises an `OSError` subclass**: `store.SourceReadError(OSError)` from `store.read_source(path)`. It wraps both an `OSError` and a `UnicodeDecodeError` | `autocompile_one` and `open_source_pdf` already catch `(CalledProcessError, OSError)` and print `failure_message(exc)` / `{exc}`. Raising an `OSError` subclass makes them report the new failure with no change, and the one place that needs a new `except` is the one that today has none (§1). |
| **Inspect Tree's rename of an unreadable file completes the move and skips the retitle** (§5). A third site beyond the roadmap's list, found while reading every `read_text` | `_rename_file` moves the file and *then* reads it to rewrite its `# Title` line, so renaming an undecodable file raises with the file already moved. Refusing the rename would leave the user unable to rename the bad file out of the way; the title cannot be rewritten, and saying so is enough. |
| **`tag_index` leaves a skipped file out of its cache**, so it is retried on every call | A file that fails costs one failed read per call; keeping it out means it is picked up the moment it is fixed, with no mtime comparison to get wrong. |

## 1. The reader (`store.py`)

- `class SourceReadError(OSError)`. Its message is `could not be read:
  <reason>`, where `<reason>` is `str()` of the `OSError` or
  `UnicodeDecodeError` that caused it. The original is chained (`from exc`).
- `read_source(path: Path) -> str`: `path.read_text(encoding="utf-8")`, turning
  `OSError` and `UnicodeDecodeError` into `SourceReadError`. The one function
  every read of a notebook's `.md` goes through.
- `_parse_file` (the tree's warning) and `ContentIndex.refresh` use it. Their
  behaviour is unchanged: `_parse_file` still returns a `FileNode` whose one
  warning is `Warning(0, "could not be read: <reason>", "")`, byte for byte
  what it says today, and `refresh` still skips the file.
- `compile.render_source` uses it (§2). `store.py` is already imported by
  `compile.py`, so there is no new import cycle.

## 2. Compile (`compile.py`)

- `render_source` reads through `read_source`, so it raises `SourceReadError`.
  `compile_file` therefore does too, when it is called without a `render`.
- `compile_all`: the `render_source` call moves under its own `try`. On
  `SourceReadError` the file is appended to `report.failed` as
  `CompileFailure(source_path, failure_message(exc))` and the loop goes on to
  the next file. `failure_message` already returns `str(exc)` when there is no
  stderr, so the message is `could not be read: <reason>`.
  - The bad file contributes no warnings (it cannot be parsed) and its cache
    entry is **left alone**: a stamp earned before the file went bad is kept,
    and the next run retries it. Its old PDF, if any, stays.
  - The other files compile, keep their stamps, and the cache is saved in the
    existing `finally`.
- Nothing else in the report changes. A read failure and a pandoc failure are
  both `CompileFailure`s; the Compile screen's *Failed:* block and the CLI's
  stderr listing print them the same way, and `vimdiomas compile` exits 1.
- `autocompile_one` and `open_source_pdf` (`tui/screens/base.py`) already catch
  `OSError` around `compile_file`, so they report `Compile failed for
  Bad.md: could not be read: …` (Entry's and Inspect Tree's autocompile) and
  `Compile failed for Bad.md:\ncould not be read: …` (Inspect Tree's PDF mode
  and Browse's `enter`) as errors, and open nothing. No code change; tests pin
  it (§7).

## 3. Browse's tag filter (`store.tag_index`)

- A file whose `stat()` raises `OSError`, or whose `read_source` raises
  `SourceReadError`, is **skipped**: it is not in the returned cache's
  `mtimes` or `tags`, so `files_for(tag)` never lists it.
- Readable files are indexed as before, including those after the bad one in
  `rglob` order.
- `paths_with_tag` (filename mode) and `_refresh_content_results` (content
  mode) both call `tag_index`, so both modes are fixed by this alone. No
  warning is shown (decision above).

## 4. Inspect Tree's MD preview (`tui/screens/inspect.py`)

- `_update_preview`'s MD branch reads through `read_source` and, on
  `SourceReadError`, shows `<name> could not be read: <reason>` in the preview
  (`literal(f"{data.path.name} {exc}")`, as the text is the user's). This
  replaces the existing `Could not read {name}: {exc}` for `OSError`, which the
  new reader subsumes.
- The tree's `⚠` and the warning block above the preview stay, as they are
  today: `_show_warnings` runs before the branch. The preview's two reads of
  the same failure (the warning block and the message) are the intended
  result: the warning is the tree's, the message is the preview's.
- PDF mode is untouched (it never reads the `.md`).

## 5. Inspect Tree's rename (`_rename_file`)

- The file is moved as today. The retitle read goes through `read_source`; on
  `SourceReadError` the retitle and the write are skipped, and a **warning**
  notification says `<new_name> was renamed, but its title was left as it is:
  <exc>`, i.e. `… left as it is: could not be read: <reason>`.
- The rest of the method is unchanged: the old PDF is removed if it existed, and
  the recompile is **not** started for an unreadable file (it could only fail the
  same way, with a second notification).
- Nothing else about renaming changes. A readable file renames, retitles and
  recompiles exactly as before.

## 6. Entry (`tui/screens/entry.py`)

`_read_deck` reads through `read_source`. Everything that calls it
(`_create_entry` and `_create_grammar_entry`, the category creation, the
subtitle creation, and `_read_category`, which keeps the grammar subtitle
select in sync with the tree's cursor) handles `SourceReadError`:

- an **error notification** naming the file and the cause, `<file name> could
  not be read: <reason>`, with markup off;
- **nothing is written** and the form keeps what was typed;
- the screen stays open and usable. `_read_category` returning nothing leaves
  the subtitle select with no choices instead of raising.

An unreadable file is a leaf with no categories in the Entry tree (the tree
already built it with a warning), so this is reachable only when a file fails
after the tree was built (the late failure above), or through the
uncategorized target of a file that became unreadable.

## 7. Tests

- `tests/test_store.py`: `read_source` on a readable file, on invalid UTF-8
  (message starts `could not be read:` and names the cause) and on a missing
  file (`SourceReadError` too, chained from `FileNotFoundError`); `walk` and
  `ContentIndex` unchanged (the existing tests keep passing); `tag_index` with
  `Bad.md` before and after `Good.md` returns `Good.md`'s tag in both orders and
  never lists `Bad.md`; a fixed file is indexed on the next call.
- `tests/test_compile.py`: `compile_all` with `Bad.md` (`b'# Bad\n\xff\n'`)
  before `Good.md` (pandoc stubbed at `_run_pandoc`): one `failed` entry whose
  message starts `could not be read:`, `Good.pdf` compiled, `Good`'s stamp
  saved, `Bad` has no stamp; a stamp for `Bad.md` earned earlier survives its
  going bad; `compile_file(Bad.md, …)` raises `SourceReadError`.
- `tests/test_main.py`: `vimdiomas compile` on that tree prints the failure to
  stderr, exits 1 and prints no traceback.
- `tests/test_tui_main_menu.py`: the notebook menu's Compile on that tree shows
  *Failed:* with the file and its cause, and the app is still running.
- `tests/test_tui_browse_screen.py`: filename mode and content mode with a tag
  filter and an unreadable file: the readable file's results are listed, and no
  notification is shown. `enter` on a result with no PDF whose source has gone
  bad notifies `Compile failed for …` and opens nothing.
- `tests/test_tui_inspect_tree.py`: MD mode on the bad file shows the message
  in the preview and the tree's `⚠` and warning block are still there; PDF
  mode `enter` on it (no PDF) notifies and opens nothing; renaming it moves it,
  skips the retitle, warns, removes the old PDF and starts no compile; the
  session survives each.
- `tests/test_tui_entry_screen.py`: creating an entry in a file that went bad
  after the tree was built notifies, writes nothing and keeps the form; the same
  for a category; `_read_category` on such a file doesn't raise.

## 8. Docs

- **`design.md`**, *Failures are reported, never fatal*: add the rules for an
  unreadable file (§2 to §6, in the same voice): Compile lists it under
  *Failed:* with `could not be read: <reason>` and goes on; the single-file
  compile paths notify the same text; Browse leaves it out without comment;
  Inspect Tree's MD preview says so; Entry notifies and writes nothing; a
  rename moves it and warns. The sentence in *A file edited by hand is
  checked, never refused* that a file is never refused stays true: an
  unreadable file is not refused, it is reported.
- **`stack.md`**, *A compile failure is per file*: `compile_all` catches
  `SourceReadError` (an `OSError`) from `render_source` as well; and one
  sentence for `store.read_source` / `SourceReadError` as the one reader of a
  notebook's `.md`.
- The Sprint 8 notes: M4's decisions into settled form when it merges.

## 9. Out of scope

- Reading a file in another encoding (no detection, no repair, no
  re-encoding). The file is reported, never rewritten.
- Showing the tree's `⚠` or a notification in Browse (decision above).
- Refreshing a tree after a late failure (decision above).
- `nvim` opening a bad file: `Enter` in MD mode runs the editor, which handles
  the bytes itself.
- Reads that are not notebook sources: the config file, the compile cache, the
  Linux input-method files, `install.py`'s shell file. Each has its own
  handling or has never been reported as a problem.
- The README.
