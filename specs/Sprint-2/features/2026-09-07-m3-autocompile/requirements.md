# M3 · Autocompile — requirements

Roadmap: [`../../roadmap-sprint-2.md`](../../roadmap-sprint-2.md#m3--autocompile).
Proposal `#18` (see [`../../guidelines/agent-notes.md`](../../guidelines/agent-notes.md)).

## Deliverable (from the roadmap)

A file is compiled automatically when

1. at least one entry has been added to it and the cursor then moves to a
   different file — or to a category inside a different file; and
2. the entry screen is left altogether.

## Done when (from the roadmap)

- Entering a word in `Food.md`, moving the cursor to a category in another
  file, and then leaving the screen produces an up-to-date `Food.pdf` with no
  visit to *Compile*.
- A cursor move with no new entries compiles nothing.
- The UI stays responsive while a compile runs.

## Scope decision made for this phase (narrows the deliverable)

**Only condition 2 is implemented.** The programmer changed scope during this
spec's discussion: autocompile fires when the entry screen is left
altogether, not additionally on every cursor move to a different file/category
(condition 1). Rationale given: condition 1 added per-move complexity
(tracking "current file" vs. "file(s) touched", deciding what counts as
"different") for a benefit — earlier compiles while still inside the entry
screen — that isn't needed if everything gets compiled on exit anyway.

This still satisfies the roadmap's **Done when** bar as written: the example
scenario (enter a word, move the cursor, leave the screen) still ends with an
up-to-date `Food.pdf`, because the compile fires on exit regardless of how
many files were touched or how the cursor moved in between. "A cursor move
with no new entries compiles nothing" holds trivially — no compile happens on
any cursor move now. "UI stays responsive" still applies to the exit-triggered
compile.

Condition 1 (compile-on-file-switch, while still inside the entry screen) is
**not** carried to *Later* as a numbered deferred item — it was a mechanism
proposed to reach the same end state sooner, not a feature in its own right,
and the programmer's own account is that it isn't needed.

## Design decisions made for this phase

1. **Dirty tracking**: `EntryScreen` keeps `self._dirty_files: set[Path]`,
   populated with `target.file_path` on every successful `_create_entry()`
   call (i.e., every entry actually saved to disk). No per-cursor-move
   tracking needed now that condition 1 is out of scope.

2. **Exit hook**: `EntryScreen.on_unmount()` triggers the autocompile pass.
   `on_unmount` is Textual's own lifecycle hook, fired whenever the screen is
   removed regardless of the navigation path that caused it (today, only
   `q` via `NavigableScreen.action_back_or_quit`) — more robust than
   duplicating the "is an `Input` focused" guard that `action_back_or_quit`
   already applies before it ever pops the screen.

3. **Must not block leaving the screen**: compiles run via
   `self.app.run_worker(..., thread=True)`, **owned by the App, not the
   screen**. This is load-bearing, not a style choice: Textual's
   `Widget._on_unmount` calls `self.workers.cancel_node(self)`, which cancels
   any worker owned by the screen the moment it unmounts. A worker started
   with `self.run_worker(...)` (screen-owned) would be cancelled before a
   slow pandoc/xelatex compile could finish. Starting it via
   `self.app.run_worker(...)` instead ties its lifetime to the App, which
   doesn't unmount when a screen pops, so the compile actually completes
   after `q` has already returned the user to the previous screen.

4. **Feedback**: silent on success (autocompile is meant to be invisible —
   "the user should never have to remember to compile"); a visible
   `self.app.notify(..., severity="error")` if a compile raises (pandoc/
   xelatex failure, e.g. `subprocess.CalledProcessError`), naming the file,
   so a broken PDF isn't discovered by surprise later. Since compiles run on
   a worker thread, the notify call is dispatched via
   `self.app.call_from_thread(...)` — Textual requires thread-safe re-entry
   into the app for UI-touching calls made from a thread worker.

## Context / constraints from other milestones

- M1 already settled that `q` never loses *entered* data because entries save
  to disk immediately on Create — M1 deliberately left compile-on-exit out of
  its own scope, reserving it for this milestone (see Sprint 2's
  `agent-notes.md` Decisions table). This milestone is what fulfills that.
- `compile_all()` (`src/idiomas/compile.py`) already has an mtime-based
  "skip if the PDF is newer than the source" check for the manual *Compile*
  menu action — unrelated to this milestone's dirty-tracking (which tracks
  *this session's* edits, not file timestamps), but the same
  source-root-relative-to-notebook-root path mapping is needed here and
  should be factored out of `compile_all` into a shared helper rather than
  duplicated.
