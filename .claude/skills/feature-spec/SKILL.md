---
name: feature-spec
description: Start work on the next milestone in the current sprint's roadmap — create its branch and scaffold a spec folder under specs/Sprint-N/features/ with plan.md, requirements.md, and validation.md, then carry it through implementation to a squash-merged PR. Use when the dev says it's time to start the next milestone, wants a feature spec written, or invokes this before beginning implementation of a roadmap item.
---

# Feature spec

Turns the next unstarted milestone in the current sprint's roadmap into a working
branch and a spec folder — `plan.md`, `requirements.md`, `validation.md` — built
from a conversation with the dev, not guessed from the roadmap text alone. Then
carries that milestone through implementation, review, and a squash-merged PR.

Convention: **dev** is the human driving development, **agent** is you.

## The specs layout

```
specs/
  current/
    vision.md, mission.md, stack.md, design.md, roadmap.md, changelog.md   # project-level
  Sprint-N/
    roadmap-sprint-N.md         # the sprint's roadmap
    features/                   # milestone folders for this sprint
      MN-YYYY-MM-DD-feature-name/{plan,requirements,validation}.md
    guidelines/
      backlog.md                 # dev-written, local-only (gitignored); read it, never rewrite it
      notes-sprint-N.md          # agent-maintained: Decisions / Assumptions / Postponed
```

The **current sprint** is the highest-numbered `specs/Sprint-*` directory. Creating
a sprint — its roadmap, its guidelines — is `sprint-start`'s job, not this one's;
this skill assumes the sprint already exists.

**Earlier sprints are frozen.** Everything under a `Sprint-*` directory that isn't
the current one is a record of what was true while that sprint ran: never edited,
never renumbered, never "kept current". Read them freely — they're where prior
decisions live — but anything a later sprint revisits gets restated in the
*current* sprint's `notes-sprint-N.md`, never written back into the old one.

## Workflow

Steps 1 through 9 below are the full milestone cycle, start to merge.

**1. The dev asks to proceed with the next feature.** That's the trigger for
everything that follows.

**2. Confirm there's a git repo and pull `main` to make sure it's current.**

```sh
git rev-parse --show-toplevel   # stop and offer `git init` if this fails
git checkout main && git pull
```

Locate the current sprint and its roadmap:

```sh
ls -d specs/Sprint-* 2>/dev/null | sort -V | tail -1
```

Read `specs/Sprint-N/roadmap-sprint-N.md` from that directory.

- If no `Sprint-*` directory exists, or `specs/current/` is missing, this project
  hasn't been through `kickoff`/`sprint-start` — stop and point the dev there.
- If the current sprint directory exists but has **no roadmap file**, stop and say
  so: a sprint's roadmap is discussed with the dev before its milestones are
  specced. That's `sprint-start`'s job — point the dev there rather than drafting
  one here.
- If the current sprint's roadmap has no unstarted milestones left, the sprint is
  over. Say so and offer `sprint-start` (which first closes the sprint through
  `changelog` if it isn't closed yet); don't append a milestone to a finished
  roadmap, and don't create `Sprint-N+1` yourself.

**3. Read the sprint's guidelines before anything else.** `guidelines/backlog.md` is
the dev's own account of what they want — it carries intent the roadmap compresses
away. `guidelines/notes-sprint-N.md` lists Decisions, Assumptions, and anything
already flagged as Postponed/pending. All three feed the interview in step 5;
`backlog.md` is never edited by you.

`backlog.md` is **local-only and never committed**: it is gitignored, so a fresh
clone doesn't have it, and it needs a backup of its own (Time Machine, iCloud or
similar) because git doesn't keep it. Never stage it. If it's missing — as it will
be in a clone without it — say so, work from the roadmap and the notes, and ask the
dev about any intent the roadmap compressed away.

If this milestone has a user-facing surface, read `specs/current/design.md` too —
it holds the project's standing UX/UI conventions (navigation, keybindings, layout,
tone), and this milestone is expected to follow them rather than invent its own.

**4. Find the next milestone.** Roadmap milestones are ordered by dependency,
listed top to bottom, numbered M1..Mn.

- List existing folders under `specs/Sprint-N/features/` (pattern `MN-*`).
- Match each folder's milestone number against the roadmap to see which milestones
  already have a spec.
- The next milestone is the first one, in roadmap order, with no matching spec
  folder.
- If the match is ambiguous, don't guess — show the dev the roadmap's milestone
  list and ask which one is next.

State which milestone you've identified as next before moving on, so the dev can
correct it.

**5. Create the branch, then interview the dev about the feature spec.**

Derive the slug as `mN-feature-name` from the milestone number and a short
kebab-case name from its title (e.g. `## M2 · Pinyin` → `m2-pinyin`).

```sh
git checkout -b YYYY-MM-DD-mN-feature-name
```

Use the actual current date. If the working tree isn't clean, stop and ask the dev
how to handle the in-progress changes (stash, commit, or branch from here anyway)
rather than branching over them silently.

**Push the branch immediately, if a remote exists** — before any commits exist on
it, not only right before the PR at the end:

```sh
git remote -v          # skip the push below if this is empty
git push -u origin YYYY-MM-DD-mN-feature-name
```

If there's no remote, or the push fails, don't block on it — note it and continue;
the dev can push manually later.

**You must interview the dev** before writing `requirements.md` — the roadmap states
the deliverable and done-when condition, not the decisions in between. Ask:

- What's in scope for this milestone, and what's explicitly deferred?
- Any decisions already made (approach, libraries, interfaces) that constrain the
  implementation?
- Anything about context — prior attempts, related code, constraints from other
  milestones — worth recording?

Come to this already knowing what `backlog.md` and `notes-sprint-N.md` say about
this milestone; ask about the gaps rather than what's already settled. If the
backlog and the roadmap disagree, surface it — don't pick a side silently.

**6. Scaffold the spec folder.** Create
`specs/Sprint-N/features/MN-YYYY-MM-DD-feature-name/` — milestone number first —
with three files:

- **`requirements.md`** — scope, decisions, context, structured from step 5. Include
  the roadmap's own deliverable and done-when text as the anchor the rest of the doc
  elaborates on. Cite the relevant `backlog.md` section where a requirement comes
  from it.
- **`plan.md`** — a series of numbered task groups (not a flat checklist). Each
  group is a coherent chunk of work with a short header and the tasks under it,
  ordered so later groups depend only on earlier ones. Keep groups scoped to what
  this milestone's deliverable actually requires — don't invent extra work.
- **`validation.md`** — how to know the implementation succeeded and can be merged.
  Ground this in the roadmap's done-when condition, made concrete and checkable
  (specific commands, specific fixtures or cases, what a passing result looks
  like). This is the acceptance bar for the branch.

Every modification to scope, plan, or acceptance criteria — from the dev or from
something that comes up mid-implementation — is made through these three files.
**Anything relevant that ends up in the code must be reflected in the md files.**
The specs and the codebase do not diverge: no divergence is expected or tolerated
between them, and a change that starts in the code instead of the spec is a process
error, not a shortcut.

If the change is a **cross-cutting UX/UI convention** — something that applies
beyond this milestone, on every screen — it belongs in `specs/current/design.md`,
not only in this folder's `requirements.md`. Update `design.md` in place when that
happens, and read it before speccing any milestone with a user-facing surface, so
this milestone inherits the conventions rather than reinventing them.

**7. Iterate on the spec with the dev before implementation starts.** The dev
reviews `plan.md`/`requirements.md`/`validation.md` and suggests modifications; you
update the files; repeat until the dev is ready for you to start writing code. Only
after this loop settles does implementation begin.

**8. Implement, and run your own tests.** Work through `plan.md`'s task groups in
order. If a new criterion or characteristic arises during implementation, update
the corresponding md file(s) immediately — don't let the code and the spec drift
apart, even temporarily.

**9. Hand off for human feedback, then merge.** When implementation is nearly done,
stop and wait for the dev's feedback — possibly manual testing — rather than
declaring the milestone finished yourself. Reiterate if they ask for changes
(looping through step 8 again). Once they're satisfied:

**Merge and clean up**, with this exact sequence, run every time:

```sh
gh pr create …                               # the PR
gh pr merge --squash --delete-branch         # squash-merges, deletes the remote branch
git checkout main && git pull                # leave the branch, take the squash commit
git branch -D YYYY-MM-DD-mN-feature-name 2>/dev/null || true   # -D, not -d: see below
git push origin --delete YYYY-MM-DD-mN-feature-name 2>/dev/null || true   # in case the remote one survived
git fetch --prune                            # drop the stale origin/… ref
git branch                                   # lists main only
```

Why `-D`: a squash merge puts one new commit on `main`, so the branch's own commits
never become ancestors of `main`, and `git branch -d` refuses to delete it as
"not fully merged". That refusal is how branches used to be left behind. `-D` is
safe **here and only here**, because the branch was merged as a PR a moment ago in
this same step. Don't "fix" it back to `-d`, and don't use `-D` anywhere else.
`gh pr merge --delete-branch` often deletes the local branch itself, which is why
the `-D` line tolerates the branch being gone already. The last line, `git branch`
listing `main` only, is what confirms the cleanup ran.

Without a remote (no `origin`, or no `gh`), merge locally instead —
`git checkout main && git merge --squash YYYY-MM-DD-mN-feature-name && git commit` —
then run the same `git branch -D` and skip the remote lines.

Then update `guidelines/notes-sprint-N.md` on `main`: move this milestone's entries
from open Decisions/Assumptions into their settled form, and add anything newly
deferred to Postponed/pending. Commit and push it.

Then report the merge and ask the dev whether to move on to the next milestone
(back to step 1) — don't auto-start the next one.

**If this was the roadmap's last milestone,** don't look for more work in this
sprint. Ask the dev whether to **close the sprint now**. On a yes, invoke the
`changelog` skill, which runs the close (gate, closing note, changelog section,
commit on `main`). On a no, report that the sprint is still open and that
`sprint-start` will close it before opening the next one.

## Notes

- One spec folder per milestone. If the dev wants to split a milestone into
  multiple smaller phases, that's a decision to surface and confirm, not to make
  silently.
- `plan.md`, `requirements.md`, and `validation.md` are living documents for the
  branch — this skill creates the initial versions and keeps them current through
  step 8, but don't re-run steps 4–5 (finding the milestone, branching) if the
  folder for the current branch already exists; treat that as "already started" and
  ask the dev what they want updated instead.
- Starting a **new sprint** is not this skill's job — that's `sprint-start`. This
  skill assumes a sprint with a roadmap already exists.
- Don't run the `changelog` skill mid-milestone; it closes a sprint, and is invoked
  from step 9 only after the last milestone has merged (or when the dev asks to
  close the sprint).
