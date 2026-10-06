# specs/

```
specs/
  current/
    mission.md             # stable, sprint-independent
    stack.md                # stable, sprint-independent: tech choices, architecture
    design.md                # stable, sprint-independent: UX/UI guidelines
    changelog.md              # one section per closed sprint, newest first
    README.md                  # this file
  Sprint-N/
    roadmap-sprint-N.md   # discussed before the sprint starts
    features/             # one folder per milestone worked in this sprint
      ...
    guidelines/
      backlog.md           # written by the dev, not the agent; local-only (gitignored)
      notes-sprint-N.md    # agent-maintained: Decisions / Assumptions / Postponed
```

- `mission.md`, `stack.md` and `design.md` live under `current/` and are never
  moved into a sprint — they describe the project, not a slice of work.
- `stack.md` is what the project is built with; `design.md` is how it behaves for
  the user. Cross-cutting UX/UI conventions (navigation, keybindings, layout) are
  stated once in `design.md` rather than per milestone.
- `changelog.md` gets a new `## Sprint N` section when that sprint closes, written
  by the `changelog` skill, listing the milestones it shipped. That section is the
  mark that the sprint is closed. It is not a commit log.
- A sprint's roadmap sits directly in `Sprint-N/`, named `roadmap-sprint-N.md`. A
  new one is discussed before each sprint begins.
- Every spec folder created while working a milestone belongs to the sprint that
  was current when it was created; it is never moved afterwards.
- `guidelines/backlog.md` is the dev's own text — hand-testing notes, intent,
  complaints. Agents read it and do not rewrite it. It is **local-only and never
  committed**: gitignored, so a fresh clone doesn't have it, and it needs a backup
  of its own (Time Machine, iCloud or similar) because git doesn't keep it. Sprints
  3–6 committed theirs; those were untracked in Sprint 7 and stay on disk.
- `guidelines/notes-sprint-N.md` is the agent's ledger over that backlog:
  Decisions, Assumptions, and Postponed/pending items.

## Sprint-1 and Sprint-2 predate this layout

Both were written before the `current/`, `backlog.md`, and `MN-YYYY-MM-DD-*`
conventions existed, and both are closed. They are left exactly as they are, not
retrofitted:

- Sprint-1 has no `backlog.md`/`motivation.md` at all — its scope came directly
  from the original proposal in `roadmap-sprint-1.md`.
- Sprint-2 has `guidelines/motivation.md` (not `backlog.md`) and
  `guidelines/agent-notes.md` (not `notes-sprint-2.md`). `motivation.md` is its
  backlog under the old name, and is local-only and gitignored like any other.
- Both sprints' `features/` folders use `YYYY-MM-DD-mN-slug`, not
  `MN-YYYY-MM-DD-slug`.

The new naming applies starting Sprint-3.

## Process rules live elsewhere

Governance — when a sprint counts as closed, what each skill does step by step,
how `notes-sprint-N.md` is structured — is authoritative in the skills under
`.claude/skills/`, not duplicated here. This file only documents the folder
layout.
