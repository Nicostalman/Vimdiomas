# M7 · README and install — requirements

> **Folder name.** This folder is `M7-2026-09-20-readme-pipx`, named before the
> milestone's spec conversation reversed the install path away from `pipx`. The
> name is left as it is rather than renamed mid-branch; the milestone is
> *README and install*, as the roadmap now calls it.

## Anchor (from the roadmap)

**Deliverable.**

- **The README documents a `git clone` install**, spelled out step by step for
  a reader who doesn't know Python tooling: clone to `~/.local/share/idiomas`,
  create a virtualenv inside the clone, install the package into it, then run
  the app once by its full path to reach the wizard.
- **The wizard puts `idiomas` on `PATH` itself**, as its final step: it
  symlinks the running console script into `~/.local/bin`.
- **`~/.local/bin` not being on `PATH` is fixed automatically**, by appending
  one line to the shell config — reversed same-day from "reported, not
  silently fixed"; see the Decisions table below.
- **The config is still written only at the end** — M5's "quitting writes
  nothing" rule now covers the symlink and the shell-config write too.
- **A full README rewrite**, not just its install section.
- **`pipx` is not the documented path**, nor `make install`, nor `curl | sh`.
- No change to `doctor.py`, the notebook screens, or the file format. The
  wizard gains exactly one step.

**Done when.** The README's install section can be followed start to finish by
someone who has never used a virtualenv; following it produces a working
`idiomas` on `PATH` with **no manual `ln` or `PATH` edit at all** in the common
case; a second wizard run never duplicates the `PATH` line; the wizard's new
step is skipped cleanly when the link is already in place; quitting the wizard
before the end still writes nothing, symlink and shell config included; and
the full test suite passes.

(Sources: [`../../roadmap-sprint-4.md`](../../roadmap-sprint-4.md) M7, as
rewritten 2026-09-20; [`../../guidelines/notes-sprint-4.md`](../../guidelines/notes-sprint-4.md)
Decisions — the M7 rows.)

## Scope

In scope:

- A new, final wizard step that creates the `~/.local/bin` symlink and reports
  `PATH` status.
- Moving the wizard's `_finish()` (tree folders + config write) onto that new
  last step, so "the last step writes everything" keeps holding.
- A new `idiomas/install.py` holding the link logic, with the user-bin
  directory coming from the platform layer.
- A full rewrite of `readme.md` against the app as it stands at the end of
  Sprint 4.
- Tests for the link logic and for the new step's behaviour.

Explicitly out of scope:

- **Touching anything in the shell config beyond the one `PATH` line**
  `ensure_on_path()` appends. No reordering, no rewriting, no other edit —
  see the reversed decision below.
- `pipx`, `make install`, `curl | sh`, brew packaging, tagged releases.
- Any change to `doctor.py`, the notebook screens, `parser.py`/`writer.py`, or
  the file format.
- Windows and Linux link creation. The platform layer gets the seam; only
  macOS is implemented, consistent with M4.
- Making the GitHub repository public — the dev's own step, later. The README
  is written as though it is.
- An uninstall command or a documented uninstall procedure beyond deleting the
  clone and the symlink.

## Decisions taken in this milestone's spec conversation

Taken on 2026-09-20. The first two reverse the roadmap's original M7.

| Decision | Rationale |
| --- | --- |
| **`git clone` replaces `pipx` as the documented install** | Dev's call, in their words: "ignore the pipx thing, a git clone makes me happy." The original entry's argument against `make install` and `curl \| sh` is unaffected and still recorded in the roadmap; what changed is that `pipx` lost too. |
| **The wizard adds `idiomas` to `PATH` automatically**, rather than the README instructing a manual `ln -s` | Dev's call: "ideally it should be added to the path automatically through the wizard." Reverses the original entry's "no change to the wizard (M5)". |
| **The first run is still by full path — the chicken-and-egg is documented, not solved** | The wizard is only reachable by running the app, so it cannot put the app on `PATH` *before* the first run. The README says to run `~/.local/share/idiomas/.venv/bin/idiomas` once; the wizard makes every run after that plain `idiomas`. Raised with the dev when they asked for the wizard to handle it; accepted. |
| **Dependencies go in a virtualenv inside the clone** (`.venv/`), created by the user following the README | Dev's choice from three options. Self-contained, survives a `git pull`, and sidesteps PEP 668 — a plain `pip install --user` is refused outright by Homebrew and system Pythons, which is exactly the reader this README is written for. |
| **`~/.local/share/idiomas` is the suggested clone location** | Dev asked why that path specifically, then confirmed it ("yes do it in local share") once it was the XDG convention for application data rather than an arbitrary pick. Stated in the README as a suggestion — nothing has depended on where the code lives since M4 — so a reader who already keeps code elsewhere isn't told they're wrong. |
| **The symlink goes in `~/.local/bin`**, not a `PATH` entry pointing at the venv and not a shell alias | Dev's choice. One file, easy to find and delete. Putting the whole venv on `PATH` would shadow the system `python` and `pip`; an alias isn't a real `PATH` entry, so nothing but an interactive shell would find it. |
| ~~`~/.local/bin` missing from `PATH` is reported with the exact line to add, never written~~ — **reversed same day** | Dev's original choice against the wizard editing `~/.zshrc`, on the grounds that a shell config is the user's own file and an installer's edit is hard to find later. Reversed hours later, after seeing the README's manual step, in the dev's words: "is this line mandatory? you should check for it and add it." It is mandatory — the symlink alone doesn't make `idiomas` findable without it — so the wizard now appends `path_export_line()` to `shell_config_path()` itself via `install.ensure_on_path()`, guarded against duplication by checking the file's own contents first (`directory_already_in_shell_config()`), not just the running process's `PATH` env var. Nothing else in the file is touched, and a write failure is reported the same way a link failure already was — the config and trees still get saved. |
| **`idiomas doctor` stays, documented as troubleshooting** | Dev asked whether doctor has any use outside the wizard. It does: `doctor.run()` has two callers — the wizard's step 1 and the CLI subcommand — and the wizard runs once, ever, so afterwards the subcommand is the only way to diagnose a dependency that broke later. Framed as "if something stops working", not as a required pre-flight step. No code change. |
| **The README is rewritten in full** | Carried over from this conversation's first round, before the pipx reversal, and unaffected by it. `readme.md` predates Sprint 3 and Sprint 4: it describes the `source/` + `notebook/` two-tree model, invokes the app as `python -m idiomas`, links `mission.md`/`stack.md`/`roadmap.md` at the repo root, and knows nothing about the config, the wizard, Settings or Inspect Tree. |

## Behaviour of the new wizard step

The step is shown after the last input-method step and before the wizard
exits. It is the step that writes.

**What it reports**, in this order:

1. Where the link will be created: `~/.local/bin/idiomas`.
2. Whether `~/.local/bin` is on `PATH`. If it isn't, and the shell config
   doesn't already mention it, what line `Finish` will add and to which file.
   If the config already has the line (an earlier wizard run) but the running
   shell hasn't picked it up yet, it says so instead of promising to add it
   again.
3. What happens on `Finish`.

**Cases it has to handle.** Each is settled here rather than left to the
implementation:

| Case | Behaviour |
| --- | --- |
| No link exists, `~/.local/bin` writable | Create it. Report success. |
| `~/.local/bin` doesn't exist | Create the directory, then the link. |
| A link already exists pointing at the same target | Nothing to do; report it as already linked. Not an error — this is the `idiomas wizard` re-run case. |
| A link exists pointing somewhere else, or a regular file is in the way | **Do not overwrite.** Report what's there and the command to replace it by hand. Another program's `idiomas`, or a second checkout, is not this wizard's to clobber. |
| The app wasn't started from a console script (`python -m idiomas`, so there's no script to link) | Skip linking. Explain that the app was started a way that has nothing to link, and that the README's install produces one. |
| Off macOS (no supported user-bin convention wired up) | Skip linking, say so, and let the wizard finish. Same shape as every other platform no-op since M4. |
| Link creation fails (permissions, read-only home) | Report the error and **still finish the wizard** — the config and trees are the point; the link is a convenience. |
| `~/.local/bin` not on `PATH`, and the shell config doesn't mention it | Append `path_export_line()` on `Finish`. |
| `~/.local/bin` not on `PATH`, but the shell config **already** has the line | Nothing to write — a previous wizard run (or a hand edit) already covers it; the running shell just hasn't picked it up. Report that a new terminal is what's needed. |
| The shell-config write fails (permissions, read-only home) | Report the error and the line to add by hand; **still finish the wizard**, same as a failed link. |

**What it must not do:** write anything to the shell config beyond the one
`export`/`fish_add_path` line, ever duplicate that line, touch any file other
than `~/.local/bin/idiomas` and the shell config named by
`shell_config_path()`, overwrite anything, or block the wizard from finishing.

**Ordering.** `_finish()` — `root.mkdir`, the per-language `tree-<Language>`
folders, `save_config`, `app.exit(config)` — moves from `InputMethodScreen`
onto this step, joined by the link creation. M5's rule that quitting before the
last step writes nothing then continues to hold unchanged, with the symlink
covered by it: `q` out of this step and nothing has been created, linked or
saved.

## Context

- **`pyproject.toml` is already in shape** (M4): `[project.scripts] idiomas =
  "idiomas.__main__:main"` is what produces the venv's `bin/idiomas` script
  that gets linked, and `[tool.setuptools.package-data]` ships
  `templates/*.tex`. No change expected.
- **The symlink target** is the running console script. `sys.argv[0]` gives it
  when the app was launched as `idiomas`; the "no console script" case above is
  what `python -m idiomas` hits.
- **The platform layer** (M4) covers "only what's actually OS-specific". The
  `~/.local/bin` convention and symlink creation are POSIX, so the bin
  directory comes from the platform layer while the decision logic — is it
  already linked, is it on `PATH`, is something in the way — stays shared in
  `install.py`.
- **`idiomas wizard`** is the dev-only escape hatch hidden from `--help` (M5).
  Not documented in the README, but it is the main way the new step's
  "already linked" case will be exercised by hand.
- **The tree layout the README must describe** is Sprint 3 M1's: one tree per
  language at `<root>/tree-<Language>/`, `.md` and `.pdf` side by side.

## What the rewritten README must cover

Sections, in order, each accurate as of the end of Sprint 4:

1. **What Idiomas is** — the pitch, linking
   [`specs/current/mission.md`](../../../current/mission.md),
   [`stack.md`](../../../current/stack.md) and
   [`design.md`](../../../current/design.md) at their real paths.
2. **Requirements** — macOS, Python 3.14+, pandoc, TeX Live + `xeCJK`, optional
   `macism` / `nvim`, marked required vs optional the way `doctor` labels them.
3. **Install** — clone, venv, install, first run by full path. Every command
   given in full, with what it does in plain words, for a reader who has never
   made a virtualenv.
4. **First run** — the wizard: what it asks, that it puts `idiomas` on `PATH`
   at the end, that it runs only once, and what to do if it says `~/.local/bin`
   isn't on `PATH`.
5. **Usage** — `idiomas`, `idiomas compile`, `idiomas doctor`.
6. **The notebook tree** — one tree per language, `.md`/`.pdf` side by side.
7. **Getting around** — the navigation model, briefly, pointing at
   [`design.md`](../../../current/design.md) rather than duplicating its key
   table.
8. **The screens** — Enter vocabulary, Browse, Compile, Inspect tree, Settings.
9. **The file format** — substantially as it is today, re-verified against
   `parser.py`/`writer.py` rather than copied on trust.
10. **Troubleshooting** — `idiomas doctor`, `sudo tlmgr install xecjk`, and the
    `PATH` line.
11. **Updating and uninstalling** — `git pull` in the clone; delete the clone
    and the symlink.
12. **Developing** — `pip install -e ".[dev]"`, `pytest`, clearly separated
    from the user install.
