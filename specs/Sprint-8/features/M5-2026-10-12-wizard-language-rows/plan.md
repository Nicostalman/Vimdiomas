# M5 · Language rows off the wizard's first step — plan

Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The filter (§1)

- `tui/screens/wizard.py`: one helper returning the checks whose `needed_for`
  is empty; `_checks_text` and `_pending_checks_text` use it before computing
  widths, so all three renders (first, spinner, after Recheck) agree.
- Leave `self._checks`, `_blocking` and `_installable_missing` as they are.
- Update the two docstrings that say what the list shows.

## 2. Tests (§3)

- Rewrite the two label tests as described in §3; add the omission tests for
  both renderers and the Pilot checks (step 1 without the row, *Next* works,
  step 3 still offers; the rows stay absent after Recheck).
- Run `tests/test_tui_wizard.py`, `tests/test_tui_dependencies.py` and
  `tests/test_doctor.py`, then the full suite.

## 3. Docs (§4)

- `design.md`: the *A language's missing dependencies* paragraph, as §4 says.
- Tick `validation.md` as each item is checked; the specs and the code must
  agree before the PR.
