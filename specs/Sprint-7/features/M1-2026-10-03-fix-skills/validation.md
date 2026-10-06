# M1 · Fix the skills — validation

The acceptance bar for the branch. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Backlogs untracked, still on disk — moved to M6

Not part of M1's acceptance bar any more (see requirements §1). The checks
below are kept as M6's to run.

```sh
git ls-files | grep -E 'guidelines/(backlog|motivation)\.md'      # prints nothing
ls specs/Sprint-{3,4,5,6}/guidelines/backlog.md specs/Sprint-7/guidelines/backlog.md \
   specs/Sprint-2/guidelines/motivation.md                         # all six listed
git check-ignore specs/Sprint-{3,4,5,6,7}/guidelines/backlog.md \
   specs/Sprint-2/guidelines/motivation.md                         # all six echoed
git status --short --ignored=no | grep -E 'backlog|motivation'     # prints nothing
git ls-files specs/Sprint-5/guidelines/image-1.png specs/Sprint-6/guidelines/bug-report.md
                                                                   # both still listed
```

The commit's diff shows the five files as deletions, and the working tree still
has them.

## 2. The files agree

Each check below is a read of the diff, with a grep to find every site:

```sh
grep -n -i 'backlog' .claude/skills/*/SKILL.md CLAUDE.md specs/current/README.md
grep -n -i -E 'changelog|close' .claude/skills/*/SKILL.md CLAUDE.md specs/current/README.md
grep -n -E 'git mv|git add|branch -d|branch -D|delete-branch' .claude/skills/*/SKILL.md
```

- Every description of `backlog.md` says it is local-only, gitignored, and
  needs its own backup (§1.4). None says it is committed or moved with
  `git mv`.
- `git mv` appears only where it applies to a non-backlog (kickoff's
  `vision.md`).
- The close is described in full only in `changelog`. `feature-spec`,
  `sprint-start` and `CLAUDE.md` point to it and agree on the trigger: the
  last merge, the dev's request, or the sprint-start fallback (§2).
- `sprint-start`'s gate test is the presence of `## Sprint N` in
  `changelog.md`, and no other file states a different test.
- Branch deletion appears in `feature-spec` step 9 only, as the exact sequence,
  with `-D` and its rationale (§3.2). There is no branch check anywhere else
  (§3.3).
- `kickoff` changed in the two places in §4 only.

## 3. Dry read: Sprint 7's own close

A walk-through of the edited skills, as if M6 (Sprint 7's last milestone) had
just been approved by the dev. It is written into *Results* below, step by
step, quoting the skill line that drives each step. Passing means:

- After the squash-merge, `git branch` shows `main` only, and
  `git branch -r` has no `origin/2026-…-m6-…` ref. This follows from step 9's
  sequence alone, with no extra check.
- `feature-spec` asks to close Sprint 7. On a yes, `changelog` runs on `main`:
  the gate passes (M1–M6 have folders), the closing note goes into
  `notes-sprint-7.md`, and `## Sprint 7` is inserted above `## Sprint 6`, with
  one commit `Close Sprint 7` pushed.
- At the next `sprint-start`, the gate finds `## Sprint 7` and passes. It
  copies `postponedfeatures.md` to `Sprint-8/guidelines/backlog.md`, and
  `git check-ignore` confirms the copy is ignored. Nothing stages it.
- The alternative path: if the dev had said "not now" at the close prompt,
  `sprint-start` finds no `## Sprint 7` and runs `changelog` before creating
  `Sprint-8/`.

The walk-through also notes one caveat: Sprint 7's M6 changes `origin` to the
public repo. The sequence in step 9 doesn't depend on which remote `origin` is.

## 4. Nothing else moved

```sh
git diff --stat main...HEAD -- src tests                           # prints nothing
python -m pytest -q                                                # passes
```

## 5. Dev review

The dev reads the skill diffs (`git diff main...HEAD -- .claude CLAUDE.md
specs/current .gitignore`) and approves. That approval, not the checks above,
closes the milestone.

## Results

Run on 2026-10-03, on branch `2026-10-03-m1-fix-skills`.

### §1 Backlogs untracked — moved to M6

The agent's `git rm --cached` was blocked by its tool-permission classifier. At
merge, the dev moved both halves of plan group 1 to M6: the untracking and the
`.gitignore` line for `motivation.md`. Sprint 3–6's backlogs and Sprint 2's
`motivation.md` are still tracked when M1 merges.

### §2 The files agree — pass

- `backlog.md` is annotated *local-only (gitignored)* in the layout blocks of
  `feature-spec`, `sprint-start`, `CLAUDE.md` and `specs/current/README.md`. The
  backup note appears in `feature-spec` step 3, `sprint-start` step 4,
  `CLAUDE.md`'s working agreement and the README's `backlog.md` bullet.
  `changelog` doesn't mention the backlog, except to warn against `git add -A`.
- `git mv` appears in kickoff (for `vision.md`) and, as a prohibition, in
  `sprint-start` step 4 ("Never `git mv` it", "never `git mv`"). It is never an
  instruction for a backlog.
- The close is described in full only in `changelog` (steps 1–5). `feature-spec`
  step 9, `sprint-start` step 2 and its Notes, and `CLAUDE.md`'s routing row all
  name the same three triggers and invoke `changelog`.
- The gate test, "`## Sprint N` present in `changelog.md`", is stated in
  `sprint-start` step 2 and agreed with by `changelog`'s preamble, the README and
  `CLAUDE.md`. No file states another test.
- Branch deletion appears only in `feature-spec` step 9, with `-D`, its
  rationale, and the no-remote variant. No other skill checks branches.
- `kickoff` changed in step 3 only: the aside reworded, and `vision.md` stated
  as committed.

### §3 Dry read: Sprint 7's own close — pass

As if the dev had just approved M6:

1. `feature-spec` step 9, *Merge and clean up*: `gh pr merge --squash
   --delete-branch` removes the remote branch. `git checkout main && git pull`
   leaves the branch. `git branch -D 2026-…-m6-… 2>/dev/null || true` removes
   it locally, whether or not `gh` already did. `git fetch --prune` drops
   `origin/2026-…-m6-…`. The final `git branch` lists `main` only. M6 re-points
   `origin` to the public repo, and the sequence doesn't depend on which remote
   `origin` is.
2. Step 9 updates and commits `notes-sprint-7.md`. Then, "**If this was the
   roadmap's last milestone,** … Ask the dev whether to **close the sprint
   now**."
3. On a yes, `changelog` runs. Step 0 puts it on `main`. Step 1's gate passes,
   since M1–M6 each have a `features/` folder. Step 2 writes the closing note into
   `notes-sprint-7.md` Decisions. Step 3 inserts `## Sprint 7` above
   `## Sprint 6`. Step 4 commits the two files by name as `Close Sprint 7` and
   pushes.
4. At the next `sprint-start`, step 2's `grep -q '^## Sprint 7$'` finds the
   section and the gate passes. Step 4 copies `postponedfeatures.md` to
   `Sprint-8/guidelines/backlog.md`, and `git check-ignore -q` confirms the copy
   is ignored. Nothing stages it.
5. The alternative path: on a "not now" at the close prompt, step 9 reports
   that the sprint is still open. `sprint-start` step 2 then finds no
   `## Sprint 7` and invokes `changelog` before `mkdir specs/Sprint-8`.

### §4 Nothing else moved — pass, with one environmental failure

- `git diff HEAD -- src tests` is empty.
- `pytest -q`: 1232 passed and 1 failed. The failure is
  `test_packaging.py::test_every_data_file_is_declared_as_package_data`. It is
  caused by an untracked Finder `src/idiomas/.DS_Store` that the test counts as
  an undeclared data file. It is not caused by M1. Deleting that file should
  clear it, but this hasn't been re-run.

### §5 Dev review — approved

The dev approved the merge on 2026-10-03.
