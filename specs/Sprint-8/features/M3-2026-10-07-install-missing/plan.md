# M3 · Install missing — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The platform layer (§3, §4)

- `platform/macos.py`: `BREW_FORMULAS`, `BASICTEX_CASK`, the `xecjk` `tlmgr`
  name, `PACKAGE_MANAGER`, `package_manager_available()`, `installable()`,
  `extend_path()`, `install(keys, run, missing_latex)`. Remove
  `INSTALL_HINTS`, `install_hint`, `latex_install_hint`.
- `platform/linux.py`: `PACMAN_PACKAGES`, `PACKAGE_MANAGER`,
  `package_manager_available()`, `installable()`, `extend_path()` (no-op),
  `install(…)`. Remove the same three. Rewrite the comments that describe the
  hint tables.
- `platform/__init__.py`: the new names on both branches and in `__all__`, the
  old ones gone.
- `cli.main()`: `platform.extend_path()` before dispatch (§4).
- `tests/test_platform.py`, `tests/test_platform_linux.py`: the `install`
  sequences with a recording `run` and a stubbed `missing_latex`. macOS: brew
  only; xelatex missing (the cask, then `extend_path`, then the `tlmgr` pair only
  when `missing_latex` reports something); stock BasicTeX (no `tlmgr`); `xecjk`
  alone (update --self, then install xecjk); no `tlmgr` found (skipped); a failed
  `run` doesn't stop the next. Arch: one deduplicated `pacman` command;
  `missing_latex` `None` (every `LATEX_PACKAGES` target); keys it can't install
  are ignored. `extend_path` with a tmp dir standing in for each known dir:
  appended once, only when it exists, never duplicated. `installable` for each
  key on each platform.
- `tests/test_no_platform_leaks.py`: add `tlmgr`, `pacman`, `sudo `.

## 2. `doctor` (§5)

- `Check.key` added; `install`, `message`, `url` and `_example()` removed;
  `missing_latex_packages()` made public.
- `cli._doctor()` prints `ok` / `missing` / `missing: <detail>`.
- `tests/test_doctor.py`, `tests/test_main.py` (or wherever `doctor`'s CLI
  output is tested): every check has its key; the new CLI lines; exit status
  unchanged.

## 3. The installer (§2)

- `vimdiomas/installer.py`: `run(app, checks)` with its runner and the
  `missing_latex` callback; the header and the Enter prompt; never raises.
- `tests/test_install.py` is the linking step's. The installer gets
  `tests/test_installer.py`: the runner (prints, no shell, `OSError` → false),
  that `run` passes the keys through and calls `extend_path`, and that `EOFError`
  at the prompt is tolerated. `app.suspend` and `platform.install` are faked.

## 4. Step 3 and Settings (§7)

- `tui/screens/dependencies.py`: `_installable` in place of `_offerable` (§7), the confirmation and
  refusal wording, the missing-manager line, `installer.run` in place of
  `_install`, and the module docstring.
- `tests/test_tui_dependencies.py`: the new wording (no backticks, no command
  anywhere in the dialog or the refusal); a missing manager refuses with its line;
  `cjk-font` on macOS is not offerable; install then recheck as before.

## 5. Step 1 (§1, §6)

- `tui/screens/wizard.py`: `#install-button` first; visibility from the checks;
  focus at mount and when it hides; the missing-manager line; the
  `ConfirmDialog`; `installer.run` then the existing recheck; `Still missing:
  …` after it; *Next*'s new error line; `_checks_text` without the URL arrow.
- `tests/test_tui_wizard.py`: shown / hidden by the checks (language checks
  alone don't show it); focus; confirmation text has no command; `n` does
  nothing; `y` runs the installer and rechecks; partial success keeps it and
  names what's left; full success hides it and moves focus to *Next*; no manager
  line; no URL or command in the rendered list for any failing check.

## 6. Inspect Tree (§8)

- `tui/screens/inspect.py`: the two messages; drop the `install_hint` import.
- `tests/test_tui_inspect_tree.py`: the messages as asserted.

## 7. Verification support (§9)

- `docker/Dockerfile`: `ARG BARE=0`, the two package lists, `sudo` and
  `learner`'s password and `wheel` group.
- `docker/README.md`: the *Bare image* paragraph.
- Build both variants. The full one must still pass `vimdiomas doctor` all `ok`
  after the README install.

## 8. Specs and docs (§10)

- `design.md` and `stack.md` as §10 lists.
- If anything comes up while implementing, these three files are updated first.

## 9. Checks before the hand-off

- Full test suite on the Mac.
- The greps and the Arch container runs in [`validation.md`](validation.md) §2
  and §3, run by the agent.
- Stop for the dev's review, the macOS VM run (§4) and the regression check on
  the dev's Mac (§5).

## 10. Hand-off, merge

- PR, squash-merge, cleanup per `feature-spec` step 9.
- Notes on `main`: M3's decisions into settled form, and the four Assumptions
  rows M3 resolves (§10).
