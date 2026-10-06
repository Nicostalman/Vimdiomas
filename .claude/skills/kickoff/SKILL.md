---
name: kickoff
description: One-time project initialization for spec-driven development — create specs/current/ from the stakeholder's vision.md, and draft mission.md, stack.md, design.md, roadmap.md and changelog.md. Use when a brand-new project is starting under this SDD workflow, before any sprint exists.
---

# Kickoff

The very first step of the SDD workflow, run once per project, before `sprint-start`
ever runs. It turns the stakeholder's vision into the five standing documents the
rest of the workflow builds on, all living under `specs/current/`.

Convention used throughout this workflow: **user** is the end user of the program
being built, **dev** is the human driving development (dev + PO in agile terms),
**sh** is the stakeholder, **agent** is you.

## The layout this skill creates

```
specs/
  current/
    vision.md        # sh-authored — you never write or edit this
    mission.md        # agent-drafted: clean, organized, expanded version of vision
    stack.md           # agent-drafted: tech stack, coding conventions, architecture
    design.md           # agent-drafted: UX/UI guidelines
    roadmap.md           # agent-drafted: path to MVP, foundation-first
    changelog.md          # agent-created empty/seeded here; filled in after each sprint closes
```

`sprint-start` picks up from here — it creates `specs/Sprint-1/` etc. alongside
`specs/current/`. This skill never creates a sprint folder.

## Workflow

**1. Confirm there's a git repo.** If `git rev-parse --show-toplevel` fails, tell the
user there's no git history to anchor specs to, and stop — offer `git init` if that
looks like the fix.

**2. Check this hasn't already run.** Look for `specs/current/` and for a
pre-existing flat layout (`specs/mission.md`, `specs/stack.md` at the top level with
no `current/` folder — an older or partially-migrated layout). If `specs/current/`
already has all five agent-drafted files, this project is already kicked off — say
so and stop; point to `sprint-start` instead. If a flat `specs/mission.md` /
`specs/stack.md` exist without `current/`, don't silently reorganize them — show the
user what you found and ask whether to migrate those files into `specs/current/` or
to treat this as a fresh kickoff alongside them.

**3. Find `vision.md`.** This file is written by the stakeholder, not you — never
draft it in their voice, and never fabricate one to keep things moving. Look for it:

```sh
ls *.md specs/*.md 2>/dev/null
git status --short
```

It may be sitting at the project root, where the dev's hand-written docs usually
start out, or already placed under `specs/`. If you find one
plausible candidate, confirm with the user before moving it; if several are
plausible, list them and ask. If none exists, stop and ask the sh/dev to write one —
kickoff cannot proceed without it, since `mission.md` is explicitly meant to
organize and expand it, not invent it.

Once confirmed, place it (using `git mv` if tracked, plain `mv` otherwise) at
`specs/current/vision.md`, verbatim — no reformatting, no fixing typos, no added
headings. `vision.md` **is committed**: it is the stakeholder's document, not a
backlog, and the rule that keeps sprint backlogs local-only doesn't apply to it.

**4. Interview the dev, then draft the four planning documents.** These are yours
to write, but not to guess — where the vision leaves gaps (stack choices, scope
boundaries, sequencing), ask the dev rather than picking silently. Draft:

- **`mission.md`** — a clean, organized, expanded version of the vision. Same
  intent, clearer structure; this is not a place to introduce new goals the vision
  didn't imply.
- **`stack.md`** — the technical side: language/framework choices, coding
  conventions, architecture. Ask the dev about anything the vision doesn't settle
  (e.g. specific libraries, target platforms). UX/UI does **not** go here — it has
  its own document, below.
- **`design.md`** — the UX/UI guidelines: interaction and navigation conventions,
  keybindings, layout and visual language, copy/tone rules, accessibility calls —
  whatever governs how the thing looks and how the user moves through it. This is
  the counterpart to `stack.md`: `stack.md` answers *what it's built with*,
  `design.md` answers *how it behaves for the user*. When a convention is
  cross-cutting (applies on every screen, not just the feature that introduced it),
  it belongs here rather than being restated per milestone.
- **`roadmap.md`** — the path to MVP. The emphasis is the initial foundation: it
  should read as elegant, scalable, and maintainable groundwork, not a full feature
  list. This is a project-level roadmap, coarser-grained than a sprint's
  `roadmap-sprint-N.md` — it says where the project is headed across sprints, not
  what M1..Mn are for the sprint about to start.

Write all four under `specs/current/`.

**5. Create `changelog.md`.** Seed `specs/current/changelog.md` as an empty record
ready to receive entries:

```markdown
# Changelog
```

Do not backfill it from git history at kickoff — this changelog is fed by the
`changelog` skill **after each sprint closes**, one section per sprint, not by raw
commit history. See that skill for the format.

**6. Report** what was created, where `vision.md` came from, and a one-line summary
of the mission/stack/design/roadmap you drafted — then stop. Opening the first
sprint is `sprint-start`'s job, a separate invocation.

## Notes

- `mission.md`, `stack.md`, `design.md`, and `roadmap.md` are living documents —
  they get revised as the project evolves. Edit them in place under
  `specs/current/` when that happens; don't fork per-sprint copies.
- `vision.md` is the one document here you never edit, only relocate once. If the sh
  revises their vision later, that's their edit to make, not yours.
- This skill runs once. If the user asks to "kick off" again on a project that
  already has `specs/current/`, treat it as a request to review/update those files,
  not to recreate them from scratch.
