# M2 · Crash-proofing — plan

Task groups, ordered so later groups depend only on earlier ones. Group 1 is the
escaping helper every screen then uses; 2–3 the compiler; 4–5 Inspect Tree's two
crashing keys; 6 docs.

Every group starts by **re-reproducing its finding as a failing test**, per
`notes-sprint-6.md`'s first Assumption — including the two halves the report
itself marks as read-from-code rather than reproduced (`idiomas compile`'s
traceback in #12, and new-directory in #14).

## 1. #16 — `literal()` and every call site

- `base.literal(text: str) -> rich.text.Text`: `Text(text)`, with a docstring
  naming it as the single route for user-derived text reaching a widget, and
  why it is not a string escape (see requirements' *Corrections*).
- Notifications carrying user text pass `markup=False` — `app.notify` takes
  only a `str`.
- Route through it, per the report's location list and its closing note about
  notifications:
  - `inspect.py`: `_show_preview_message`'s text when it is file content or an
    OS error message (`_update_preview`'s MD branch and the `pdftotext`
    fallback in `_run_extract_text`, and both workers' `Preview failed`);
    `_add_file_leaf`'s `file_node.path.stem`; every `app.notify`/`self.notify`
    interpolating a name; `ConfirmDialog`'s delete message.
  - `entry.py`: `_add_file_leaves`'s file stem and category names, and the
    leaf added by category creation; every notification interpolating hanzi,
    a category name or a subtitle name.
  - `panels.SelectField`: its option labels and its display line, which is
    where the subtitle names reach a widget.
  - `browse.py`: result labels.
  - `base.build_dir_tree`: directory labels (a directory name is user text
    too, in both trees).
  - `base.autocompile_one`: its failure notification.
  - `PlaceholderScreen` accepts a `str | Text`; the compile summary (group 3)
    passes it a `Text`, since the stderr tail is full of LaTeX brackets.
- Tests (`test_tui_inspect_tree.py`, `test_tui_entry_screen.py`,
  `test_tui_browse_screen.py`, `test_tui_panels.py`), the report's regression
  line — `[/]`, `[/x]` and `[b]x[/b]` in file content, file names, category
  names and subtitle names — plus a trailing and an embedded backslash, the
  case a string escape gets wrong:
  - A deck with `to [/] test` in a translation: Inspect Tree opens, `tab` to MD
    mode does not raise, and the preview shows the literal `[/]`.
  - A file named `[b]x.md`: it is listed as `[b]x` in both trees, not `x`.
  - A category named `Verbs [/x]`: Entry opens; the leaf shows the literal name;
    it is selectable and an entry can be added to it.
  - A subtitle named `[b]s[/b]` shows literally in the `SelectField` list.
  - A notification naming a file containing `[/]` does not raise.
  - The `pdftotext` fallback preview path with bracket text in the PDF text.
  - `literal()` itself, unit-tested: `a\[b]`, `trail\` and `[b]x[/b]` come
    back with `.plain` equal to the input.

## 2. #12 — per-file compile in `compile.py`

- `compile.CompileFailure` dataclass: `source: Path`, `message: str`.
- `compile.CompileReport` dataclass: `compiled: list[Path]`,
  `failed: list[CompileFailure]`; a `__bool__`/`any_work` helper if the callers
  want one.
- `compile.STDERR_TAIL_LINES = 10`, and
  `failure_message(exc) -> str`: the last `STDERR_TAIL_LINES` non-empty lines
  of `exc.stderr` decoded UTF-8 with `errors="replace"`, falling back to
  `str(exc)`.
- `compile_all` returns a `CompileReport`. Per file, `compile_file` is wrapped
  in `try/except (subprocess.CalledProcessError, OSError)`: on failure, append a
  `CompileFailure` and continue without touching the cache entry; on success, as
  today.
- The `if cache_changed: _save_cache(cache)` moves into a `finally` around the
  loop.
- Tests (`test_compile.py`):
  - A tree with one good and one failing source (a heading containing
    `\new`, per the report): `compile_all` returns both a compiled path and a
    failure, raises nothing, and the good file's PDF exists.
  - The failing file's `message` is non-empty and contains a recognisable piece
    of the xelatex error (integration test, real pandoc/xelatex).
  - The cache is written after such a run, and a second `compile_all` skips the
    good file and retries the failing one.
  - A run where every file fails still writes no bogus stamps and returns an
    empty `compiled`.

## 3. #12 — the three callers

- `main_menu._run_compile`: build the `PlaceholderScreen` message from the
  report — a `Compiled:` block listing successes, then, if any,
  a `Failed:` block with each failed file's full path — as the `Compiled:`
  block already shows them, and because a bare name is ambiguous between
  `Vocabulary/Food.md` and `Grammar/Food.md` — and its message indented below
  it. The whole message goes to the screen as `literal()`, the stderr tail
  being full of LaTeX brackets. `Everything is up to date.` when both lists
  are empty.
  Both the `compile` and `compile_force` options keep routing through it.
- `inspect._open_pdf`: wrap the fallback `compile_file` in
  `try/except (subprocess.CalledProcessError, OSError)`; on failure, notify with
  the same `failure_message` tail and return **without** calling `open_file`.
- `__main__._compile`: print the successes as today, then print each failure to
  `sys.stderr`; track whether any language had failures and
  `raise SystemExit(1)` at the end if so.
- Tests:
  - `test_tui_main_menu.py`: choosing Compile with one good and one failing file
    leaves the app running, pushes `PlaceholderScreen`, and its text names the
    failing file and contains its error tail.
  - `test_tui_inspect_tree.py`: `Enter` in PDF mode on a failing file with no
    PDF posts an error notification, opens nothing, and the app stays up.
  - `test_main.py`: `idiomas compile` over such a tree prints the success, prints
    the failure to stderr, and exits 1; over a clean tree it exits 0.

## 4. #14 — name validation

- `store.validate_name(name: str) -> str | None`. Refuse, each with its own
  message: empty after strip; `name != name.strip()`; contains `/`, `\`,
  `os.sep` or `os.altsep`; contains a C0 control character or DEL; is `.` or
  `..`.
- `inspect.action_rename`, `action_new_dir`, `action_new_file`: call it in each
  `_handle` before anything else; on a message, `notify(..., severity="error")`
  and return.
- `action_rename`'s file branch is reordered: collision check → `rename` →
  `_retitle` + `write_text` **on the new path** → PDF handling. The whole body is
  wrapped in `try/except OSError` → notify.
- `action_new_dir` and `action_new_file` wrap their `mkdir`/`write_text` the
  same way.
- `action_new_dir` keeps creating at the tree root (see requirements'
  *Corrections*: the dev's Sprint 3 backlog rules out nesting).
- Tests (`test_store.py`): `validate_name` accepts ordinary names and a name
  with spaces inside it; refuses `""`, `"  "`, `" x"`, `"x "`, `"a/b"`,
  `"a\\b"`, `"."`, `".."`, `"../x"`, `"a\x00b"`, `"a\tb"`.
- Tests (`test_tui_inspect_tree.py`), the report's regression line — `/`, `..`
  and `../x` through rename (file and directory), new file and new directory:
  - Each is refused with an error notification, **no filesystem change at all**
    (asserted by comparing a directory listing before and after), and the app
    stays up.
  - The report's exact reproductions: renaming `food` to `sub/food2` leaves
    `food.md` present **with its original header** — this is the half that
    regressed the header today; renaming to `../outside` leaves the file in the
    tree; a new file named `a/b` does not end the session.
  - A rename that fails at the `rename()` call itself (parent made read-only)
    notifies and leaves the header unchanged.

## 5. #9 — the missing editor

- `inspect._open_md`: `shutil.which("nvim")` first; when `None`,
  `notify(f"nvim is not installed{hint}.", severity="warning")` using
  `platform.install_hint("nvim")`, and return before `suspend()`, before the
  `stat`, and before any write.
- The `subprocess.run` call is wrapped in
  `try/except (OSError, subprocess.SubprocessError)` → notify, with the mtime
  comparison and the autocompile skipped on that path.
- Tests (`test_tui_inspect_tree.py`), the report's regression line — missing
  editor at action time:
  - `which` patched to `None`: `Enter` in MD mode notifies, the screen is still
    usable (the tree still has focus and responds), the file's mtime is
    unchanged, and no compile worker is started.
  - `subprocess.run` patched to raise `FileNotFoundError`: same outcome, and the
    TUI is not left suspended.
  - With an editor present, today's behaviour is unchanged (existing tests).

## 6. Docs

- `specs/current/design.md`:
  - the *Names the app refuses* subsection (created by M1) gains Inspect Tree's
    path-prompt rules, stated as one list beside M1's category-name rules, with
    a sentence on why the two sets differ;
  - the *Inspect Tree's PDF preview pane* section gains the missing-editor
    message alongside the existing missing-poppler one;
  - two new cross-cutting subsections instead of a sentence under *Flat
    menus*, since #16 and #12 each hold on every screen rather than on the
    menus: *Text from the tree is shown as typed* (#16) and *Failures are
    reported, never fatal* (#12's Compile screen, CLI and PDF-mode `Enter`;
    #9; #14's filesystem errors).
- `specs/current/stack.md`: the PDF section gains "a compile failure is per
  file: the rest of the run continues, the successes are cached, and
  `idiomas compile` exits 1", and the TUI section a *User text reaches
  widgets through `literal()`* subsection saying why it is a `Text` rather
  than an escaped string.
- Update this milestone's three spec files as anything changes during
  implementation.
