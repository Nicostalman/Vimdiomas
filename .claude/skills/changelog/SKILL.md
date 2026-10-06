---
name: changelog
description: Close a sprint — gate its milestones, write its closing note, and add its section to specs/current/changelog.md (grouped by sprint, newest first, numbered by milestone), committed on main. The changelog section is the mark that the sprint is closed. Use when the last milestone of a sprint has merged (invoked by feature-spec), when the dev says to close the sprint, or when sprint-start finds the previous sprint not yet closed.
---

# Changelog

Runs the **close of a sprint**, and maintains `specs/current/changelog.md` as the
record of what shipped, grouped by sprint, newest sprint first. The file is created
once at `kickoff` and **gets a section when each sprint closes** — it is not a raw
git-log dump, and it is not touched mid-sprint.

A sprint's `## Sprint N` section in `changelog.md` is the checkable mark that the
sprint is **closed**. `sprint-start`'s gate tests for exactly that. The close
procedure lives only here; the other skills invoke this one rather than restating
it. It is invoked:

- by `feature-spec` step 9, when the roadmap's last milestone has merged and the
  dev says yes to closing the sprint;
- by the dev directly ("close the sprint"), even with milestones still
  outstanding — the gate below settles those;
- by `sprint-start` step 2, when it finds the previous sprint has no changelog
  section yet.

Closed is not frozen. A sprint freezes when `Sprint-N+1` exists. Between its close
and the next `sprint-start`, its notes can still take a correction.

## Why sprint-level, not commit-level

The old changelog approach recorded one bullet per git commit. This one instead
records one bullet per **milestone**, numbered the way the sprint's own roadmap
numbered it (`Sprint N · M<k>`). A milestone is usually many commits squashed into
one PR merge; the changelog's job is to say what feature landed, not to mirror
commit history. If the dev wants raw commit history, that's what `git log` is for.

## Format

```markdown
# Changelog

## Sprint 2
- M1 · Navigation conventions
- M2 · Entry screen corrections
- M3 · Autocompile
- M4 · macOS input-method switching

## Sprint 1
- M0 · Scaffold
- M1 · Data layer
- M2 · Pinyin
- M3 · Discovery and search
- M4 · Compile
- M5.1 · Main menu
- M5.2 · Entry screen
- M5.3 · Browse screen
```

- One `##` heading per sprint, **newest sprint first**.
- One bullet per completed milestone, in roadmap order, `M<k> · Title`.
- A milestone that was **dropped** (never implemented, not deferred) is omitted —
  it never shipped. A milestone **deferred** to a later sprint is also omitted from
  the sprint that deferred it; it appears under whichever sprint eventually ships
  it.
- No commit hashes, no per-commit bullets, no marker comment — this file is
  regenerated per-sprint from each sprint's own roadmap and `features/` folder, so
  there's nothing to diff against a stale pointer for.

## Workflow

The close runs on `main`, **after** the last milestone's squash-merge — never on a
feature branch, and never before the merge it records.

**0. Confirm there's a git repo and that `specs/current/changelog.md` exists.** If
it doesn't, this project hasn't been through `kickoff` — stop and point the dev
there; don't create the file from scratch here. Then get onto a current `main`:

```sh
git checkout main && git pull
ls -d specs/Sprint-* 2>/dev/null | sort -V | tail -1
```

The sprint being closed is the highest-numbered `Sprint-*` — the current one, or,
when `sprint-start` invokes this, the one it is about to open the next sprint after.

**1. Gate.** Read `specs/Sprint-N/roadmap-sprint-N.md` and list its
`features/` folders. A sprint can close when every roadmap milestone either has a
spec folder in `features/` or has been explicitly deferred or dropped by the dev.
Nothing else closes it — not "the interesting parts are done", not a long gap since
the last commit, not the existence of a new backlog file.

If milestones are still outstanding, **stop and list them.** Ask the dev, for each
one, whether it is finished, deferred to the next sprint, or dropped outright. Only
their answer closes it.

**2. Closing note.** In `specs/Sprint-N/guidelines/notes-sprint-N.md`'s Decisions
section, record a short closing note: what landed, what was dropped, and what
carries forward (deferred milestones, and anything still open in Postponed/pending
that the next sprint should be offered).

**3. Changelog section.** If a `## Sprint N` heading already exists, the changelog
is current for that sprint — make no edit, unless the dev specifically points out a
milestone that's missing (e.g. one that finished after the changelog was last
written). Otherwise, build the milestone list: the roadmap gives the numbers and
titles, in roadmap order; `features/` (folders named `MN-YYYY-MM-DD-*`) confirms
which got a spec folder and merged; the notes' Postponed/pending section and the
gate's answers say what was deferred or dropped, so it's excluded rather than
guessed at. Insert the new `## Sprint N` section above the existing top heading
(or as the first section if the changelog is still empty), with one bullet per
completed milestone as shown in the format above.

**4. Commit and push on `main`**, as one commit holding the closing note and the
changelog section:

```sh
git add specs/Sprint-N/guidelines/notes-sprint-N.md specs/current/changelog.md
git commit -m "Close Sprint N"
git push                     # skip if there's no remote
```

Closing commits go straight to `main`, the way sprint-notes commits always have.
Stage only those two files by name — never `git add -A`, which could pick up a
backlog if its ignore rule were ever missing.

**5. Report** what was added — e.g. "Closed Sprint 2: 4 milestones (M1–M4), M5
deferred." — or that the changelog was already current for that sprint. Then say
that `sprint-start` is next, as a separate invocation. If `sprint-start` invoked
this, hand back to it instead.

## Notes

- This groups by **sprint and milestone**, never by commit or date. If the dev
  wants a commit-level history, use `git log` directly.
- Don't rewrite or reword existing sprint sections when adding a new one; only ever
  insert a new section above the existing content.
- Never edit a milestone's title here to match the branch/folder slug — use the
  title as written in that sprint's `roadmap-sprint-N.md`, since that's the
  human-readable one.
