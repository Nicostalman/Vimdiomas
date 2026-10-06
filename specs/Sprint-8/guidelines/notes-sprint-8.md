# Sprint 8 — notes

The agent-maintained companion to
[`../roadmap-sprint-8.md`](../roadmap-sprint-8.md): it records what was decided,
assumed, or postponed while the backlog was turned into that roadmap, and it
grows as the sprint runs.

**Where the backlog came from.** [`backlog.md`](backlog.md) is a **copy** of the
dev's root-level `postponedfeatures.md`, taken on 2026-10-06 and kept verbatim.
As since Sprint 7, it is gitignored and never committed, so the link resolves
only on the dev's machine. It has one section, *Fix wizard*.

**Sprint 7 closed cleanly.** Its changelog section and closing note were
written on 2026-10-06 (`4b79610`). Five of its six milestones landed; M4, Anki
export, was dropped before its spec and does not carry over.

**What carries over from Sprint 7's Postponed table.** One item, by the dev's
choice: **`doctor` checking for the LaTeX packages the template loads**, which
becomes M2. The rest of that table stays out and is restated in this file's own
Postponed table.

**Why this sprint exists.** Asked whether a new computer with only Python, git
and a terminal would end up with a working app, the agent's answer was no: the
wizard reports pandoc and TeX missing and shows a command, and only xeCJK (Sprint
6 M7) is ever installed for the user. Sprint 4 had decided against installing
dependencies ("The wizard checks and blocks or warns; it doesn't run brew or
tlmgr"). This sprint reverses that decision.

**The backlog's standing instruction.** It opens, as Sprint 7's did: "It is
important the specs are as thorough as possible as to minimze interaction with
the dev during the implementation step." This applies to every milestone this
sprint.

## Decisions

Settled with the dev during this sprint-start conversation, on 2026-10-06.

| Decision | Rationale |
| --- | --- |
| **Every open question is settled in the spec conversation, not during implementation** | The backlog's opening line, carried over unchanged from Sprint 7. A question that comes up mid-implementation is a gap in the spec, recorded in the spec when it comes up. |
| **Reverses Sprint 4's "Installing dependencies for the user" exclusion** | The backlog: "No instructions should be shown on how to do it. The app should just run the commands". Sprint 4's roadmap stays frozen; the reversal is recorded here. |
| **Supported platforms are macOS and Arch Linux only** | The backlog: "For now, only Macos and Arch linux will be supported." |
| **On any other OS the wizard refuses to start** | Dev's choice, over running without an install button. The Debian and Fedora command tables in `platform/linux.py` (Sprint 5 M7) are removed. What exactly "refuses" covers (the wizard alone, the whole app, `vimdiomas doctor`) is open for M1's spec. |
| **Homebrew (macOS) and pacman (Arch) are assumed present, not checked or installed** | The backlog: "Take for granted Brew and Pacman are installed." |
| **Step 1's *Install missing* installs required and optional dependencies, not the language ones** | Dev's choice, from three options. xeCJK and the CJK font stay with step 3's existing offer (Sprint 6 M7), which already installs them when Chinese is ticked. |
| **macOS TeX: an existing `xelatex` is kept; otherwise BasicTeX** | Dev's choice: "check if mactex is installed, right? if not, option 1". If any TeX that provides `xelatex` is found (MacTeX or other), no TeX distribution is installed. If not, `brew install --cask basictex`, then `tlmgr` for the packages the template needs. Full MacTeX (about 5 GB) is never installed by the app. |
| **Three milestones, in dependency order: platform gate, package check, install** | The install (M3) needs to know which platforms it is on (M1) and needs a complete list of what can be missing (M2). See the roadmap's preamble. |
| **The README is not part of this sprint** | Offered as a carry-over (the dangling *Dependencies* link left by `becefef`, and saying the wizard now installs everything); the dev did not choose it. |

## Assumptions

Taken as given by this sprint; not verified in code or stated in the roadmap.

| Assumption | Origin | Notes |
| --- | --- | --- |
| **BasicTeX plus `tlmgr` packages can compile the template** | The agent's proposal, accepted by the dev | **Verified 2026-10-06**, at the dev's request. The method: CTAN's `BasicTeX.pkg` (TeX Live 2026, Apple-notarized) unpacked with `pkgutil --expand-full` into the scratchpad, not installed, and put alone on `PATH` with Homebrew's pandoc. The app's own `compile_file` ran on `tests/fixtures`. Results: **(1)** Of the template's packages (fontspec, xeCJK, lmodern, geometry, longtable, caption, array, xcolor, plus lmodern's `.otf` fonts), **only xeCJK is missing** from stock BasicTeX. German notebooks compile on it as shipped; Chinese ones fail. **(2)** A fresh BasicTeX's `tlmgr install` **refuses to run until `tlmgr update --self`** has run, because its tlmgr is older than the repository's. **(3)** After `tlmgr update --self` and `tlmgr install xecjk`, the three Chinese fixtures (Food, Grammar, Clasificadores) and both German ones compile, with the same embedded fonts and page counts as the MacTeX build. So M2's package check finds only xeCJK missing on macOS, and M3's macOS TeX sequence is `brew install --cask basictex`, then `tlmgr update --self`, then `tlmgr install` for what is missing. Not verified: the real `.pkg` install under `/usr/local/texlive`, which needs `sudo` there, as opposed to the unpacked copy. |
| **A freshly installed TeX is not on the wizard's `PATH`** | How BasicTeX and pacman's TeX install: BasicTeX puts its binaries in `/Library/TeX/texbin`, added to `PATH` through `/etc/paths.d`, which only a new shell reads | M3's recheck must look in the known install location too, or the wizard would still report `xelatex` missing straight after installing it. The same goes for `tlmgr`, which runs straight after the cask in the same *Install missing* run. |
| **Step 3's existing xeCJK offer works on any TeX the app installs** | Sprint 6 M7 was verified on the dev's MacTeX only | **False on a fresh BasicTeX**, found in the BasicTeX check: `sudo tlmgr install xecjk` alone is refused until `tlmgr update --self` has run. Fixed in M3 (roadmap, M3 Deliverable). |
| **`brew install --cask basictex` and `sudo pacman -S` both ask for a password in the terminal** | The cask runs a `.pkg` installer; pacman needs root | The suspend-the-TUI approach from Sprint 6 M7 (`dependencies.py`) already handles that. |
| **The Arch verification image has to become a bare one to test M3** | `docker/Dockerfile` installs every dependency up front (Sprint 5 M7) | M3's spec settles whether that's a second Dockerfile, a build argument, or a change to the existing one. |
| **The dev hand-tests on macOS, as always** | Every sprint so far | Their Mac already has every dependency, so hand-testing *Install missing* on macOS needs a way to make a dependency look missing. M3's spec settles how. |

## Postponed features / pending

Raised during the sprint and deliberately not implemented now. Sprint 7's own
Postponed table stays where it is; only what this sprint carries is restated
below.

| Item | Why postponed | Where it resurfaces |
| --- | --- | --- |
| **README: the dangling *Dependencies* link, and saying the wizard installs everything** | Offered at sprint start, not chosen | Whenever the dev wants the README to match. After M3 the README's "Before you start, have the tools listed under Dependencies" line is wrong as well as broken. |
| **Debian, Fedora and other distros** | The backlog limits support to Arch | If someone asks. Their command tables are removed in M1; Sprint 5 M7's specs keep them. |
| **Installing Homebrew itself** | The backlog takes it for granted | If a user without brew reports it. |
| **Editing and deleting an existing entry in the app**; **moving an entry between categories or files** | Carried from Sprint 7 | The next backlog. |
| **Windows support** and **WSL** | Carried from Sprints 5–7 | Whenever someone needs it. |
| **Multi-page PDF preview** | Carried from Sprints 5–7 | If a notebook grows past a page or two often enough to be annoying. |
| **Persisting the tag cache** and **the content index** | Carried from Sprints 5–7 | If Browse feels slow on a large tree. |
| **Opening the PDF at the entry's page, or the source at its line** | Carried from Sprint 7 | If the dev wants to land on the entry itself. |
| **Searching notes, tags or extra columns; fuzzy or ranked content matching; traditional ↔ simplified hanzi matching** | Carried from Sprint 7 | If the dev asks for one. |
| **Brew packaging** | Carried from Sprints 4–7 | A nice-to-have, unscheduled. |
| **A user-extensible language registry** | Carried from Sprint 6 M7 | Unscheduled. |
| **A menu taller than the frame can push its legend off-screen** | Carried from Sprint 6 M4 | If a long list is ever added. |
| **A straight `'` in an entry** | Carried from Sprint 7 M2 | If it shows up in a real notebook. |
| **Anki export** | Dropped in Sprint 7 | If the dev or a user asks for it. |
