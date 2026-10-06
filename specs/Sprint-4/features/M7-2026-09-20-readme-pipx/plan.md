# M7 · README and install — plan

Task groups in order; each depends only on the ones before it. The code comes
first and the README second, so the README documents behaviour that has
actually been run.

> **Amended 2026-09-20, after group 4 shipped.** Groups 1–5 below describe the
> first pass, which only *reported* a missing `PATH` line. The dev then asked
> for it to be added automatically ("is this line mandatory? you should check
> for it and add it"). Group 6 is that retrofit; it isn't folded back into
> groups 1–2 because that work already shipped and was reviewed — the
> amendment is additive, the way `plan.md` is meant to grow.

## 1. The link logic

A new `src/idiomas/install.py`, with no Textual in it — plain functions the
wizard step calls and the tests exercise directly.

1. `user_bin_dir()` in the platform layer: `~/.local/bin` on macOS, `None`
   elsewhere. Add it to `idiomas/platform/__init__.py`'s macOS branch, its
   no-op branch and `__all__`, following `cjk_font_installed`'s shape.
2. `console_script_path()` — the running console script, or `None` when the app
   wasn't started from one (`python -m idiomas`). From `sys.argv[0]`, resolved;
   `None` when it doesn't exist or isn't a file.
3. `link_status()` — inspect `<user_bin>/idiomas` without touching it, and
   return which of `requirements.md`'s cases applies: nothing there, already
   linked to this target, occupied by something else, no target to link, or
   unsupported platform.
4. `on_path(directory)` — is the directory on `PATH`, comparing resolved paths
   rather than raw strings, so `~/.local/bin` and `/Users/x/.local/bin` match.
5. `shell_config_hint()` — the shell config file to name and the exact `export`
   line to print. Name the file from `$SHELL`; fall back to `~/.zshrc` on
   macOS, whose default shell is zsh.
6. `create_link()` — `mkdir -p` the bin directory, then symlink. Returns what
   happened; raises nothing the caller must catch blind — a failed creation
   comes back as a reportable result, per the "still finish the wizard" rule.
7. Tests in `tests/test_install.py`: every case in `requirements.md`'s table,
   against a `tmp_path` bin directory with `user_bin_dir` monkeypatched. In
   particular: an existing correct link is reported as already linked and
   **nothing is rewritten**; an occupied path is **never** overwritten.

## 2. The wizard's final step

1. New `PathScreen(_WizardStep)` in `wizard.py`, pushed by the last
   `InputMethodScreen` instead of that screen calling `_finish()`.
2. Its content, per `requirements.md`: where the link goes, whether
   `~/.local/bin` is on `PATH` (with the exact line to add when it isn't), and
   what `Finish` will do. Titled and prompted like every other step (M5's
   bold-title + plain-language-prompt convention).
3. Move `_finish()` off `InputMethodScreen` onto `PathScreen`, and have it
   create the link before writing the trees and config. A link failure is
   reported and does not stop the write.
4. `q` on this step goes back to the last input-method step, writing nothing —
   M5's rule, now covering the symlink.
5. The "already linked" and "nothing to link" cases render as a plain statement
   with no scary wording; neither blocks `Finish`.
6. Tests: the step writes config **and** link on `Finish`; `q` out of it writes
   neither; a link failure still writes the config. Use the existing wizard
   tests' harness rather than inventing a second one.

## 3. Run it by hand, the way a user would

Before writing a word of the README, do what the README will tell the reader to
do — from a clean clone, so no `.venv`, `.egg-info` or untracked file from the
working tree can help it along.

1. `git clone` the repo into a scratch directory standing in for
   `~/.local/share/idiomas`.
2. Create the venv inside it, install the package into it.
3. With the dev's real config temporarily moved aside — a **copy** is what the
   wizard gets pointed at, never the live file (the notes' M6 row records what
   testing against the real one cost last time) — run the venv's `idiomas` by
   full path and walk the wizard to the end.
4. Confirm: the symlink appears at `~/.local/bin/idiomas`, plain `idiomas` then
   works from a directory outside the repo, and the `PATH` report was accurate.
5. Re-run `idiomas wizard` to exercise the "already linked" case.
6. Confirm `idiomas compile` and `idiomas doctor` work from outside the repo —
   the end-to-end proof that neither the config nor the packaged template
   depends on where the clone sits.
7. Record the exact commands and their output; they are what the README quotes.
8. Restore the dev's real config.

## 4. Rewrite `readme.md`

1. Re-read before describing: `__main__.py`'s subcommands, `config.py`'s schema
   and paths, the menus in `landing.py` / `main_menu.py` / `settings.py`, the
   wizard's steps in order, and `specs/current/design.md`'s navigation
   conventions.
2. Re-verify the file-format section against `parser.py` and `writer.py` —
   header repair, preserved category order, tab-separated entries, indented
   italic notes, `## Tags` last and omitted when empty, numbered pinyin.
3. Write the twelve sections from `requirements.md`, in that order.
4. The install section quotes the commands from group 3 verbatim, each with a
   plain-words line on what it does. No step assumed to be obvious.
5. Fix every stale link and every stale claim: `specs/current/` paths, the
   `tree-<Language>` layout, `idiomas` rather than `python -m idiomas`,
   `pip install -e` only under Developing.
6. Do **not** document `idiomas wizard`.

## 5. Check the rewrite against reality

1. Read the finished README top to bottom against what group 3 observed; every
   command in it must be one that was run.
2. Run the full test suite.
3. Clean up: remove the symlink and the scratch clone, so the dev's existing
   `.venv` setup is what remains and no stale copy shadows it on `PATH`.

## 6. Make the `PATH` fix automatic

Retrofit, per the dev's hands-on feedback after group 5 shipped: the reported
line wasn't enough, and it's genuinely mandatory for `idiomas` to be found.

1. `install.py`: `directory_already_in_shell_config(directory)` — read-only
   check of `shell_config_path()`'s contents, separate from `on_path()` (which
   only sees the running process's env, not a line a previous run already
   wrote to the file).
2. `install.py`: `ensure_on_path(directory)` — append `path_export_line()` to
   `shell_config_path()` only when `directory_already_in_shell_config()` says
   it isn't there yet; create the file if it's missing; never rewrite existing
   content; return a result the caller can report on failure without raising.
3. `wizard.py`'s `PathScreen`: call `ensure_on_path()` in `_on_finish()`,
   alongside `create_link()`. Both are attempted; either's failure is reported
   the same way, and the config/trees are written regardless.
4. `_path_note()`: before Finish, distinguish "will add this line" from
   "already in your config, just needs a new terminal" — using
   `directory_already_in_shell_config()`, not `on_path()`, so the message is
   accurate even in the same shell session that a previous run already fixed.
5. Tests: appending when absent, never duplicating when already present
   (byte-for-byte identical on a second run), creating the file when missing,
   a write failure still finishing the wizard and writing the config, and the
   pre-Finish report distinguishing "will add" from "already there".
6. `readme.md`: the wizard now fixes `PATH` itself; the manual `export` line
   stays only as a fallback for when it couldn't.
7. Update `requirements.md`, `validation.md` and the roadmap's M7 entry to
   record the reversal — done as part of this group, not deferred to hand-off.

## 7. Hand off

1. Commit the code, the README and this spec folder.
2. Hand to the dev: they read the README as a reader, and run the install
   themselves if they want the stronger check.
3. Iterate on their feedback, updating these three files as anything changes.
4. On their go-ahead: PR, squash-merge into `main`, delete the branch locally
   and on the remote, and settle this milestone's entries in
   `../../guidelines/notes-sprint-4.md` — including correcting the existing M7
   row, which still describes the pipx plan.
5. Report that Sprint 4's last milestone is merged and that `changelog` /
   `sprint-start` are the next steps.
