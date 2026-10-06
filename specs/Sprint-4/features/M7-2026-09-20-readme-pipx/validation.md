# M7 · README and install — validation

The acceptance bar for this branch. The roadmap's done-when condition is:

> The README's install section can be followed start to finish by someone who
> has never used a virtualenv; following it produces a working `idiomas` on
> `PATH` with no manual `ln` or `PATH` edit at all in the common case; a
> second wizard run never duplicates the `PATH` line; the wizard's new step is
> skipped cleanly when the link is already in place; quitting the wizard
> before the end still writes nothing, symlink and shell config included; and
> the full test suite passes.
>
> Amended 2026-09-20: the first implementation only reported a missing `PATH`
> entry rather than fixing it, matching the requirements as first written. The
> dev asked for it to be automatic ("is this line mandatory? you should check
> for it and add it"), which is what the rows below now check.

Made concrete below.

## A. The documented install actually works

Run from a scratch directory, from a **clean clone**, with the dev's real
config moved aside (a copy, never the live file):

| # | Check | Passing result |
|---|---|---|
| A1 | Clone, venv, install — exactly the README's commands | Each exits 0; no step needed a command the README doesn't give |
| A2 | First run by full path | `<clone>/.venv/bin/idiomas` opens the wizard, since no config exists |
| A3 | Walk the wizard to the end | Finishes; config written to `~/.config/idiomas/config.toml`; `tree-<Language>` folders created under the chosen root |
| A4 | The symlink | `~/.local/bin/idiomas` exists, is a symlink, and resolves to the clone's `.venv/bin/idiomas` |
| A5 | Plain `idiomas`, from outside the repo, in a **new shell** | Opens the app against the written config. No manual `ln`, no manual `PATH` edit — the wizard's own shell-config write is what makes the new shell find it |
| A6 | `cd ~ && idiomas doctor` | Prints its checks, each `[required]` or `[optional]`; no traceback |
| A7 | `cd ~ && idiomas compile` | Compiles or reports up to date — never a missing-template or missing-config error |
| A8 | `pyproject.toml` unchanged | If a change was needed, it is recorded in `requirements.md`'s Decisions table and A1–A7 were re-run |

A7 depends on pandoc/xelatex/xeCJK being installed. A genuinely missing
required tool satisfies A7 by failing on *that* tool with doctor's message —
not on an import, config or template error.

## B. The new wizard step behaves in every case

One row per case in `requirements.md`'s table. Automated where the row is
logic, by hand where it is a screen.

| # | Case | Passing result |
|---|---|---|
| B1 | No link exists | Created; reported as created |
| B2 | `~/.local/bin` doesn't exist | Directory created, then the link |
| B3 | Link already correct (`idiomas wizard` re-run) | Reported as already linked; the existing link is **not** recreated or rewritten; `Finish` is not blocked |
| B4 | Something else occupies the path | **Not overwritten.** The step reports what's there and the command to replace it by hand |
| B5 | Started as `python -m idiomas` | Linking skipped with an explanation; wizard still finishes |
| B6 | Off macOS | Linking skipped; wizard still finishes |
| B7 | Link creation fails | Reported; **config and trees still written** |
| B8 | `~/.local/bin` already on `PATH` | Reported as ready; shell config **not touched** |
| B9 | `~/.local/bin` not on `PATH`, and the shell config doesn't mention it | `Finish` **appends** the `export` line to the real shell config file; report names the file and the line before it happens |
| B10 | Not on `PATH`, but the shell config **already has the line** (re-run) | **Not appended a second time.** Reported as already present, needing only a new terminal |
| B11 | The shell-config write fails (permissions) | Reported, with the line to add by hand; **config and trees still written** |

## C. Quitting still writes nothing

| # | Check | Passing result |
|---|---|---|
| C1 | `q` out of the new final step | No config written, no tree folders created, no symlink created, **and no shell-config write** |
| C2 | `q` from the new step goes back | Lands on the last input-method step with its answers intact |
| C3 | Abort from step 1 | Unchanged from M5: confirm dialog, then nothing written |

## D. Only the one PATH line is ever written to the shell config

The hard line from `requirements.md`, updated for the automatic write. After
every run in A and B:

| # | Check | Passing result |
|---|---|---|
| D1 | The shell config named by `shell_config_path()` | Changes **only** when B9/B11 apply, and then only by one appended line plus a one-line comment; every byte that was already in the file is still there, unchanged, in the same order |
| D2 | Every *other* shell config (`~/.bashrc`, `~/.profile`, `~/.zprofile`, or `~/.zshrc` when a different one was named) | Unmodified — compare mtime and contents before and after |
| D3 | Nothing outside `~/.local/bin`, the shell config, the tree root and `~/.config/idiomas/` was created or changed | Verified against what the run touched |
| D4 | Running the wizard (or the flow) a second time with the line already present | The file is byte-for-byte identical to after the first run — confirms `directory_already_in_shell_config()` is checked, not just skipped by luck |

## E. The README says nothing false

Read top to bottom. Nothing that was true only before Sprint 3 or Sprint 4
survives.

| # | Check | Passing result |
|---|---|---|
| E1 | No `source/` + `notebook/` two-tree model | The tree section describes `<root>/tree-<Language>/`, `.md` and `.pdf` side by side |
| E2 | No `python -m idiomas` as the user-facing invocation | Commands are `idiomas`, `idiomas compile`, `idiomas doctor` |
| E3 | No `pip install -e` presented as *the* install | It appears only under Developing |
| E4 | No `pipx` | Gone from the file entirely |
| E5 | Links resolve | `mission.md`, `stack.md`, `design.md` and the roadmap point into `specs/current/` and `specs/Sprint-4/`; every relative link opens the file it names |
| E6 | First run is the wizard | The wizard's real steps in the order `wizard.py` runs them, ending with the `PATH` step, and that it runs only once |
| E7 | Config location stated | `~/.config/idiomas/config.toml` |
| E8 | `idiomas wizard` absent | Not documented anywhere |
| E9 | File format matches the code | Header repair, preserved category order, tab-separated fields, indented italic note, `## Tags` last and omitted when empty, numbered pinyin — re-checked against `parser.py`/`writer.py` |
| E10 | Dependencies marked required vs optional | Matching `doctor.py`: required pandoc, xelatex, xeCJK, Heiti SC; optional `macism`, `nvim` |
| E11 | `doctor` framed as troubleshooting | Not presented as a required step before first run |
| E12 | Every command in it was run | Each appears in group 3's recorded output |

## F. It reads for the intended audience

The README's reader is someone who has never made a virtualenv — the dev's own
stated reason for raising this milestone. So:

| # | Check | Passing result |
|---|---|---|
| F1 | No unexplained step | Every command has a plain-words line saying what it does |
| F2 | No assumed tooling | Nothing requires knowing what a venv, a console script or `PATH` is before reading |
| F3 | The full-path first run is explained, not just given | The reader is told *why* the first run is different from every one after it |

## G. Nothing regressed

```sh
pytest
```

Passes, including the new `tests/test_install.py` and the wizard tests. No
existing test changed to accommodate the new step except where the step
genuinely moved behaviour (`_finish()` off `InputMethodScreen`), and any such
change is visible in the diff rather than buried.

## H. The dev's own pass

Not done until the dev says so. They read the README as a reader, and run the
install themselves if they want the stronger check. Anything they ask for loops
back through `plan.md` before this file is re-checked.

## I. The machine is left clean

The scratch clone removed and `~/.local/bin/idiomas` deleted, so the dev's
existing `.venv` setup is what remains and no stale link shadows it on `PATH`.
The dev's real `~/.config/idiomas/config.toml` is back exactly as it was.

---

## Verification record (2026-09-20)

What was actually run on this branch, and what it showed.

**A — the documented install.** A clean `git clone` of this branch into a
scratch directory, then `python3 -m venv .venv` and `.venv/bin/pip install .`,
exactly as the README's three steps give them. Results:

- The console script appeared at `.venv/bin/idiomas`.
- `importlib.resources.files("idiomas")/"templates"/"xecjk.tex"` resolved
  **inside the venv's site-packages**, not the clone's source tree — M4's
  packaging holds under a real install.
- `idiomas doctor`, run from `~`, reported all six checks ok.
- `idiomas compile`, run from `~`, reported "Chinese: everything is up to
  date" against the real configured tree.
- `pyproject.toml` needed **no change** (A6/A8), as the roadmap expected.
- The README's update path (`git pull` + reinstall) ran clean.
- `doctor` exited 1 with a required tool hidden from `PATH`.

**B — the link, against the installed package.** Run under a throwaway `HOME`,
with `sys.argv[0]` set to the clone's console script: `link_status()` returned
`ready`, `create_link()` created the symlink, and the created link *ran*
(`idiomas doctor` through it). Afterwards the throwaway `HOME` contained
`.local/bin/idiomas` and **nothing else** — no shell config was created (D1–D3).

The occupied case was confirmed against the dev's real machine without writing
anything: `link_status()` reported `occupied`, naming the existing
`~/.local/bin/idiomas` → repo-`.venv` symlink left over from M5's hand-linking
workaround. That is the state the dev's own hands-on run will start from.

**What could not be run here, and why.** The wizard's screens could not be
driven end-to-end as a user: this environment has no tty, so the real TUI
can't be launched (`script` fails with `tcgetattr/ioctl: Operation not
supported on socket`). The step's behaviour is covered by the ten new tests in
`tests/test_tui_wizard.py` instead, and the interactive walkthrough is the
dev's pass (H), which the roadmap always made the closing condition anyway.

**Corrections the check forced.** Three claims were written and then found
false before the README shipped:

- `tab` does **not** cross from Entry's tree to its form — `action_next_field`
  returns early unless a form field already has focus. The README now gives
  `esc` then `L`, which is the route that works.
- The `macism` install command was aligned to the one `doctor.py` itself
  prints (`brew install laishulu/homebrew/macism`).
- "It checks all of them for you" was overstated: the wizard cannot check
  Python, which is what runs it. Now "apart from Python itself".

**G — the suite.** 458 passed, up from 448 on `main`: ten new tests (nine in
`tests/test_install.py`'s file plus the PATH-step group in
`tests/test_tui_wizard.py`). Two pre-existing wizard tests changed, both
because behaviour genuinely moved: the input-method step's button now reads
`Next` rather than `Finish`, and the shared advance helper walks one step
further.

**I — the machine.** Scratch clone and throwaway `HOME` removed. The dev's
`~/.local/bin/idiomas`, `~/.zshrc`, `~/.zprofile` and
`~/.config/idiomas/config.toml` were all verified unchanged by mtime after
every run.
