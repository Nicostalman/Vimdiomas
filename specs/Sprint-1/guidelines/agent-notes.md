# Sprint 1 — agent notes

> **Closed sprint.** Sprint 1 is finished; this file is a record of what was
> true while it ran. It is not updated by later sprints — anything a later
> sprint revisits belongs in that sprint's `agent-notes.md`.

Agent-maintained companion to the sprint's guidelines. Sprint 1 predates the
`guidelines/` convention, so it has no programmer-written motivation document:
its scope came directly from the original proposal, captured in
[`../roadmap-sprint-1.md`](../roadmap-sprint-1.md).

## Proposed / deferred features

Carried in the roadmap's **Later** section, reproduced here so the register is
complete in one place. None of these were implemented in Sprint 1.

| Item | Source |
| --- | --- |
| Creating directories and files from the app | roadmap-sprint-1 · Later |
| Editing and deleting entries from the TUI (append-only for now) | roadmap-sprint-1 · Later |
| Renaming and deleting categories from the TUI | roadmap-sprint-1 · Later |
| Editing tags from the TUI (read for filtering, written by hand) | roadmap-sprint-1 · Later |
| Shell integration for *Notebook* and *Inspect tree* (needs a sourced zsh function) | roadmap-sprint-1 · Later |
| Other languages beyond Chinese | roadmap-sprint-1 · Later |
| Watch mode (recompile a PDF when its `.md` changes) | roadmap-sprint-1 · Later |
| Search inside entries (hanzi and translations, not just filenames and tags) | roadmap-sprint-1 · Later |

## Assumptions

Recorded as they were made during Sprint 1.

| Assumption | Where it was made |
| --- | --- |
| The source tree is at most three levels: directory → file → category | M5.2 entry screen |
| The user owns the tree structure; the app never creates directories or files | M5.2 entry screen |
| `(uncategorized)` is shown only for files that actually hold loose entries | M5.2 entry screen |
| Browse operates on the compiled notebook tree, not the source tree | M5.3 browse screen |
| `pinyin.py` receives well-formed input; malformed input is unspecified | M2 pinyin |
| Only one language (Chinese) exists, so no notebook selection is needed | roadmap-sprint-1 |
| The notebook and source trees are tracked in git | M0 scaffold |

## Outcome

M0 through M5.3 landed. M6 (seed content) was not implemented — hand-testing
with real content took its place.
