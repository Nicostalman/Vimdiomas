# M2 · Crash-proofing — requirements

## Anchor (from the roadmap)

The second tier: every finding where ordinary input or an ordinary keystroke
takes the whole TUI down. None of these corrupt data; all of them end the
session, and two of them make a screen unopenable while the offending file
exists.

**Findings in scope:** #9, #12, #14, #16.

**Deliverable.**

- **Bracket text in a notebook is text, not markup** (#16). `[/]` in a
  translation crashes Inspect Tree's MD mode; a category named `Verbs [/x]`
  makes Entry unopenable; `[b]x[/b]` in a filename is silently shown as `x`.
  Every place user text reaches a widget — previews, tree labels, select
  labels, notifications — passes it as literal content rather than markup.
- **A compile failure is reported, not fatal** (#12). The notebook menu's
  Compile and Inspect Tree's PDF-mode `Enter` call into the compiler outside any
  handler, so one file that xelatex rejects ends the session and discards the
  cache entries for every file that had already rebuilt in that run. Failures
  become per-file: the rest keep compiling, the successes are saved, and the
  user is told which files failed and why. The `idiomas compile` CLI stops
  printing a raw traceback for the same reason.
- **A name prompt cannot write outside the tree** (#14). Rename, new file and
  new directory join their input straight onto a parent path, so `../outside`
  moves a file out of the tree and `sub/food2` crashes the app after having
  already rewritten the file's header. Path separators, `.`/`..` and edge
  whitespace are refused before anything touches the filesystem, and a header is
  only rewritten once the rename has succeeded.
- **A missing optional editor is a message** (#9). `doctor` calls Neovim
  optional; Inspect Tree's MD-mode `Enter` invokes `nvim` with no handler for
  its absence. The action reports that the editor is unavailable and leaves the
  screen usable and the file untouched.

**Done when.** Each of the four findings has a regression test; none of the
report's reproductions ends the session; a tree containing a file named
`[b]x.md` with `[/]` in a translation opens in both tree screens; a deliberately
broken file next to a good one leaves the good one compiled and the app running;
the dev confirms by hand; and the full test suite passes.

Backlog source:
[`../../guidelines/backlog.md`](../../guidelines/backlog.md)'s *Bug fixes*
section — "see the file bug-report" — so
[`../../guidelines/bug-report.md`](../../guidelines/bug-report.md) is the
requirement text, cited by finding number throughout.

## Depends on M1

M1 leaves behind two things this milestone builds on rather than duplicates:

- **`design.md`'s *Names the app refuses* subsection**, created by M1 for the
  category-name rules. #14's path-prompt rules are added to it, not to a second
  home.
- **`TextField`'s control-character sanitiser** (M1, #15). `PromptDialog` uses a
  plain `Input`, which M1 deliberately left alone as "M2's #14" — the name
  validation below is where that gap closes.

## Decisions from the spec conversation (2026-09-29)

| Decision | Rationale |
| --- | --- |
| **A partially-failed Compile shows a summary on the screen Compile already pushes.** `PlaceholderScreen` gains a failures section below the compiled list: each failed file by name, with the tail of pandoc's stderr | Dev's choice from three. The results screen already exists and is already where the user looks after a Compile; a notification cannot hold stderr, expires, and stacks up when several files fail. Nothing new to learn and nothing to dismiss before reading it. |

## Decisions taken while speccing (agent)

Everything below was delegated by the dev ("the feature spec for the bugs is up
to you, unless it's an undefined design decision").

### #16 — markup escaping

| Decision | Rationale |
| --- | --- |
| **One helper, not per-call-site escaping**: `idiomas.tui.screens.base.literal(text) -> str`, wrapping `textual.markup.escape` | The roadmap asks which. A helper is one place to change if Textual's markup rules move, one name to grep for when auditing whether a new screen is safe, and one thing to test. Per-site escaping is the version that silently grows a hole the next time a screen interpolates a filename. |
| **It returns an escaped `str`, not a `Content`/`Text` object** | The call sites are `Static.update`, `Tree.add`/`add_leaf`, `OptionList` option labels and `app.notify`, and they do not all accept the same rich type in the Textual version pinned here. A `str` works at every one of them, so there is a single rule — *user text goes through `literal()`* — rather than a per-widget lookup table. |
| **Every site the report names is covered, and so is every other site that interpolates user text**: Inspect Tree's MD preview and `pdftotext` fallback, its tree labels and its notifications; Entry's tree labels (file stems, category names) and its notifications; `SelectField`'s subtitle labels; `ConfirmDialog`'s and `PromptDialog`'s messages; `PlaceholderScreen`'s message; Browse's results | The report's own list ends with "Notification messages that interpolate hanzi or names deserve the same treatment". Fixing only the three reproduced crashes would leave the same bug behind under a different keystroke. |
| **Text the app itself composes is not escaped** — only the user-derived fragments inside it | `f"Delete {literal(name)}?"` keeps the app's own message intact and neutralises only what came from the tree. Escaping the whole string would be harmless today and wrong the first time a message wants styling. |
| **An audit test enumerates the call sites** rather than trying to prove the absence of unescaped ones | Proving a negative across a TUI is not something a test can do honestly. What it can do is assert each known site, which is what the report's regression line asks for. |

### #12 — per-file compile

| Decision | Rationale |
| --- | --- |
| **`compile_all` returns a `CompileReport`**, not a `list[Path]`: `compiled: list[Path]` and `failed: list[CompileFailure]`, where `CompileFailure` is `(source: Path, message: str)` | The callers need to distinguish the two outcomes, and a structured result is also what M4's single *Compile* option needs to "report what it did". A sentinel inside the existing list would not survive that. |
| **The loop never raises for a per-file failure.** `subprocess.CalledProcessError` and `OSError` are caught per file, recorded, and the loop continues | The report's own suggested fix. |
| **The cache is saved in a `finally`**, so a success recorded before any later failure — or before an unexpected exception — is kept | The report notes `compile_cache.json` was not written at all in its reproduction "even though an earlier file had already been rebuilt during that run". Saving in `finally` covers both the caught case and anything not anticipated. |
| **`message` is the last 10 non-empty lines of the subprocess's stderr**, decoded as UTF-8 with `errors="replace"`, or `str(exc)` when there is none | xelatex's useful part — the `! Undefined control sequence` block and the line it points at — is at the end. A full xelatex log is hundreds of lines and would bury the filename list above it. The count is a module constant so it is one edit if it proves wrong in hand-testing. |
| **Inspect Tree's `_open_pdf` catches the same errors**, notifies, and does **not** open a viewer on a PDF that was not produced | Opening a stale or absent PDF after a failed compile would be a second, quieter wrong answer. |
| **The `idiomas compile` CLI prints failures to stderr and exits 1 if any file failed**, after printing the successes | A CLI that reports a failure and exits 0 is unusable in anything scripted. The successes still print, because they still happened. Note: the report marks this half as read-from-code, not reproduced — it is reproduced first, per `notes-sprint-6.md`'s first Assumption. |
| **`autocompile_one` is unchanged** | It already catches both exception types and notifies; it is the one path that was right. |

### #14 — name validation

| Decision | Rationale |
| --- | --- |
| **A name is refused if** it is empty after stripping; differs from its own stripped form (edge whitespace); contains `/`, `\`, `os.sep` or `os.altsep`; contains a NUL or any other C0 control character; or is `.` or `..` | Exactly the set that makes `parent / name` mean something other than "a child of parent". The roadmap's own list, plus NUL, which `pathlib` raises on rather than refusing cleanly. |
| **Edge whitespace is refused, not trimmed** | The roadmap says refused. A silently trimmed name is a file the user cannot find by the name they typed, which is the same class of surprise as the bug. |
| **`validate_name` lives in `idiomas.store`**, returning `str | None` (an error message, or `None`) | `store.py` is already the module that owns what a path in the tree is (`walk`, `is_grammar`). A new module for one function would be a worse trade. |
| **It is *not* shared with M1's category-name rules** — the roadmap's open question, answered **no** | They constrain different things. A category name is heading text: `C:\new words` and `Food/Drink` are legitimate categories (M3's #13 is about *rendering* them, not forbidding them), while both are impossible filenames. A file may legitimately be called `Tags`, which M1 forbids as a category. Sharing code would mean one of the two rule sets getting constraints it has no reason for. What *is* shared is `design.md`'s one *Names the app refuses* subsection, which states both. |
| **Refusal is an `app.notify` at `error` severity** naming the rule that was broken, and nothing touches the filesystem | The app's existing shape for a refused name in this screen (`"{name} already exists."`). |
| **The header is rewritten only after the rename succeeds**, on the new path | The report's own fix. Today `_retitle` writes `# sub/food2` into a file that then fails to move, leaving a header that matches no filename — which M9 will later surface as a warning on a file the user never edited. |
| **Every filesystem call in the three handlers is wrapped in `try/except OSError`**, reported by notification | Validation cannot cover a permissions error, a full disk or a race. The screen stays up regardless. |
| **New directory creates under the cursor's directory**, matching `m` (new file), rather than always at the tree root | Not in the report, but `action_new_dir` uses `self.tree_root` while `action_new_file` uses `_target_dir_for_new_file()`, and the report's `n` reproduction is only reachable because of the asymmetry. Flagged to the dev in the PR as a small behaviour change inside the finding's own handler rather than smuggled in silently; if they would rather keep it root-only, the validation still stands. |

### #9 — the missing editor

| Decision | Rationale |
| --- | --- |
| **`shutil.which("nvim")` is checked before `self.app.suspend()`**; if it is absent, notify and return | Suspending the TUI and then failing leaves the terminal to be restored on the way out of an exception — checking first means the screen never goes away at all. |
| **The message carries the platform's install hint** via the existing `platform.install_hint("nvim")`, the same way Inspect Tree's missing-poppler message already does | There is already a convention for "an optional dependency is missing"; this is the second user of it, not a new one. |
| **`subprocess.run` is still wrapped in `try/except (OSError, subprocess.SubprocessError)`** | `which` succeeding does not guarantee the exec does — a broken symlink, a permissions change between the two calls. Cheap, and it is the actual guarantee the done-when asks for. |
| **The file is not read or written on this path**, and the mtime comparison is skipped entirely when the editor never ran | "leaves the screen usable and the file untouched". |

## Corrections made at the start of implementation (2026-09-29)

Three decisions above did not survive contact with the code once the branch
was opened. Each row replaces the one it names; the originals stay above so
the reasoning that was overturned is still on record.

| Correction | Replaces | Why |
| --- | --- | --- |
| **`literal(text)` returns a `rich.text.Text`, not an escaped `str`**, and notifications that carry user text pass `markup=False` instead | #16's *returns an escaped `str`* row | Checked against Textual 8.2.8: no string escape round-trips a backslash. `textual.markup.escape("a\\[b]")` renders as `a\\[b]`, and a name ending in `\` — a legal filename on macOS and Linux — renders with it doubled, through both Textual's parser and Rich's (which `Tree` labels go through, not Textual's). A `Text` never reaches a markup parser, so it is exact by construction. Every site this milestone touches accepts one: `Static`/`Static.update`, `Tree.add`/`add_leaf` (whose `process_label` passes a `Text` through untouched) and `Option`. `app.notify` only takes a `str`, but has its own `markup=False`. |
| **The whole message is literal, not just its user-derived fragments** | #16's *text the app itself composes is not escaped* row | With `Text` there is no fragment-level escaping to do: a `Text` is literal throughout. No screen in the app uses markup styling today (checked), so nothing is lost. If one ever does, it builds a `Text` with styled spans, which is how Rich composes styled and literal text anyway. |
| **`PromptDialog`'s initial value is not touched** | #16's *`ConfirmDialog`'s and `PromptDialog`'s messages* row (the `PromptDialog` half) | Its value goes into an `Input`, which never parses markup — escaping it would put backslashes into the name the user is editing. Its label is app text. `ConfirmDialog`'s message, which does interpolate names, is covered. |
| **New directory stays at the tree root** | #14's *new directory creates under the cursor's directory* row | The dev's own Sprint 3 backlog: "Directories can not be nested, so where the user is standing does not matter." Root-only was a decision, not an asymmetry, and `validate_name` refusing `/` keeps it enforced. The row itself allowed for this ("the validation still stands"). The report's `n` reproduction (`../x`) is reachable at the root, so it is still fixed and still tested. |

## Context

- **`textual.markup.escape`** inserts a backslash before an opening `[`, which
  Textual's markup parser consumes and renders as a literal `[`. It is the
  documented counterpart to the parser that raises `MarkupError` today.
- **`main_menu._run_compile`** calls `compile_all` directly in the event
  handler and pushes `PlaceholderScreen` with a joined path list. Both the
  `compile` and `compile_force` options route through it — M4 merges them, and
  keeping the summary inside this one method is what makes that merge a
  deletion rather than a rewrite.
- **`compile._save_cache`** runs once after the loop
  (`compile.py:244`), which is why a mid-run failure loses every stamp already
  earned in that run.
- **`inspect.action_rename`'s file branch** does `_retitle` → `write_text` →
  `rename`, in that order. The first two succeed and the third raises, which is
  the "header is already `# sub/food2`" half of #14.
- **`inspect.action_new_dir`** joins onto `self.tree_root`;
  `action_new_file` joins onto `_target_dir_for_new_file()`. The report marks
  the new-directory half of #14 as read-from-code rather than reproduced.
- **`doctor.py`** already registers Neovim as an optional check, which is what
  makes #9 a contradiction rather than a missing feature: the app states the
  dependency is optional and then requires it.
- The report's findings were reproduced against commit `aa11572`. Per
  `notes-sprint-6.md`'s first Assumption, each is **re-reproduced before being
  fixed** — including the two halves the report itself marks as read-from-code
  (the CLI traceback in #12, new-directory in #14).

## Out of scope

- **M3's compile-output findings.** #12 makes a failure survivable; #13 and #5
  are what stop the failures from happening in the first place, and they are
  M3. A file that fails to compile today will still fail after this milestone —
  it just will not take the session with it.
- **`compile_all`'s staleness cache.** #11 is M3. This milestone only changes
  *when* the cache is saved, not *what* is recorded in it — M3 then moves the
  recording into `compile_file` and simplifies what is written here.
- **Surfacing warnings.** M9.
- **Escaping user text for the *PDF*.** That is `_escape` and M3's #13 and #10;
  `literal()` is about Textual widgets only, and the two must not be confused
  for each other.
- **Renaming across directories**, which `validate_name` now forbids. Moving a
  file between directories from the app is not a feature today and is not one
  this milestone adds; `nvim` and the shell cover it.
- **Making `nvim` configurable.** The editor stays `nvim`; this milestone only
  stops its absence from being fatal.
