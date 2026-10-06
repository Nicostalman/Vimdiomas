# M5 · README rewrite — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Facts check (§2, §3)

- Read every install command in `src/idiomas/platform/macos.py` and
  `linux.py`, and the checks in `doctor.py`. Note any that today's README
  disagrees with.
- Read the `\usepackage` lines in `src/idiomas/templates/xecjk.tex`.

## 2. Rewrite `readme.md` (§1–§4)

- Title and tagline.
- *Installing*: the pointer, download, set up, first run, wizard, updating,
  uninstalling.
- *Dependencies*: macOS and Linux tables (with git and `pdftoppm` added on
  macOS), the LaTeX packages paragraph, *What `idiomas doctor` checks*.
- `## Tutorial`, empty.
- Delete everything else.

## 3. Files outside the README (§5)

- `docker/README.md`: take in the Docker instructions.
- `specs/current/mission.md`: repoint the contract line.

## 4. Checks (validation.md §1–§2)

- Run validation.md §1's structural checks.
- Run the full test suite (nothing should change).

## 5. Clean install in the Linux container (validation.md §3)

- Build the Sprint 5 M7 image. Follow *Installing* exactly as written, cloning
  the mounted checkout of this branch in place of the GitHub URL (the only
  deviation). Run the wizard through to the end, then `idiomas doctor`, then
  open the app.
- Report the result. Any step that doesn't work as written is fixed in the
  README, and recorded here.

## 6. The dev's review edits (requirements.md, Decisions)

- The dev hand-edited `readme.md`: one-line tagline, *Tutorial and overview*
  first with two screenshots, *Installing* condensed, *Updating* and the wizard
  steps cut.
- Move the screenshots to `docs/images/overview-{1,2}.png`, fix the links.
- Bring requirements.md §1, §2, §4 and validation.md §1–§2 in line.
- Re-run validation.md §1–§2.

## 7. Hand off to the dev (validation.md §4)
