# M1 · Fix the skills — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. Untrack the backlogs (§1.1, §1.2) — moved to M6

Not done in M1, by the dev's decision at merge. M6 carries this group out.

- Add `specs/Sprint-2/guidelines/motivation.md` to `.gitignore`, with a
  comment.
- `git rm --cached` on `specs/Sprint-{3,4,5,6}/guidelines/backlog.md` and
  `specs/Sprint-2/guidelines/motivation.md`.
- Check the files are still on disk, and that `git status` doesn't show them
  as untracked (they are ignored).

## 2. `changelog` owns the close (§2.1, §2.2)

- Rewrite the description: closing a sprint, with the changelog section as
  its mark.
- Rewrite the workflow as the five-step close: gate, closing note, section,
  commit on main, report. Keep the format section and the Notes rules as they
  are.
- Say who invokes it: `feature-spec` step 9, `sprint-start`'s gate, or the dev
  directly.

## 3. `feature-spec` (§1.4, §2.1, §3.2)

- Layout block: mark `backlog.md` local-only.
- Step 2: "no unstarted milestones left" offers `sprint-start`, noting it closes
  the sprint first if needed (added during implementation, for consistency with
  §2.3).
- Step 3: the backlog is local-only. A missing `backlog.md` is said aloud and
  worked around.
- Step 9: the exact merge-and-cleanup sequence, with the `-D` rationale and
  the no-remote variant. Then the notes update. Then, if this was the last
  milestone, ask to close the sprint and invoke `changelog` on a yes.
- The closing paragraph: the sprint-complete wording points to the close, not
  "changelog / sprint-start are the next steps".

## 4. `sprint-start` (§1.3, §1.4, §2.3)

- Layout block: mark `backlog.md` local-only.
- Step 2: the gate checks for `## Sprint N` in `changelog.md`. If it is
  missing, invoke `changelog` to close the sprint. The closing-note paragraph
  moves to `changelog`.
- Step 4: the copy-from-`postponedfeatures.md` standard, the fallback, no
  `git mv` and no `git add`, the `check-ignore` verification and repair,
  companions committed, verbatim text, and the backup note.
- Notes: replace the "run the `changelog` skill" bullet, and add the
  local-only bullet.

## 5. `kickoff` (§4)

- Reword step 3's "like `backlog.md`…" aside.
- State that `vision.md` is committed.

## 6. `CLAUDE.md` and `specs/current/README.md` (§5)

- `CLAUDE.md`: the routing row for `changelog`, the layout comment, the
  closed-versus-frozen sentence, and the working-agreement bullet.
- `README.md`: the layout comment, the `backlog.md` bullet, the `changelog.md`
  bullet, and the Sprint-2 `motivation.md` note.

## 7. Verify (validation.md)

- Run every check in [`validation.md`](validation.md). Write the dry read of
  Sprint 7's own close into `validation.md`'s results section.
- Run the full test suite, as a sanity check that nothing outside the process
  files moved.
