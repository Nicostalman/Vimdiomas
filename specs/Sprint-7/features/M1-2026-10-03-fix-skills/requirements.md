# M1 · Fix the skills — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-7.md`](../../roadmap-sprint-7.md), *M1 · Fix the
skills*:

> **Deliverable.** Backlogs are never committed (item 1) … Closing a sprint
> writes the changelog (item 2) … No loose local branches (item 3) …
>
> **Done when.** `git ls-files` lists no `backlog.md` (and none of the
> companions, if those are in) and the files are still on disk. The four skills,
> `specs/current/README.md` and `CLAUDE.md` agree with each other. A dry read of
> `feature-spec` and `sprint-start` against this sprint's own close shows the
> changelog written at close and no branch left behind. The dev reviews the skill
> diffs.

The source is the backlog's *Fix skills* section, items 1–3
(`guidelines/backlog.md`, local-only).

This milestone changes process files only: `.claude/skills/*/SKILL.md`,
`CLAUDE.md`, `specs/current/README.md`, `.gitignore` and the git index. No code
under `src/` or `tests/` changes.

## 1. Backlogs are never committed (backlog item 1)

> **Moved to M6 (dev, 2026-10-03, at merge).** §1.1's untracking and §1.2's
> `.gitignore` line are not done in M1. The dev: "all this will be dealt with in
> m6". M1 ships §1.3 and §1.4, the skill and doc changes. §1.1 and §1.2 are
> recorded below as the agreed target, and M6 carries them out.

### 1.1 Which files

- **Untracked:** `specs/Sprint-{3,4,5,6}/guidelines/backlog.md` and
  `specs/Sprint-2/guidelines/motivation.md`. The last one is Sprint 2's backlog
  under its old name. This was the dev's choice in the spec conversation.
- **Stay tracked and published:** Sprint 5's `image-1.png`, Sprint 6's
  `bug-report.md`, and Sprints 1–2's `agent-notes.md`. The dev chose to keep
  the companions published. Only a backlog is local-only.
- Untracking uses `git rm --cached`. Every file stays on disk, byte-for-byte.
- Removing a closed sprint's file from the index is not an edit to that sprint.
  Its content is unchanged and it stays on disk where it was. The roadmap
  settled this at sprint start. Closed sprints' notes link to their
  `backlog.md`. Those links will not resolve in a clone without the file, and
  that is accepted: the frozen files are not edited to fix them.

### 1.2 `.gitignore`

- `specs/Sprint-*/guidelines/backlog.md` already exists (added at sprint start).
- Add `specs/Sprint-2/guidelines/motivation.md`, with a short comment saying it
  is Sprint 2's backlog under its old name.
- `postponedfeatures.md` is already ignored, and stays ignored.

### 1.3 `sprint-start` places the backlog by copying it, unstaged

Step 4 is rewritten:

- **The standard source is `postponedfeatures.md` at the project root.** This
  is the dev's living deferred list, and it is gitignored. sprint-start looks
  for it first, says what it opens with, and confirms with the dev that it is
  this sprint's backlog.
- **It is copied, not moved:**
  `cp postponedfeatures.md specs/Sprint-N/guidelines/backlog.md`. The root file
  stays the dev's and goes on being their living list. The copy is the sprint's
  frozen snapshot.
- **Fallback:** if `postponedfeatures.md` is absent, sprint-start lists the
  other root `.md` candidates and asks, as it does today. Whatever the source,
  the backlog is placed with plain `cp` (or `mv` if the dev asks for a move).
  It never uses `git mv` and never runs `git add`.
- **Verify it is ignored:** `git check-ignore -q specs/Sprint-N/guidelines/backlog.md`
  must succeed, and `git status --short` must not list it. If it fails, the
  ignore rule is missing, which happens in a project that adopted these skills
  without it. sprint-start then adds `specs/Sprint-*/guidelines/backlog.md` and
  the root source file's name to `.gitignore` before anything is committed.
- **Companions** the backlog references (a bug report, an image) are copied
  into the same `guidelines/` folder and committed like any other sprint file.
  Only `backlog.md` is local-only.
- The text stays **verbatim**, as today.

### 1.4 Every description of the backlog says it is local-only

Wherever a file describes `backlog.md`, it says three things:

- the file is **local-only and never committed**;
- it is **gitignored**, so a fresh clone does not have it;
- it **needs a backup of its own** (Time Machine, iCloud or similar), because
  git does not keep it.

The places:

| File | Where |
| --- | --- |
| `sprint-start/SKILL.md` | The layout block comment, step 4, and a Notes bullet |
| `feature-spec/SKILL.md` | The layout block comment, and step 3. If `backlog.md` is missing, which happens in a clone without it, step 3 says so and works from the roadmap and notes, asking the dev about any intent the roadmap compressed away. |
| `changelog/SKILL.md` | No mention needed. It never reads the backlog. |
| `kickoff/SKILL.md` | §4 below |
| `specs/current/README.md` | The layout block comment, the `backlog.md` bullet, and the Sprint-2 paragraph (`motivation.md` is local-only too) |
| `CLAUDE.md` | The layout block comment, and the working agreement about the dev's own files |

## 2. Closing a sprint writes the changelog (backlog item 2)

### 2.1 What closes a sprint

The trigger is the **last milestone's merge in `feature-spec`**, the dev's
choice. There is no new skill.

- `feature-spec` step 9, after the merge, the branch cleanup (§3) and the notes
  update: if this was the roadmap's last milestone, it asks the dev whether to
  close the sprint now. On a yes, it invokes `changelog`. On a no, it reports
  that the sprint is still open and that `sprint-start` will close it.
- The dev can also say "close the sprint" at any time, with milestones still
  outstanding. That invokes `changelog` directly.
- **`changelog` becomes the skill that runs a sprint close.** Its description,
  routing row and workflow are rewritten around this. The close procedure lives
  only there, and `feature-spec` and `sprint-start` invoke it rather than
  restating it.

### 2.2 The close procedure (in `changelog`)

Run on `main`, after the last milestone's squash-merge. This keeps the dev's
standing preference: the changelog is written after the merge, never before.

1. **Gate.** Every roadmap milestone has a spec folder, or has been explicitly
   deferred or dropped by the dev. If any is outstanding, list it and ask, as
   `sprint-start` step 2 does today. Only the dev's answer closes it.
2. **Closing note** in `notes-sprint-N.md` Decisions: what landed, what was
   dropped, and what carries forward. This moves out of `sprint-start` step 2,
   where it lives today.
3. **Changelog section:** insert `## Sprint N` with one bullet per shipped
   milestone, in the existing format. If the section already exists, make no
   edit unless the dev names a missing milestone. That rule is unchanged.
4. **Commit and push on `main`**, as one commit titled `Close Sprint N`. Closing
   commits go straight to main, the way the sprint-notes commits always have.
5. **Report** what was added, and that `sprint-start` is next.

A closed sprint is *not* frozen by this. It freezes when `Sprint-N+1` exists,
as today. Between close and the next sprint-start, its notes can still take a
correction.

### 2.3 `sprint-start`'s gate checks the close

Step 2 becomes: **the previous sprint is closed when `changelog.md` has a
`## Sprint N` section.** That section is the checkable mark of a close.

- **The section is present:** the gate passes. sprint-start still reads the
  old sprint's roadmap and notes, to offer carry-overs, but writes nothing into
  it.
- **The section is missing:** sprint-start runs the close then and there, by
  invoking `changelog` (gate questions, closing note, changelog section,
  commit), before it creates `Sprint-N+1`. This was the dev's choice. The close
  still happens while the old sprint is writable.
- The trailing Notes bullet "Once this sprint closes, run the `changelog`
  skill…" is replaced to match.
- **First sprint** (no previous sprint): the gate is skipped, as today.

### 2.4 Sprint 1 and Sprint 2

Their sections already exist in `changelog.md`. Nothing about them changes.

## 3. No loose local branches (backlog item 3)

### 3.1 The cause

The dev's diagnosis: this is a misspecification, not something to check for
afterwards. Step 9 says "Delete the branch both locally and on the remote" but
gives no commands. Two things then go wrong. The merge runs while the branch is
checked out, and a checked-out branch cannot be deleted. And `git branch -d`
refuses a squash-merged branch, because its commits never landed on main by
ancestry. So the local delete fails or gets skipped, and the branch survives
until the dev asks about it.

### 3.2 The fix: an exact, always-run sequence in step 9

`feature-spec` step 9 replaces the bullets "Open a PR and squash-merge" and
"Delete the branch…" with this sequence, run every time:

```sh
gh pr create …                               # the PR, as today
gh pr merge --squash --delete-branch         # merges, deletes the remote branch
git checkout main && git pull                # leave the branch, take the squash commit
git branch -D YYYY-MM-DD-mN-feature-name 2>/dev/null || true   # -D: a squash merge is never "merged" to -d
git push origin --delete YYYY-MM-DD-mN-feature-name 2>/dev/null || true   # in case the remote one survived
git fetch --prune                            # drop the stale origin/… ref
```

- `-D` is safe *here and only here*. The branch was merged as a PR a moment
  ago, in the same step.
- The step says why `-D` and not `-d`, so a later reader doesn't "fix" it back.
- `gh pr merge --delete-branch`, run from the branch, usually switches to `main`
  and deletes the local branch itself. The `-D` line therefore tolerates the
  branch being gone already (`2>/dev/null || true`). Found during
  implementation.
- The step ends with `git branch` listing `main` only, as the last line of the
  sequence. This confirms the sequence ran. It is not a separate check.
- Without a remote (no `origin`, no `gh`), the merge is a local
  `git merge --squash` plus a commit, followed by the same `checkout`/`-D`. The
  remote lines are skipped.

### 3.3 Nothing else

There is no sweep at `feature-spec` step 2 and none in `sprint-start`'s gate.
This was the dev's call: branches should be cleaned up automatically, not
hunted for later.

## 4. `kickoff`: minimal consistency edit

`kickoff` has already run and will never run again in this project. It is
edited only where it would contradict the new rules:

- Step 3 says `vision.md` sits at the root "like `backlog.md` and other
  hand-written docs in this workflow tend to". It is reworded so it doesn't
  imply a backlog is placed the way `vision.md` is.
- Step 3 or Notes states that `vision.md` **is committed**. It is the
  stakeholder's document, not a backlog, and the local-only rule does not apply
  to it.
- Nothing else in `kickoff` changes.

## 5. `CLAUDE.md` and `specs/current/README.md`

- **Routing table:** the `changelog` row becomes "The last milestone of a
  sprint has merged, the dev says to close the sprint, or `sprint-start` finds
  the previous sprint not yet closed." The `sprint-start` row loses nothing.
- **Layout block:** `backlog.md` is annotated *dev-written, local-only (gitignored)*.
- **"A closed sprint is frozen"** paragraph: unchanged in meaning. A sentence
  is added saying a sprint is *closed* when its changelog section is written,
  and *frozen* when the next one opens.
- **Working agreements:** the bullet on the dev's own files adds that
  `backlog.md` is never staged or committed.
- `specs/current/README.md`: the bullet on `changelog.md` says the section is
  written when the sprint closes (by `changelog`), and §1.4's backlog changes
  apply.

## 6. Out of scope

- Fixing the links to `backlog.md` inside closed sprints (frozen).
- Removing old backlogs from git history. M6 publishes with no history.
- The user's auto-memory note on changelog timing. The skills now encode it,
  and the memory is the dev's and the agent's, not the repo's.
- Any change under `src/` or `tests/`.

## Decisions taken in the spec conversation (2026-10-03)

| Decision | Source |
| --- | --- |
| Last milestone merge in `feature-spec` triggers the close; no new skill | Dev |
| `sprint-start` closes a not-yet-closed sprint itself, via `changelog` | Dev |
| Branch cleanup is an exact sequence in step 9, with no check elsewhere | Dev ("should be done automatically and not … actively checked for") |
| Only `motivation.md` joins the backlogs. `image-1.png` and `bug-report.md` stay published | Dev |
| `postponedfeatures.md`, copied in, is the standard backlog source | Dev |
| `kickoff` gets a minimal consistency edit. `vision.md` is committed | Dev |
| `changelog` owns the close procedure (gate, closing note, section, commit) | Agent, so the procedure lives in one place. Open to dev review |
| §1.1's untracking and §1.2's `.gitignore` line move to M6 | Dev, at merge ("all this will be dealt with in m6") |
