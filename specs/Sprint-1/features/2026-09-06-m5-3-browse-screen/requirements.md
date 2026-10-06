# M5.3 · Browse screen — Requirements

## Roadmap anchor

**M5.3 deliverable.** Fuzzy filename search plus a tag filter over `tag_index()`.

**M5's overall Done when** was already fully checked in M5.2 (entry-writing). This phase's own bar is narrower: the browse/fuzzy-search/tag-filter behavior works as described, over the right tree.

## Scope

Confirmed with the user — this phase is scoped more narrowly than "browse the vocabulary": **Browse operates over the compiled `notebook/` tree (PDFs), not the `source/` (`.md`) tree.** Selecting a result opens it in the OS's default PDF viewer (macOS `open`). Browsing/previewing `.md` source files themselves is explicitly out of scope for now (the user's own words: "this function is not available for now in the md tree").

In scope:

- `src/idiomas/tui/screens/browse.py` — `BrowseScreen`, replacing M5.1's `Browse` placeholder.
- **Filename fuzzy search**: an `Input` field; typing filters the list of `.pdf` files under `config.notebook_root` (found via a plain recursive walk, mirroring `compile_all`'s own mirroring logic) using M3's `fuzzy()` against each PDF's notebook-relative path (e.g. `Vocabulary/Food`), so same-named files in different directories stay distinguishable.
- **Tag filter**: a second `Input` field (confirmed with the user — free-text for now; a future phase may switch this to a selectable list of known tags, noted as a likely follow-up, not built here). Typing a tag narrows results to PDFs whose *source* `.md` (via M3's `tag_index()` over `config.source_root`) carries that exact tag. An empty tag field applies no tag constraint. Only files with an existing compiled PDF ever appear — a tag match whose `.md` hasn't been compiled yet is silently not shown, consistent with "Browse operates over the notebook tree."
- Both filters combine (AND): the visible list is the fuzzy-ranked filename matches, further restricted to those also carrying the typed tag (if any).
- **Selecting a result** (Enter, or a dedicated "Open" action) shells out to the OS's default PDF viewer via `open <path>` (macOS, per `mission.md`'s single-platform scope — no cross-platform fallback needed).
- A results list (`ListView`/`OptionList`) showing the ranked/filtered matches; empty state shown when nothing matches.

Explicitly deferred:

- Browsing or previewing `.md` source files — confirmed out of scope for this phase.
- A selectable list of known tags (instead of free-text) — noted by the user as a likely future want, not built now.
- Any editing, deletion, or content preview of the underlying vocabulary — unchanged from the roadmap's "Later" section.

## Decisions

- **Browse is notebook-tree-only**, confirmed explicitly by the user, overriding what might otherwise be assumed (browsing the source vocabulary tree). This is a deliberate, narrower reading of the roadmap's terse M5.3 text.
- **Tag filter is free-text for now**, confirmed with the user, with a selectable-list version flagged as a plausible future iteration (not scheduled, not designed further here).
- **Opening a PDF shells out to `open`** (macOS-specific), matching `mission.md`'s single-platform scope — no dependency added, no cross-platform abstraction built for a single-user macOS tool.
- **Tag data still comes from the source tree** (`tag_index()` over `config.source_root`) even though results are notebook PDFs — tags are only ever recorded in `.md` files; the notebook mirror carries no tag information of its own. Mapping from a tagged source path to its PDF path reuses the exact same relative-path mirroring logic as `compile_all()`.

## Context

- Builds on M3 (`fuzzy`, `tag_index`) and M4 (`compile_all`'s mirroring convention: `source_root/rel.md` ↔ `notebook_root/rel.pdf`) and M5.1 (replaces the `Browse` placeholder).
- Since this only opens an external viewer and doesn't write any files, there's less at stake than M5.2's real file-writing; tests can mock the `open` subprocess call rather than needing a real GUI PDF viewer in CI-like conditions.
