# M5 · README rewrite — validation

The acceptance bar for the branch. Section numbers (§) refer to
[`requirements.md`](requirements.md). Everything here is run once and reported.
There are no new automated tests, since nothing in `src/` changes.

## 1. Structure (§1)

- [x] `grep -n '^## ' readme.md` prints exactly
      `## Tutorial and overview`, `## Installing`, `## Dependencies`, in that
      order.
- [x] `grep -c '^# ' readme.md` is 1, outside code blocks.
- [x] Both screenshots linked from `readme.md` exist under `docs/images/`.
- [x] `grep -nE 'specs/|CLAUDE.md|\.claude' readme.md` prints nothing.
- [x] Every relative link in `readme.md` and `docker/README.md` resolves to a
      file or heading that exists.

## 2. Content (§2, §3, §5)

- [x] *Installing* has: the clone command with
      `https://github.com/Nicostalman/Idiomas.git`, venv + `pip install .`, the
      full-path first run, the wizard note (runs once, settings path, PATH),
      uninstalling. No *Updating* section and no six-step list: the dev cut
      them (requirements.md, Decisions).
- [x] *Dependencies* has the macOS and Linux tables, with git and `pdftoppm`
      on macOS, the LaTeX packages paragraph naming all seven, and what
      `idiomas doctor` checks.
- [x] Every install command in the tables matches `platform/macos.py` /
      `platform/linux.py` where those files have one.
- [x] Every dependency `doctor.py` checks appears in the tables for both
      platforms.
- [x] `docker/README.md` holds the Docker instructions and no longer links to
      a README anchor.
- [x] `specs/current/mission.md` no longer calls `readme.md` the contract.
- [x] `git diff --stat main` touches only `readme.md`, `docker/README.md`,
      `specs/current/mission.md`, `docs/images/` and this spec folder.
- [x] `.venv/bin/pytest` passes.

## 3. Clean install (the roadmap's done-when)

In the Sprint 5 M7 Linux container (`docker/`), following *Installing* as
written, cloning `/src` at this branch instead of the GitHub URL:

- [x] The three install commands succeed. (Run 2026-10-04 in the container: clone,
      venv, `pip install .`, and `.venv/bin/idiomas doctor` exits 0 with the
      required and Chinese checks `ok`.)
- [ ] The full-path first run opens the wizard, and the wizard finishes.
- [ ] In a new shell, `idiomas doctor` exits 0 and `idiomas` opens the
      language menu.
- [ ] Adding one entry and compiling produces a PDF.

Not driven by the agent: the wizard, the new shell, adding an entry and
compiling are an interactive TUI. The dev runs them in the container (or says
they are happy to rely on Sprint 5 M7, which exercised the same steps).

## 4. The dev's review

- [x] The dev reads `readme.md` and approves it. (The dev's own edits are the
      review; merge requested 2026-10-05.)
- [ ] The dev confirms or rejects moving the Docker instructions into
      `docker/README.md` and the `mission.md` edit (requirements.md,
      Decisions).
