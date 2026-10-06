# M3 · One tree widget — requirements

## Anchor (from `roadmap-sprint-3.md`)

**Deliverable.** The tree behaviour and styling currently living in `EntryTree`
is extracted into a shared base widget with a single home, alongside the
existing `NavigableScreen`/`VimOptionList`/`PanelAwareInput` family in
`tui/screens/base.py`. `EntryScreen` adopts it and is **visually and
behaviourally identical** — that identity is the milestone's whole risk. The
base carries what every tree in the app shares — the aesthetic of the entry
screen's left panel, the vim keys, no horizontal scrollbar, content-sized
view — and leaves what differs (M4's category-leaves vs. file-leaves) to
subclasses. The convention is recorded in `design.md`.

**Done when.** `EntryScreen`'s tree renders identically to before — verified by
the dev's own eye, not only by the tests; `tests/test_tui_entry_screen.py`
passes unchanged where it can; the base widget is documented in `design.md`;
and no tree styling remains duplicated outside it.

## Scope

- Not a feature. No new user-visible behavior. This is a pure refactor —
  `EntryScreen` must look and behave exactly as it does today.
- Extracted into the base widget: the `j`/`k` cursor-down/cursor-up bindings,
  the `shift+left`/`shift+right` → `screen.panel_prev`/`panel_next` dispatch
  bindings, and the tree's shared aesthetic (bordered, no horizontal
  scrollbar, content-sized width).
- **Not** extracted, because it is entry-specific rather than shared tree
  behavior: `NodeData`, `NodeKind`, `VALID_TARGET_KINDS`, `build_tree`,
  `_add_dir_children` — all of `EntryTree`'s category/file-selection
  semantics stay in `entry.py`, unchanged. `EntryScreen EntryTree`'s
  `max-width: 60%` also stays entry-specific — it exists only because the
  tree shares the screen with the form panel, which is not a fact about
  trees in general.
- Out of scope: Inspect Tree itself (M4), any new tree behavior, any change
  to `EntryScreen`'s layout or CSS beyond moving the shared declarations.

## Decisions

Settled with the dev during this milestone's spec interview (2026-09-09).

| Decision | Rationale |
| --- | --- |
| The base widget lives in `tui/screens/base.py` | Matches the roadmap's own suggestion and the existing convention: `NavigableScreen`, `MenuScreen`, `VimOptionList`, `PanelAwareInput` are all already there — one file for shared screen/widget conventions. |
| This milestone is a **pure extraction**: the base widget is generic over the tree's data type and carries no knowledge of categories or files. It exposes no hook or abstract method for M4 to implement | Dev's choice, against the alternative of designing an explicit extension point now. M4 is free to build its own `NodeData`/tree-population logic on top of the base when it lands; nothing here anticipates it beyond leaving room via genericity. |
| The base widget's class name is **`SupaTree`** | Dev's naming choice. |

## Context

- `EntryTree` (`src/idiomas/tui/screens/entry.py:98-116`) is the widget being
  refactored. It currently subclasses `Tree[NodeData]` directly and carries
  both the shared bindings (to be extracted) and entry-specific tree-building
  logic (to stay).
- The shared CSS today lives in `app.tcss` under `EntryScreen EntryTree { ... }`
  — `width: auto`, `max-width: 60%`, `border: round $accent`,
  `overflow-x: hidden`. Of these, `width: auto`, `border`, and `overflow-x`
  are the generic "content-sized, bordered, no h-scroll" aesthetic the
  roadmap calls out as shared; `max-width: 60%` is a fact about sharing
  screen space with the form panel and stays with `EntryScreen`.
- `tests/test_tui_entry_screen.py` is the existing test coverage for
  `EntryScreen`/`EntryTree` and is expected to keep passing unchanged.
