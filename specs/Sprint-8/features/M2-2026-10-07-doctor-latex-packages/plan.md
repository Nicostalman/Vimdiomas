# M2 · `doctor` checks the LaTeX packages — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The platform layer (§3)

- `platform/macos.py` and `platform/linux.py`: the `LATEX_PACKAGES` table (name
  → `tlmgr` package / pacman package, §1) and `latex_install_hint(packages)`
  (deduplicated, first-seen order, `None` for `[]`).
- `platform/linux.py`: narrow `INSTALL_HINTS["xelatex"]` to
  `sudo pacman -S texlive-xetex`; rewrite the comment above the table.
- `platform/__init__.py`: import and export `latex_install_hint` on both
  branches and in `__all__`.
- `tests/test_platform.py`, `tests/test_platform_linux.py`: `latex_install_hint`
  as §5 lists.

## 2. The check (§1, §2)

- `doctor.py`: the `LATEX_PACKAGES` table of (name, probe), `Check.detail`,
  `_missing_latex_packages()` (one `kpsewhich` call, basename matching), the new
  `LaTeX packages` check after `xelatex`, its `message` and `install`.
- Update the module docstring (the required set is now pandoc, xelatex and the
  packages).
- `tests/test_doctor.py`: updates and new tests as §5 lists, including the
  consistency test against `xecjk.tex` and both platform tables.

## 3. Where it shows (§4)

- `tui/screens/wizard.py`: `_checks_text` prints a failing check's `detail`
  under its line, wrapped to the panel; `_pending_checks_text` unchanged.
  Measure the panel's content width when implementing and write it down in the
  code as the wrap width.
- `tui/screens/dependencies.py`: `refusal()` wording for a check with a
  `detail`; the module docstring stays (M3 rewrites it).
- `tests/test_tui_wizard.py`, `tests/test_tui_dependencies.py` as §5 lists.

## 4. Confirm the list by compiling (§6)

- Bare Arch run and the Mac checks from [`validation.md`](validation.md), §3 and
  §4. If a compile needs something the table lacks, or the table lists
  something no compile needs, §1 and the table are corrected first, then the
  code.

## 5. Specs and docs (§7)

- `stack.md` and `design.md` as §7 lists.
- If anything comes up while implementing, the three files here are updated
  first.

## 6. Checks before the hand-off

- Full test suite on the Mac.
- The greps and container runs in [`validation.md`](validation.md).
- Stop for the dev's review and hand-testing on the Mac.

## 7. Hand-off, merge

- PR, squash-merge, cleanup per `feature-spec` step 9.
- Notes on `main`: M2's decisions into settled form (including the `fontspec`
  correction); anything newly postponed.
