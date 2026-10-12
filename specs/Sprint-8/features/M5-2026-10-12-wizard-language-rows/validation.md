# M5 · Language rows off the wizard's first step — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [ ] `uv run pytest` passes in full.
- [ ] Wizard tests: `_checks_text` and `_pending_checks_text` omit a check with
      `needed_for`, and the columns are sized to the rows shown (the first line
      starts `[required] pandoc`); the rows stay absent after Recheck.
- [ ] Pilot: with xeCJK missing, step 1's list has no `xeCJK` and *Next* moves
      to the name step; at step 3, ticking Chinese still offers the install, and
      German alone proceeds.
- [ ] `tests/test_doctor.py` unchanged and passing: `doctor.run()` still
      reports xeCJK and the font with `needed_for`.

## 2. What the greps should find

- [ ] `git grep -n "needed_for" -- src/vimdiomas/tui/screens/wizard.py` shows the
      new filter and `_installable_missing`'s existing use, nothing else.
- [ ] `git diff main --stat -- src` touches `wizard.py` only.

## 3. By hand (the dev)

On a machine where xeCJK is missing (it is, after the dev's clean-up):

- [ ] `vimdiomas` first run: step 1 lists `pandoc`, `xelatex`, `LaTeX packages`,
      `macism`, `nvim`, `pdftoppm` and no xeCJK or Songti SC row, with the
      columns lined up.
- [ ] *Recheck* keeps it that way, spinner included.
- [ ] *Next* works; at the languages step, ticking Chinese offers to install
      xeCJK.
- [ ] `vimdiomas doctor` still prints `[ Chinese] xeCJK  missing`.

## 4. Specs

- [ ] `design.md` updated as §4 lists.
- [ ] Code and these three files agree.
