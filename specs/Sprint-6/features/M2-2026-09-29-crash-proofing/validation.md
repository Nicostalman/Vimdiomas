# M2 · Crash-proofing — validation

Grounded in the roadmap's done-when condition, made concrete.

## Regression coverage, finding by finding

Each row is the report's own *Regression coverage* line and the test that
satisfies it. Every one is **written failing first**, against the current code,
to confirm the finding is still live — including the two halves the report marks
as read-from-code rather than reproduced.

| # | Report's coverage line | Test |
|---|---|---|
| 9 | missing editor at action time; verify the screen remains usable and the source file is untouched | `test_tui_inspect_tree.py`: `which` → `None`, and `subprocess.run` raising; mtime asserted unchanged, tree still responsive, no autocompile worker started |
| 12 | one good and one failing file through menu Compile, Inspect open, and the CLI; assert the app stays up, the failure is reported, and the good file's stamp is saved | `test_compile.py` (the report, the cache), `test_tui_main_menu.py` (the summary screen), `test_tui_inspect_tree.py` (`Enter` on a failing file), `test_main.py` (stderr + exit 1) |
| 14 | `/`, `..` and `../x` through rename (file and directory), new file and new directory; assert a user-visible error and no filesystem change | `test_store.py` (`validate_name`) and `test_tui_inspect_tree.py` (all four prompts — rename a file, rename a directory, new file, new directory — × eight inputs: the report's `/`, `..`, `../x`, plus `sub/food2`, `a/b`, `.` and edge whitespace on either side; the listing compared before and after) |
| 16 | `[/]`, `[/x]` and `[b]x[/b]` in file content, file names, category names and subtitle names, through Entry, Inspect Tree (both modes) and `SelectField` labels | `test_tui_inspect_tree.py`, `test_tui_entry_screen.py`, `test_tui_browse_screen.py`, `test_tui_panels.py`; plus `literal()` unit-tested on `a\[b]` and `trail\`, the backslash cases a string escape gets wrong |

## Automated

- `.venv/bin/python -m pytest -q` — the full suite passes, including the
  integration tests that use real pandoc/xelatex.
- **None of the report's reproductions ends the session.** Each is run as a
  headless Textual test that asserts the app is still running afterwards, not
  merely that no exception propagated:
  - #16's three: `[/]` in a translation (Inspect Tree, MD mode), `Verbs [/x]` as
    a category name (Entry opens), `[b]x` as a filename (listed in full).
  - #12's two: menu Compile with a failing file, and `Enter` in PDF mode on one.
  - #14's three: `sub/food2`, `../outside`, and a new file named `a/b`.
  - #9's one: MD-mode `Enter` with no `nvim`.
- **The done-when's two composite cases**, each its own test:
  - a tree containing a file named `[b]x.md` with `[/]` in a translation
    **opens in both tree screens** — Entry and Inspect Tree — and the file is
    selectable in each;
  - a deliberately broken file next to a good one **leaves the good one
    compiled and the app running**: the good PDF exists, its stamp is in the
    cache, the failure is named on screen, and the session is alive.
- **No filesystem change on a refused name.** The tree's full recursive listing
  — from the tree's *parent*, since `..` is how a name escapes — and every
  file's bytes are captured before and compared after, for all 32
  refused-input cases (four prompts × eight inputs).
- **A failed rename leaves the header alone.** The `# food` header is asserted
  byte-identical after `sub/food2` is refused *and* after a `rename()` that
  fails at the syscall.

## Manual, by the dev

Against a scratch copy of the tree, not the real one — several of these create
files that deliberately break.

- [ ] **#16, the two crashes.** In a scratch file, hand-edit a translation to
      contain `to [/] test`. *Inspect tree* → highlight it → `tab` to MD mode:
      the preview shows the text with the brackets, and the app stays up. Add a
      category named `Verbs [/x]` by hand; open *Enter vocabulary*: it opens, and
      the category shows with its brackets.
- [ ] **#16, the silent one.** Create a file named `[b]x.md`. Both trees list it
      as `[b]x`, not `x`.
- [ ] **#12.** Put a file with a category named `C:\new words` next to a normal
      one. Notebook menu → *Compile*. The app stays up; the results screen lists
      the good file under *Compiled* and the bad one under *Failed* with an error
      message you can actually read. Run *Compile* again: the good file is
      skipped, the bad one is retried.
- [ ] **#12, Inspect Tree.** Delete the bad file's PDF if it has one, then press
      `Enter` on it in PDF mode: an error notification, no viewer opens, the
      screen still works.
- [ ] **#12, the CLI.** `idiomas compile` over the same tree: the good file is
      reported compiled, the failure is printed, and `echo $?` is `1`.
- [ ] **#14.** In *Inspect tree*: `r` on a file → `sub/food2` → refused with a
      message, and the file's header is **unchanged** when you open it in MD
      mode. `r` → `../outside` → refused, and the file is still in the tree. `m`
      → `a/b` → refused. `n` → `../x` → refused. `r` → a name with a trailing
      space → refused.
- [ ] **#14, normal use still works.** Rename a file to an ordinary new name: the
      file moves, the header follows it, and the PDF rebuilds.
- [ ] **#9.** If `nvim` is on your `PATH`, temporarily rename it (or run this
      step in the Linux container from Sprint 5 M7 without it installed). MD mode
      → `Enter`: a message says the editor is unavailable and how to install it;
      the screen is still usable and the file is untouched.
- [ ] **Nothing else changed.** Ordinary entry, ordinary compile, ordinary
      preview — all as before.

## Merge bar

All automated checks pass, the four regression tests above are present and
green, none of the report's reproductions ends the session, the two composite
done-when cases pass, and the dev confirms the manual list.
