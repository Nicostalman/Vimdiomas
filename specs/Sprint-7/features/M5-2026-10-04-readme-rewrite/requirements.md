# M5 · README rewrite — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-7.md`](../../roadmap-sprint-7.md), *M5 · README
rewrite*:

> **Deliverable.** `readme.md` with a title and exactly three sections.
> *Installing* covers `git clone`, the install, the first-run wizard, updating
> and uninstalling. *Dependencies* covers what has to be on the machine and per
> platform (pandoc, xelatex, the CJK packages and font only for Chinese, `nvim`),
> and what `idiomas doctor` checks. *Tutorial* is an empty heading.
>
> **Done when.** The README has exactly the three sections, *Tutorial* is empty,
> and following *Installing* on a clean machine (or the Sprint 5 M7 Linux
> container) installs a working app. The dev reads it and approves.

The backlog, *Redo readme.md*: "It should only have the following sections:
Installing, Dependencies and Tutorial. The tutorial will be full of screenshots
so I'll do it manually."

This is a documentation-only milestone: **no change to `src/` or `tests/`.**

## Decisions

Settled with the dev in the spec conversation, 2026-10-04.

| Decision | Rationale |
| --- | --- |
| **Everything outside the three sections is dropped, not moved**: *Using it*, *Your notebook*, *The file format*, *When something stops working*, *Developing* | Dev's choice, over moving them to `docs/` or `specs/current/`: the Tutorial covers usage. The file-format standard already lives in `design.md` (*A file edited by hand is checked, never refused*) and Sprint 6 M9's `requirements.md` §1. The two facts of *When something stops working* that a user needs at install time (`idiomas doctor`, and xeCJK as the usual culprit) go into *Dependencies*. |
| **The clone URL stays `https://github.com/Nicostalman/Idiomas.git`** | Dev's choice. Assumes the public repo takes the same name once the private one is deleted. If M6 picks another name, M6 updates the README. |
| **Dependencies names the LaTeX packages the template loads** | Dev's choice. Answers Sprint 6's postponed *`doctor` checking for the LaTeX packages* in the docs only: `doctor` is unchanged and the Postponed row stays open for the code. |
| **A one- or two-sentence tagline sits between the title and *Installing*** | Dev's choice. It says what Idiomas is and which languages it supports. No links into `specs/`, which M6 may not publish. |
| **The Docker instructions move into `docker/README.md`** | Agent's proposal, for the dev to confirm in review. `docker/README.md` links to the main README's *Testing on Linux (Docker)* anchor, which disappears. The container is also how this milestone's done-when is checked. The content moves, it isn't rewritten. |
| **`mission.md`'s "`readme.md` is the contract" points at `design.md` instead** | Agent's proposal. The file format leaves the README, and `design.md` already states the standard. One-line edit in `specs/current/mission.md`. |

| **The dev's hand edits to the README supersede §1, §2 and §4 below** (review, 2026-10-05) | Dev's choice. The tagline becomes one line; the Tutorial moves first, is titled *Tutorial and overview*, and holds two screenshots and a line on Vim keybindings, written by the dev; *Installing* is condensed to one code block and loses its wizard-steps list and *Updating*. Sections 1, 2 and 4 are rewritten to describe the file as merged. |
| **The two screenshots live in `docs/images/`** | Agent's choice, accepted by the dev. They were untracked files at the repo root with macOS's default names. They are renamed `overview-1.png` and `overview-2.png`, and the README links them by relative path. |

## 1. Shape of the file

```
# Idiomas

<tagline>

## Tutorial and overview
## Installing
## Dependencies
```

- Exactly three `##` headings, in that order. `###` subheadings are allowed
  inside *Installing* and *Dependencies*.
- The tagline is one line: "Store vocabulary efficiently into markdown files,
  tastefully compiled to PDF."
- *Tutorial and overview* is the dev's, not the agent's: two screenshots
  (`docs/images/`) and a line saying the keybindings are Vim's only.
- No `---` rules between sections. They were there to separate ten sections.
- No link into `specs/`, `CLAUDE.md` or `.claude/`.

Order: the dev's choice (above) puts the Tutorial first, ahead of the backlog's
Installing, Dependencies, Tutorial. *Installing* opens with a pointer to
*Dependencies*, and the wizard checks them anyway.

## 2. Installing

Carried from today's *Install*, *First run: the wizard* and *Updating and
uninstalling*, then condensed by the dev (see Decisions). Items 2–4 are now one
commented code block (`# Download`, `# Setup`, `# Run once`), and items 5 and 6
are cut to what is listed under them:

1. A one-line pointer: the tools listed under *Dependencies* (at least Python
   3.14+ and git) have to be there first. The wizard checks the rest.
2. **Download**: `git clone https://github.com/Nicostalman/Idiomas.git
   ~/.local/share/idiomas`, and why that folder.
3. **Set up**: `python3 -m venv .venv` and `.venv/bin/pip install .`, with the
   one-sentence explanation of a virtual environment.
4. **Run once by full path**: `~/.local/share/idiomas/.venv/bin/idiomas`, and
   why plain `idiomas` works only after the wizard.
5. **The wizard** (`###`): that it runs once, settings in
   `~/.config/idiomas/config.toml`, and the PATH note. The six-step list, the
   `q` / nothing-written-on-quitting paragraph and the "something in the way"
   note are gone.
6. **Updating**: dropped. The README no longer covers it.
7. **Uninstalling** (`###`): remove the clone and `~/.local/bin/idiomas`. The
   notebook and settings survive, and where they are.

Today's text references "the list above" for dependencies. That becomes "under
*Dependencies* below".

## 3. Dependencies

Carried from today's *What you need first*, with these changes:

- **macOS optional table gains `pdftoppm`** (`brew install poppler`). `doctor`
  checks it on both platforms (`doctor.py`, `platform/macos.py`'s
  `INSTALL_HINTS`), but today's README lists it for Linux only.
- **macOS required table gains git**, as Linux's has. It ships with the Xcode
  command-line tools: `xcode-select --install`.
- **LaTeX packages** (Decisions): one paragraph saying the template loads
  `fontspec`, `lmodern`, `geometry`, `longtable`, `caption`, `array` and
  `xcolor` (and `xeCJK` for Chinese). The full TeX Live, BasicTeX and the
  Linux collections in the tables already include them. A bare `texlive-xetex`
  on Arch does not, and `doctor` does not check for them.
- **What `idiomas doctor` checks** (`###`, replaces *When something stops
  working*): it reports each dependency as `ok` or missing, labelled
  `required`, `optional` or with the language that needs it. It exits
  non-zero when a required one, or one needed by a configured language, is
  missing. Run it if compiling suddenly fails or the keyboard stops switching.
  The xeCJK fix (`sudo tlmgr install xecjk`, or the distro's Chinese TeX Live
  package) stays as the one troubleshooting line.
- The Linux notes (fcitx5/ibus, Noto vs Songti, WSL unsupported) stay as they
  are.

Every install command in the tables must match `platform/macos.py` and
`platform/linux.py` where those files have one.

## 4. Tutorial

`## Tutorial and overview`, first section, written by the dev (§1). Not the
empty heading the roadmap asked for: the dev filled it in during review.

## 5. Outside `readme.md`

- `docker/README.md`: replace the anchor link with the content of today's
  *Testing on Linux (Docker)*: build, run, what `-v` and `-e TERM_PROGRAM`
  do, cloning the mounted checkout for a branch, running the tests, and
  `docker cp`. It points at the main README's *Installing* for the install
  itself.
- `specs/current/mission.md`, *Non-goals*: "`readme.md` is the contract"
  becomes a pointer to `design.md`'s hand-edit standard.
- No other file links into a README anchor (checked with `grep -rn readme`:
  `src/` and `tests/` mention "the README's install", which still exists).

## Out of scope

- The Tutorial's content beyond the two screenshots and one line.
- Any change to `doctor`, the wizard or the install.
- Choosing the public repo's name (M6).
- Documentation files other than `docs/images/`'s two screenshots.
