# Vimdiomas

This project is developed under a **spec-driven development (SDD)** workflow. The
specs are not documentation written after the fact — they are where every change
starts.

Convention: **user** is the end user of the program, **dev** is the human driving
development (dev + PO in agile terms), **sh** is the stakeholder, **agent** is you.

## The rule

**Nothing is implemented that is not specified first.** Every change to the code
begins in the spec files and is reflected there — scope in `requirements.md`, work
in `plan.md`, acceptance in `validation.md`, all under the milestone's folder in
`specs/Sprint-N/features/`.

No divergence between the specs and the codebase is tolerated. If something new
comes up mid-implementation — a criterion, a constraint, a decision — update the
corresponding spec file *as it happens*, not at the end. Code that landed without a
spec change behind it is a process error to raise with the dev, not a shortcut to
take.

## Where things live

```
specs/
  current/                  # project-level, spans sprints, edited in place
    mission.md              # what the project is and why
    stack.md                # what it's built with: tech choices, architecture
    design.md               # how it behaves for the user: UX/UI guidelines
    changelog.md            # one section per closed sprint, newest first
  Sprint-N/
    roadmap-sprint-N.md     # the sprint's milestones, M1..Mn
    features/               # one folder per milestone: plan/requirements/validation
    guidelines/
      backlog.md            # dev-written, local-only (gitignored) — read it, never edit it
      notes-sprint-N.md     # agent-maintained: Decisions / Assumptions / Postponed
```

See `specs/current/README.md` for the layout in full, including the older
conventions Sprint 1 and Sprint 2 were written under.

**`stack.md` vs `design.md`:** technology and architecture go in `stack.md`; any
user-facing convention — navigation, keybindings, layout, tone — goes in
`design.md`. A convention that applies across screens is stated once in `design.md`
rather than repeated in each milestone that touches it. Read `design.md` before
speccing anything with a user-facing surface.

**A closed sprint is frozen.** Once `Sprint-N+1` exists, nothing under `Sprint-N/`
is edited again, not even to correct it. Read closed sprints freely — prior
decisions live there — but anything a later sprint revisits is restated in the
current sprint's `notes-sprint-N.md`. A sprint is *closed* when its `## Sprint N`
section is written into `changelog.md`, and *frozen* when the next one opens.

## Routing: which skill to invoke

The workflow is implemented by four skills in `.claude/skills/`. They are
self-contained and authoritative — follow the invoked skill's steps rather than
improvising an equivalent. Invoke them by name when the dev's request matches:

| Skill | Invoke when |
|---|---|
| `kickoff` | A brand-new project is starting and `specs/current/` doesn't exist yet. Runs once, ever. Not applicable to this project — it has already run. |
| `sprint-start` | The dev says a sprint is over, wants the next sprint opened, or has written a new backlog after a round of hand-testing. Also resumes a sprint start interrupted before its roadmap was written. |
| `feature-spec` | The dev says it's time to start the next milestone, asks for a feature spec, or is about to begin implementation of a roadmap item. This is the skill that carries a milestone from branch through spec, implementation, and squash-merged PR. |
| `changelog` | The last milestone of a sprint has merged, the dev says to close the sprint, or `sprint-start` finds the previous sprint not yet closed. This is the skill that closes a sprint: gate, closing note, changelog section, commit on `main`. |

**When the dev asks for feature work without naming a skill** — "add X", "implement
Y", "fix this screen" — that is still `feature-spec`'s territory if it's a roadmap
milestone. Don't open the editor and start writing code; identify the milestone,
invoke `feature-spec`, and let it drive. If the request is not a roadmap milestone
(a one-off fix, a question, an experiment), say so and confirm with the dev how they
want it handled rather than silently working outside the specs.

## Working agreements

- **Interview before speccing.** The roadmap states a deliverable and a done-when
  condition, not the decisions in between. Ask the dev; don't guess the gaps.
- **Stop before declaring done.** A milestone is finished when the dev says so,
  usually after manual testing — not when the agent's own tests pass.
- **Milestone numbering restarts at M1 each sprint.** Numbers are read together
  with their sprint ("Sprint 2 · M1").
- **The dev's own files are theirs.** `backlog.md` and `vision.md` are never
  rewritten, reformatted, or drafted in their author's voice. `backlog.md` is also
  never staged or committed: it is local-only and gitignored, and needs a backup of
  its own because git doesn't keep it.
