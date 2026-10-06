---
name: sprint-start
description: Open a new sprint under specs/ — verify the previous sprint is closed, create Sprint-N with its features/ and guidelines/ folders, take in the dev's backlog.md, and write roadmap-sprint-N.md and notes-sprint-N.md. Also resumes a sprint start that was interrupted before its roadmap was written. Use when the dev says a sprint is over, wants to start the next sprint, or has written a new backlog after a round of hand-testing.
---

# Sprint start

Opens the next sprint. This is the conversation that happens *before* any milestone
is specced: making sure the sprint that ended is closed (closing it through
`changelog` if it isn't), creating `Sprint-N/`, placing the dev's backlog, and
agreeing on the roadmap.

`feature-spec` picks up from here. This skill never creates a spec folder or a
milestone branch. `kickoff` runs before this skill ever runs for the first time —
if `specs/current/` doesn't exist yet, this is a brand-new project and `kickoff`
needs to run first, not this skill.

Convention: **dev** is the human driving development, **sh** is the stakeholder,
**agent** is you. The backlog here is dev-authored (not sh-authored — the sh's
input lives in `specs/current/vision.md`, handled by `kickoff`).

## The layout

```
specs/
  current/
    vision.md, mission.md, stack.md, design.md, roadmap.md, changelog.md   # project-level, never moved
  Sprint-N/
    roadmap-sprint-N.md
    features/                       # filled by feature-spec, one folder per milestone
    guidelines/
      backlog.md                    # dev-written, local-only (gitignored); you never write, edit or stage it
      notes-sprint-N.md             # agent-maintained: Decisions / Assumptions / Postponed
```

## The rule that governs everything here

**A closed sprint is frozen.** Once `Sprint-N+1` exists, nothing under `Sprint-N/`
is edited again — not its roadmap, not its `features/` folders, not
`notes-sprint-N.md`, not to "keep it current" and not to fix a decision the new
sprint reverses. Its files are a record of what was true while it ran.

When the new sprint revisits something the old one assumed or deferred, that
belongs in the **new** sprint's `notes-sprint-N.md`, restated there. Never a status
column in the old file, never a forward reference like *"revisited in Sprint 3"*
written into Sprint 2. If you catch yourself opening a closed sprint's file to
write, stop — the content belongs in the current sprint.

Reading closed sprints is not just allowed, it's step 2.

## Workflow

**1. Work out where things stand.**

```sh
ls -d specs/current 2>/dev/null
ls -d specs/Sprint-* 2>/dev/null | sort -V | tail -1
```

- **No `specs/current/`** — the project hasn't been through `kickoff`. Stop and
  point the user there; don't improvise `vision.md`/`mission.md`/`stack.md`/
  `design.md` here.
- **`specs/current/` exists but no `Sprint-*` directory** — this is the first
  sprint. Skip the closed-sprint gate (step 2) and go straight to step 3 with `N=1`.
- **The latest sprint has no `roadmap-sprint-N.md`** — a sprint start was
  interrupted partway. **Resume it.** That sprint is the one you're opening; don't
  compute the next integer, don't create a new directory. Skip to whichever of
  steps 3–5 hasn't been done (check for `guidelines/backlog.md` and
  `guidelines/notes-sprint-N.md`) and carry on from there to step 6. Say which steps
  you're skipping and why.
- **The latest sprint has a roadmap** — it's a real, started sprint. The new one is
  the next integer, and step 2 decides whether it may be opened at all.

**2. A sprint does not start until the last one is closed.** This is a gate, not a
formality. The previous sprint is **closed** when `specs/current/changelog.md` has
a `## Sprint N` section for it — that section is the checkable mark of a close:

```sh
git checkout main && git pull
grep -q '^## Sprint N$' specs/current/changelog.md && echo closed
```

- **The section is present:** the gate passes. Nothing is written into the old
  sprint.
- **The section is missing:** the sprint was never closed. Invoke the `changelog`
  skill to close it now — its gate settles any outstanding milestones with the dev,
  then it writes the closing note, the changelog section and the `Close Sprint N`
  commit. Do not create the new sprint directory until that close is done — once
  it exists, the old sprint is frozen and the record can no longer be corrected.

Either way, read — never edit — the old sprint before proposing anything:

- Its roadmap and `features/`: which milestones landed, and which were deferred.
- Its `guidelines/notes-sprint-N.md`: the closing note, open Decisions/Assumptions,
  and anything in the Postponed/pending section that might now belong in the new
  sprint.

Then tell the dev what carries over: deferred milestones and anything still open in
the Postponed/pending section. Ask whether each enters the new sprint — don't
decide it yourself, and don't assume a deferred milestone is automatically in
scope.

**3. Create the sprint.**

```sh
mkdir -p specs/Sprint-N/features specs/Sprint-N/guidelines
```

From this point `Sprint-N-1/` is frozen.

**4. Find and place the backlog.** `guidelines/backlog.md` is written by the dev,
not by you: **every sprint starts with a backlog written by the dev.**

**A backlog is local-only and never committed.** It lives on disk in its
`guidelines/` folder and is gitignored (`specs/Sprint-*/guidelines/backlog.md`), so
a fresh clone doesn't have it, and it needs a backup of its own (Time Machine,
iCloud or similar) because git doesn't keep it. Never `git mv` it, never
`git add` it.

**The standard source is `postponedfeatures.md` at the project root** — the dev's
living deferred list, itself gitignored. Look for it first; say what it opens with
and confirm with the dev that it is this sprint's backlog. Once confirmed, **copy**
it, don't move it:

```sh
cp postponedfeatures.md specs/Sprint-N/guidelines/backlog.md
```

The root file stays the dev's and goes on being their living list; the copy is the
sprint's frozen snapshot.

**Fallback:** if `postponedfeatures.md` is absent, look for another root-level
markdown file the dev wrote:

```sh
ls *.md
git status --short          # a brand-new, untracked .md at the root is the usual shape
```

Candidates are root-level markdown files that aren't the project's standing docs
(`readme.md`, `CHANGELOG.md`, `CLAUDE.md`, `LICENSE.md`). If exactly one plausible
candidate exists, say which file you believe it is and what it opens with, and ask
the dev to confirm. If several are plausible, list them and ask. Never guess
silently. Place it with plain `cp` (or `mv` if the dev asks for a move) — never
`git mv`.

**Verify it is ignored**, whatever the source:

```sh
git check-ignore -q specs/Sprint-N/guidelines/backlog.md && echo ignored
git status --short          # must not list the backlog
```

If the check fails, the ignore rule is missing — as in a project that adopted these
skills without it. Add `specs/Sprint-*/guidelines/backlog.md` and the root source
file's name to `.gitignore`, and re-check, before anything is committed.

**Companions** the backlog references (a bug report, an image) are copied into the
same `guidelines/` folder and committed like any other sprint file. Only
`backlog.md` is local-only.

Keep the text **verbatim**: don't reformat, don't reorder, don't fix its typos,
don't summarize it, don't add a heading.

If no such file exists, say so and ask — the dev may have it elsewhere, or may not
have written one yet. Never draft a backlog in their voice. Kickoff aside, every
sprint needs one; don't invent milestones from conversation alone.

**5. Draft `guidelines/notes-sprint-N.md`.** This is yours to write. It has exactly
three sections, and it **grows as the sprint progresses** — this first draft is a
seed, not a final version. Standardize the format using tables in each section:

- **Decisions** — choices made while turning the backlog into a roadmap (approach,
  scope calls, anything the dev settled during this conversation), plus any
  closing-sprint decisions carried in from step 2.
- **Assumptions** — everything the sprint takes as given that isn't verified in code
  or stated in the roadmap. Things the dev asserted in passing are exactly what
  this table is for.
- **Postponed features / pending** — ideas AND pending things raised during the
  sprint that will not be implemented now, for simplicity's sake. The canonical
  example: a menu option whose real implementation is out of scope gets left as a
  dummy button, and an entry here says it needs real implementation in a future
  sprint. Deferred milestones from step 2 land here too.

**6. Discuss the roadmap, then write it.** A backlog is a list of features; a
roadmap is an ordered, numbered set of milestones. Turning one into the other is a
conversation, not a transcription. Work through with the dev:

- Which backlog items are in this sprint and which stay deferred.
- What order they go in — dependency order, not the order they were written in.
- Where one item is really several milestones, or several are really one.
- What "done" means for each, concretely enough to check.

Then write `specs/Sprint-N/roadmap-sprint-N.md`. This file **clarifies the backlog**
and is **a summary of the sprint** that stays **easily readable** — each feature
numbered **M1 to Mn**. Match the previous sprint's roadmap
in shape if one exists: a short preamble stating the ordering principle, then one
section per milestone with a clear deliverable and a done-when condition, then
anything explicitly deferred.

**Milestone numbering restarts at M1 in every sprint.** Sprint 2's first milestone
is M1, not M7. Milestone numbers are read together with their sprint ("Sprint 2 ·
M1"); don't carry numbering across sprints, and don't ask — this is settled.

**7. Report** the sprint directory, where the backlog came from, the milestone list
agreed on, and what carried over or was dropped — then stop. Speccing the first
milestone is `feature-spec`'s job, a separate invocation.

## Notes

- One sprint directory per sprint, created once. If a sprint's roadmap needs to
  change mid-sprint, that's an edit to the current `roadmap-sprint-N.md`, not a new
  sprint.
- The roadmap file is what marks a sprint as started. A `Sprint-N/` without one is
  an unfinished sprint start to be resumed, never a reason to open `Sprint-N+1`.
- Being asked to start a sprint is not evidence the last one is closed. The backlog
  arrives while the previous sprint still has open milestones more often than not —
  that's the case step 2 exists for.
- Don't renumber, move, or "tidy" the `features/` folders of any sprint, including
  the current one. Their names are how the roadmap maps onto history.
- `specs/current/mission.md`, `stack.md`, `design.md`, and `roadmap.md` describe the
  project, not a slice of work. If this sprint changes any of them, edit them in
  place under `specs/current/` — they are the files that legitimately span sprints.
  A cross-cutting UX/UI convention agreed while planning the sprint belongs in
  `design.md`, not restated in each milestone that happens to touch it.
- This skill doesn't close the sprint it opens. That sprint is closed by the
  `changelog` skill — from `feature-spec` once its last milestone merges, when the
  dev asks, or from the next `sprint-start`'s step 2 as a fallback.
- `backlog.md` is never staged or committed, in this skill or any other. When
  committing the new sprint, stage files by name, never `git add -A`.
