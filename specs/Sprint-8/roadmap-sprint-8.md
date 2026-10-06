# Roadmap — Sprint 8

Sprint 7 made the project public. Sprint 8 makes it **install itself**. Today, a
new computer with Python, git and a terminal gets through `pip install .` and
then reaches a wizard that reports pandoc and TeX missing and shows a command to
run. By the end of this sprint the wizard's first step has an **Install
missing** button that runs those commands itself, on the two platforms the app
now supports: macOS (with Homebrew) and Arch Linux (with pacman).

The backlog is [`guidelines/backlog.md`](guidelines/backlog.md), a copy of the
dev's `postponedfeatures.md`. It is never committed, so the link resolves only
on the dev's machine. Its one section, *Fix wizard*, is split into M1 and M3.
One item joins from Sprint 7's Postponed table, by the dev's choice: `doctor`
checking the LaTeX packages the template loads (M2). The decisions behind this
are in [`guidelines/notes-sprint-8.md`](guidelines/notes-sprint-8.md).

The backlog opens with an instruction that applies to every milestone below:
"It is important the specs are as thorough as possible as to minimze
interaction with the dev during the implementation step." Each milestone's
*Open for the spec conversation* list is the minimum its interview has to close,
not the whole of it.

The ordering principle is **dependency order**:

- **The platform gate comes first** (M1). The install can only run commands
  for a platform it knows, so the app has to say what it supports, and refuse
  everything else, before anything installs.
- **The package check comes second** (M2). *Install missing* can only fix what
  `doctor` reports. Today a TeX that has `xelatex` but lacks a package the
  template loads passes the check and then fails at the first compile. BasicTeX
  is exactly that case, and it's what M3 installs on macOS.
- **The install comes last** (M3), on top of both.

Earlier sprints' vocabulary is used below without re-explaining it. **Step 1**
is the wizard's *Dependencies* screen (`DependenciesScreen`). **Step 3** is its
languages screen, where ticking Chinese already offers to install xeCJK and the
CJK font (Sprint 6 M7, `tui/screens/dependencies.py`). See
[`../current/design.md`](../current/design.md), *A language's missing
dependencies*.

---

## M1 · Supported platforms

The backlog: "The wizard should check for the os. For now, only Macos and Arch
linux will be supported."

**Deliverable.**

- The platform layer identifies exactly two supported platforms: **macOS** and
  **Arch Linux** (by `/etc/os-release`, the way `distro_family()` already reads
  it, Arch derivatives included or not as the spec decides).
- On anything else, **the wizard refuses to start**: a message saying only
  macOS and Arch Linux are supported, and nothing written.
- The Debian and Fedora tables in `platform/linux.py`'s `INSTALL_HINTS`, and any
  code that exists only to choose between them, are removed.
- `stack.md` and `design.md` state the supported platforms once.

**Open for the spec conversation.**

- What "refuses" covers: the wizard alone, or also the app with an existing
  config (a config copied from another machine), and `vimdiomas doctor`.
- Whether the refusal is a TUI screen or a line printed before the TUI starts.
- Whether Arch derivatives (Manjaro, EndeavourOS: `ID_LIKE=arch`) count as Arch.
- What happens to the non-macOS, non-Linux fallback block in
  `platform/__init__.py`.

**Done when.** On macOS and Arch the wizard runs as before. On another distro
(checked in a Debian container, or with `os-release` faked in tests) it refuses
with the agreed message and writes nothing. No Debian or Fedora command is left
in the code, and the full test suite passes.

---

## M2 · `doctor` checks the LaTeX packages

Carried from Sprints 5–7's Postponed tables: "on Arch a bare `texlive-xetex`
passes `doctor` and then fails to compile."

**Deliverable.**

- The list of LaTeX packages the template loads (beyond xeCJK, which already has
  its own check), worked out from the template and confirmed by compiling.
- A `doctor` check for them through `kpsewhich`, the way xeCJK is checked now,
  reported as `required` and blocking step 1's *Next* when missing.
- For each platform, the command that installs whatever is missing: `tlmgr
  install …` on macOS, the pacman TeX Live packages on Arch. M3 runs these
  commands. Until then they're only shown.

**Open for the spec conversation.**

- One check for the whole set, or one per package (the wizard's list has room
  for about eight lines).
- How the check reports which packages are missing, so the command installs
  only those.
- Whether the BasicTeX package list is verified here or in M3. It's only
  needed once M3 installs BasicTeX, but it's found the same way.

**Done when.** A TeX that's missing one of the template's packages fails the
check on step 1 and in `vimdiomas doctor`, with the package named. A complete
TeX passes as before. The full test suite passes.

---

## M3 · Install missing

The backlog: "The first screen of the wizard checks for missing dependencies.
If one is missing, a third button should be added: "install missing". No
instructions should be shown on how to do it. The app should just run the
commands".

**Deliverable.**

- Step 1 shows a third button, **Install missing**, whenever a required or
  optional dependency is missing. Language dependencies (xeCJK, the CJK font)
  are left to step 3's existing offer.
- Pressing it runs the platform's commands for everything missing, with the TUI
  suspended so `sudo` (pacman) or the BasicTeX `.pkg` installer can ask for a
  password, then rechecks.
  - **macOS:** `brew install` for pandoc, poppler (`pdftoppm`), neovim and
    macism. For TeX: nothing if `xelatex` is already there (MacTeX or any other
    TeX), otherwise `brew install --cask basictex`. Then `tlmgr install` for
    whatever M2's check reports missing.
  - **Arch:** one `sudo pacman -S --needed …` for everything missing.
- The failure lines no longer show commands or install hints ("No instructions
  should be shown"). They say what's missing and nothing else.
- The recheck finds a TeX installed during this session even though the wizard's
  `PATH` predates it (BasicTeX's `/Library/TeX/texbin`).
- `design.md`'s *A language's missing dependencies* and the dependency
  conventions are updated: it's no longer true that "only a language's own
  dependencies are ever offered for installation".
- A way to verify on a bare Arch machine. Today's `docker/Dockerfile` installs
  everything up front.

**Open for the spec conversation.**

- Whether *Install missing* asks for confirmation first, as step 3's offer
  does, or runs straight away.
- Whether the commands run one at a time or as one batch, and whether one
  failing stops the rest.
- Whether `brew` or `pacman` being absent, though assumed present, gets a
  one-line failure or nothing.
- What the button does after a partial success (still shown, renamed,
  disabled).
- Whether step 3 and Settings › Add a language also stop showing commands, or
  keep their confirmation text as it is.
- How the dev hand-tests on a Mac that already has everything (a temporary
  `PATH`, a test-only override, a spare user account).
- The bare Arch image: a second Dockerfile, a build argument, or a change to the
  existing one.

**Done when.** On a bare Arch container with only `python` and `git`, following
the README's *Installing* and pressing *Install missing* leaves every required
and optional check `ok`, and a Chinese notebook compiles once step 3 has
installed its dependencies. On macOS, a missing dependency is installed by the
button and passes the recheck without restarting the wizard. No install command
or hint appears anywhere on step 1. The full test suite passes.

---

## Not in this sprint

The dev's own `postponedfeatures.md` is theirs to manage. Also out, by decision
during this sprint's planning:

- **The README.** Its dangling *Dependencies* link and the claim that the user
  installs tools first are left as they are (see notes, Postponed).
- **Debian, Fedora, Windows, WSL.** M1 drops what existed for the first two.
- **Installing Homebrew or pacman.** Taken for granted, per the backlog.
- **Full MacTeX.** Never installed by the app; a user's existing one is kept.
- Everything else in Sprint 7's Postponed table, restated in this sprint's
  notes.
