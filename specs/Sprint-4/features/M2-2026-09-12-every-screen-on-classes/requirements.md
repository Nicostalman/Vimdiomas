# M2 · Every screen on the new classes — requirements

Sprint 4 · M2. Source: [`backlog.md`](../../guidelines/backlog.md) § *Classes
rework*, § *Browse fixes*; roadmap:
[`roadmap-sprint-4.md`](../../roadmap-sprint-4.md) § M2.

## Anchor: the roadmap's text

**Deliverable.** Browse, Inspect Tree, every menu and every placeholder are
rebuilt on M1's classes and follow M1's focus/`esc`/shift+hjkl rules. Browse's
`esc`/auto-focus fixes land as a consequence. A modularity pass addresses the
duplicate tree builders, screen-specific CSS, and duplicated autocompile-worker
code — `plan.md` settles which land here. No screen still defines its own
ad-hoc panel or focus handling outside the shared classes.

**Done when.** Every screen and menu opens focused on its first panel's
content; `esc` climbs the same way everywhere; shift+hjkl move spatially
everywhere; Browse opens on the filename filter and `esc` leaves it; the dev
confirms each screen by hand-testing; and the full test suite passes.

## Decisions from this spec conversation

Settled with the dev on 2026-09-12, resolving M1's and this roadmap entry's
open questions.

| Decision | Rationale |
| --- | --- |
| **Menus are flat: backpanel → content directly, no intermediate `Panel`.** | Dev's choice between the two options M1 left open. A menu's list already *is* the screen's one visual region — wrapping it in a `Panel` inside the `Backpanel` would draw two borders for one thing. |
| **Browse is one `Panel` holding all three widgets** (filename filter, tag filter, results), stacked as today — not three separate panels. | Dev's choice. Matches today's visual layout exactly; shift+hjkl have nothing to move between, same as Inspect Tree's single panel. |
| **Placeholders get backpanel → panel → static**, not left bare. | Dev's choice, for the same reason every other screen is unified: "no screen still defines its own ad-hoc panel or focus handling outside the shared classes." The `Static` isn't focusable, so the panel itself holds focus on open (M1's existing "no focusable content → focus the panel" rule). |
| **The modularity pass takes all three candidates** the roadmap names (duplicate tree builders, screen-specific CSS, duplicated autocompile-worker code). | Dev's instruction: "do what you think is good. As a general rule, related things in the app should be easily modifiable in one place." `plan.md` § 5 spells out each one. |
| **The backpanel is only reachable via `esc` with more than one panel.** With zero panels (a menu) or exactly one (Browse, Inspect Tree), `esc` stops one level short of the backpanel instead. | Dev feedback, hands-on, generalizing what was first built as a menu-only rule: with one panel there's exactly as little reason to climb to the backpanel as with none — no second panel to jump to, nothing else to see. Only Entry (two panels) still reaches it. `Backpanel.reachable()` (`len(panels()) > 1`) is the single check both `Panel.action_defocus` and `Backpanel.action_defocus` use. |

## Scope

### In

1. **Browse** rebuilt on `PanelScreen`/`Backpanel`/`Panel`/`TextField`. One
   panel; opens focused on the filename filter; `esc` from either filter goes
   to the panel, then the backpanel. `AUTO_FOCUS = "#results"` is deleted —
   it existed only to dodge a focused-field trapping `q`, which M1's `esc`
   already fixes generally.
2. **Inspect Tree** rebuilt on `PanelScreen`. One panel holding the tree, the
   mode badge, and the footer hint (mirrors Entry's form panel holding its
   footer hint). Its tree stops subclassing `SupaTree` (which is deleted) and
   subclasses `VimTree` directly, like `EntryTree`, with the same
   shift-arrows-to-no-op override — the tree now lives inside a `Panel`,
   which claims shift+arrows for panel movement.
3. **Every menu** (Landing, Settings, Main menu) rebuilt flat, per the
   decision above.
4. **Placeholder** rebuilt: backpanel → panel → the message `Static`.
5. **Old classes retired**: `NavigableScreen`, `PanelAwareInput`, `SupaTree`,
   and the old `MenuScreen` are deleted from `base.py` once nothing
   references them (verified: only the four screen modules above do).
   `VimTree`, `VimOptionList`, `FooterHint`, `ConfirmDialog`, `PromptDialog`
   stay, unchanged.
6. **The modularity pass** — see `plan.md` § 5 for the concrete scope of
   each candidate.
7. **Docs:** `design.md`'s *Transition* section and its old key table are
   deleted (not merged) now that nothing runs on the old model; the menu
   vocabulary/flat-model behavior is added to the model section. `stack.md`
   drops its "older trio" transition note.

### Out (deferred)

- The installation wizard's screens (M5, M6) — built on these classes later,
  not part of M2.
- The standalone new-category form — M3. Entry itself is not touched again
  here beyond what M1 already did.
- Any change to Browse's filtering/results logic, or Inspect Tree's file
  operations — only navigation/panel structure changes.

## The menu model (flat)

Applies to `LandingMenuScreen`, `SettingsScreen`, `MainMenuScreen`.

- **Structure.** `Backpanel` directly contains the `VimOptionList` — no
  `Panel` in between. The list *is* the backpanel's content, the same role a
  panel's content plays elsewhere, one level shallower.
- **On opening.** The list is focused directly — the general "land in the
  first content" rule, applied where there are zero child panels.
- **`esc` does nothing.** A menu has zero panels, and the general
  *backpanel reachability* rule (below) says the backpanel is never reached
  via `esc` with zero or one panel — so `esc` on the list leaves it focused.
  Browse's results list, by contrast, still climbs from content to its one
  `Panel` (content → panel is unaffected by this rule); it just never climbs
  *past* that panel to the backpanel, for the same reason a menu doesn't.
  The backpanel can still be focused directly (e.g. in a test), and `esc` on
  the backpanel itself is a no-op there too, same as everywhere.
- **`enter`/`tab` on the backpanel.** Focus the list — the general
  backpanel → first-panel's-content rule, applied where there is no first
  panel to hand off to; the backpanel focuses its own content instead. In
  practice this is only reachable by focusing the backpanel directly, since
  `esc` no longer routes there.
- **shift+hjkl.** No-ops everywhere on a menu — there are no panels to move
  between. This must fall out of the existing `panels()`/`edge_panel()`/
  `neighbour()` logic returning nothing when a screen has zero panels, not a
  menu-specific special case.
- **Look.** The backpanel's border is dim normally and **accent while the
  list has focus** (`:focus-within` matches even though the backpanel itself
  is never literally focused in normal use) — the backpanel is doubling as
  "the panel you're in" here, unlike a multi-panel screen where the
  backpanel is only accent when it is *itself* literally focused (content
  inside a real panel leaves the backpanel dim). The `.backpanel-flat` CSS
  class carries this. The list itself has **no border of its own** — dev's
  call, unlike Browse's results list, which keeps one deliberately (see
  Browse, below) — and gray padding on all sides inside the list so its gray
  background doesn't touch the highlighted row's edge *(dev feedback,
  hands-on: the blue highlight clashed with the black screen background
  without vertical padding; left/right padding was added afterward for the
  same reason)*.

## Browse

- One `Panel` (plan.md names its id) holds, stacked top to bottom: the
  filename-filter `TextField`, the tag-filter `TextField`, the results
  `VimOptionList`, the empty-state `Static` — same order and look as today.
- Opens focused on the filename filter (today's `AUTO_FOCUS = "#results"`
  is deleted).
- `esc` from either filter field, or from the results list, goes to the
  panel. `esc` again, from the panel, does **nothing** — one panel, so the
  backpanel is never reached (see *backpanel reachability*, above).
- The old `PANEL_IDS`/`_switch_panel`/`action_panel_prev`/`action_panel_next`
  are deleted. With one panel, shift+hjkl are no-ops here, the same as
  Inspect Tree — there is nothing to switch to.
- **`tab` cycles filename filter → tag filter → results → filename filter**,
  wrapping — a screen-specific `action_next_field`, the same shape as
  Entry's. *(Dev feedback, hands-on: the first drop left `tab` unbound on
  `BrowseScreen`, so it fell through to Textual's own `tab -> app.focus_next`
  default, which also stops on the focusable panel and backpanel themselves —
  two extra, unwanted stops before reaching the next field.)*
- **The results list auto-highlights its first row**, on open and after
  every filter change. *(Dev feedback, hands-on: unlike a menu's
  `VimOptionList`, whose options are passed to the constructor and so are
  auto-highlighted by `OptionList.__init__`, Browse's results are added
  after the fact on every filter change — `action_first()` is now called
  explicitly once candidates are populated.)*
- **The results list keeps its own border**, even though it's a panel's
  content, not a panel. *(Dev's explicit aesthetic call, overriding the
  general "content has no border of its own" convention for this one
  widget — the `.panel VimOptionList { border: none }` rule this milestone
  first added is removed again.)*

## Inspect Tree

- One `Panel` holds the tree, the mode badge `Static`, and the footer hint,
  the same shape as Entry's form panel holding its own footer hint.
- The tree becomes a direct `VimTree` subclass (no more `SupaTree`), with
  `Tree`'s own shift-arrow defaults overridden to a no-op, the same fix M1
  gave `EntryTree`.
- `tab` keeps its screen-specific meaning (toggle PDF/MD mode) when the tree
  (content) has focus: `Panel`'s own `tab` binding only fires when the panel
  *itself* is focused (its guard raises `SkipAction` otherwise, per M1), so
  `InspectTreeScreen`'s `action_toggle_mode` binding still sees the key once
  focus is on the tree — the same bubbling relationship Entry's
  `action_next_field` already relies on. When the panel itself has focus (not
  the tree), `tab` instead focuses the tree, same as `enter` — mode-toggling
  is only ever reached from inside the tree.
- `esc` from the tree goes to the panel; `esc` again does **nothing** — one
  panel, same as Browse, so the backpanel is never reached.

## Placeholder

- `Backpanel` → one `Panel` → the message `Static`. A `Static` isn't
  focusable, so opening lands on the panel itself (M1's existing "no
  focusable content → focus the panel" rule) — no new logic needed.
- `esc` on the panel does nothing — one panel, so the backpanel is never
  reached, same as Browse and Inspect Tree; `q` leaves from any level.

## Modularity pass

See `plan.md` § 5 for the concrete task breakdown. Scope, per the dev's "do
what you think is good... related things easily modifiable in one place":

- Unify the directory-walk shared by `entry.py`'s and `inspect.py`'s
  `build_tree`/`_add_dir_children` — the recursive walk over `DirNode` is
  identical; only what happens at a file leaf differs (Entry adds
  category/uncategorized/new-category leaves under it, Inspect Tree adds the
  file itself as a leaf).
- Unify `_compile_one`, duplicated verbatim in `entry.py` and `inspect.py`
  apart from one word in the notify message.
- Fold CSS that's really general — `#entry-form Input` and `BrowseScreen
  Input` both set `margin-bottom: 1`, for instance — into one rule the new
  classes own, while leaving genuinely per-screen sizing (`#entry-form`'s 60%
  width) alone.

## Constraints and context

- **Nothing outside the four target screens references the retired classes**
  (`NavigableScreen`, `PanelAwareInput`, `SupaTree`, old `MenuScreen`) —
  verified by grep against `src/` and `tests/`.
- **Backpanel with zero or exactly one child panel** are cases M1's tests
  never exercised (Entry always has two). Covered directly on generic host
  screens in `test_tui_panels.py`, as well as through the menu screens,
  Browse, and Inspect Tree themselves.
- **Textual `OptionList` has no default `escape` binding**, so `esc` from the
  results list in Browse (or from a menu's list) bubbles up to the panel/
  backpanel the same way it does from `EntryTree`, without a widget-specific
  override — verified against the installed Textual version, same basis as
  M1's bubbling note.
- **Test count.** 309 tests on `main` at the start of this branch. No count
  drop except tests consciously replaced one-for-one, named in `plan.md` § 4.
