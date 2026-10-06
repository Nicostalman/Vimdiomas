# M1 · Navigation conventions — requirements

## Roadmap anchor

**Deliverable** (from [`../../roadmap-sprint-2.md`](../../roadmap-sprint-2.md)):

- `h` `j` `k` `l` work wherever the arrow keys already do — in `OptionList`
  (main menu, browse results) and `Tree` (entry screen).
- `enter` chooses.
- `q` returns to the previous menu; on the main menu it exits the app. It must
  **not** fire while an `Input` has focus, or the letter cannot be typed.
- `shift`+`h`/`l` — and `shift`+`←`/`→` — moves between panels: tree ↔ form on
  the entry screen, and between browse's three stacked fields.
- Every `escape` binding is removed: `PlaceholderScreen.BINDINGS` and
  `EntryScreen`'s `focus_tree`.
- Leaving a screen with `q` must not lose work — saving and compiling happen
  on the way out. Edge cases are the implementer's call, but silent loss is
  not one of them.
- The conventions are recorded as a section of [`../../stack.md`](../../stack.md).

**Done when.** Every screen can be driven end to end with `hjkl`, `enter` and
`q` alone; `q` on the main menu exits; `q` inside a text field types a `q`; no
`escape` binding remains in the codebase; and `stack.md` carries the key map.

Traces to proposals `#7`, `#8`, `#19`, `#20`, `#21` in
[`agent-notes.md`](../../guidelines/agent-notes.md), sourced from
`motivation.md`'s *vim commands*, *enter vocabulary menu*, and *other menus*
sections.

## In scope

- A shared base `Screen` class (`NavigableScreen`) holding the `q` binding
  (with the Input-focus guard) and the shift+h/l panel-switch mechanism.
  `MainMenuScreen`, `PlaceholderScreen`, `EntryScreen`, and `BrowseScreen` all
  subclass it.
- `q` behavior: pop the screen, unless the screen stack has only one screen
  left (the main menu), in which case it exits the app. This falls out of
  checking `len(self.app.screen_stack)` rather than special-casing
  `MainMenuScreen` — the main menu is simply the only screen that is ever
  alone at the bottom of the stack.
- hjkl support added at the widget level: `OptionList` and `Tree` instances
  gain `h`/`j`/`k`/`l` bindings that alias whatever the arrow keys already do
  on that widget. This means a small `VimOptionList` wrapper (used by
  `MainMenuScreen` and `BrowseScreen`'s results list) and an update to the
  existing `EntryTree` subclass.
- Removal of `EntryTree`'s `Binding("right", "select_cursor", ...)` override.
  It predates `shift+l`/`L` as the panel-switch key and made plain `l`/right
  behave like `enter`. **Implementation finding:** `Tree` has no default
  binding for plain left/right at all (only `shift+left`/`shift+right`, for
  parent/ancestor jumps) — the Sprint 1 override existed precisely because
  plain right otherwise did nothing. With panel-switching now owning
  `shift+left`/`shift+right`/`H`/`L` and `enter` owning selection, plain
  `h`/`l` are left unbound on the tree (matching "whatever the arrow key
  already does" — which is nothing).
- Panel switching via two mechanisms, since they end up covering different
  cases (**implementation finding**, not anticipated at spec time — see
  below): the capital letters `H`/`L`, and `shift+←`/`shift+→`.
  - Entry screen: toggles between the tree and the form (2 panels — this is
    already effectively a toggle, wraparound and toggle are the same thing).
  - Browse screen: cycles linearly with wraparound across the three stacked
    controls (filename filter → tag filter → results → back to filename
    filter), in that fixed order.
- All `escape` bindings removed: `PlaceholderScreen.BINDINGS` and
  `EntryScreen`'s `focus_tree` binding (superseded by shift+h to go back to
  the tree).
- Footer/hint text on `EntryScreen` (`FOOTER_HINT`) updated to describe the
  new key map instead of the old `Esc`-based one. (Fuller footer-hint rewrite
  reflecting M2's field changes as well is `#13`, tracked for M2 — this is
  the M1-scoped subset: replacing `Esc back to tree` with the new keys.)
- New key map documented as a section of `stack.md`.

## Explicitly deferred

- **Compile-on-exit from the entry screen.** Entries are already persisted to
  disk immediately on "Create" (`writer.save`), so `q` never loses *entered*
  data — only a possibly-stale PDF. Full compile-on-navigation logic
  (per-file "dirty since last compile" tracking, hooked off
  `_on_node_highlighted`, plus compile-on-screen-exit) is `#18` / M3's job in
  full. M1 does not add any compiling behavior on `q`. This is a deliberate
  reading of the roadmap's "no silent loss" bar: no *entries* are lost,
  because they're saved on creation, not on exit.
- Everything in M2 (entry-screen field/tree corrections), M3 (autocompile),
  M4 (macOS input switching) — untouched here.
- `gloss`→`translation` rename and other M2-scoped `FOOTER_HINT` wording are
  out of scope; M1 only removes the stale `Esc` reference.

## Context / prior decisions

- `EntryTree`'s current `Binding("right", "select_cursor", ...)` was a
  Sprint 1 decision, made before `shift+l`/`L` existed as the panel-switch
  key. M1 removes it (see *In scope* above) — recorded as a reversal, not a
  bug.
- Textual has no built-in "does the focused widget accept text input" guard
  for `BINDINGS`. `NavigableScreen`'s `q` action checks
  `isinstance(self.focused, Input)` and no-ops if true, letting the
  keystroke fall through to the `Input` as a normal character.

## Implementation findings (not known at spec time)

Discovered while building against Textual's actual key-handling behavior;
recorded here and in [`agent-notes.md`](../../guidelines/agent-notes.md)
rather than silently reconciled, since they change what the roadmap's
`shift+h`/`shift+l` phrasing actually maps to in code.

- **`shift+h`/`shift+l` are not real Textual key names.** Shift + a letter
  key arrives as the literal capital letter (`event.key == "H"`), because a
  letter already encodes case — there's no separate "shift" modifier to
  report. The screen-level bindings use `H`/`L` instead.
- **A focused `Input` intercepts every printable character for itself**,
  including `H`/`L`, before any screen-level binding is reached. This means
  the letter-based switch can only ever move focus *into* a panel that
  contains an `Input` — never back out of one via a letter, since the
  letter always types instead. `shift+left`/`shift+right` are the only keys
  that can plausibly leave a focused `Input`, but `Input` binds those itself
  by default (to extend a text selection) — so a new `PanelAwareInput`
  wrapper overrides just those two keys to dispatch to the screen instead,
  trading away shift-arrow text-selection inside fields for a working
  "leave this field" key. This is used for every `Input` in the app.
- **Browse's default focus violated the "q alone" bar.** Textual's default
  `AUTO_FOCUS` lands on the first focusable widget in compose order — the
  filename filter, an `Input`. A screen that opens with an `Input` already
  focused is unreachable via `q` until focus moves off it first, which the
  roadmap's "driven end to end with hjkl, enter and q alone" phrasing rules
  out. Fixed by setting `BrowseScreen.AUTO_FOCUS = "#results"`.
- **`len(self.app.screen_stack)` cannot detect "this is the root screen."**
  Textual's `App` always keeps an implicit base `Screen` underneath
  everything the app itself pushes, so the stack is never at length 1 for a
  screen the app put there — `MainMenuScreen` is at stack depth 2, not 1.
  `MainMenuScreen` instead overrides `action_back_or_quit` directly to call
  `self.app.exit()`.
