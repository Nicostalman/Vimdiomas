# M1 · Navigation conventions — plan

**Revised during implementation** — three things assumed at spec time didn't
hold once checked against Textual's actual behavior; see the notes inline and
[`agent-notes.md`](../../guidelines/agent-notes.md) for the recorded decisions.

## 1. Shared base screen

- Added `src/idiomas/tui/screens/base.py` with `NavigableScreen(Screen)`:
  - `BINDINGS` includes `q` → `action_back_or_quit`, and panel-switching
    bound to `shift+left,H` → `action_panel_prev` and `shift+right,L` →
    `action_panel_next`.
    **Revision:** the spec's `shift+h`/`shift+l` don't exist as real key
    names — Textual reports Shift+H as the literal capital letter `"H"`,
    since a letter key already encodes case (confirmed via
    `textual.keys`/`events.Key`). Bound to `H`/`L` instead.
  - `action_back_or_quit`: no-op if `isinstance(self.focused, Input)`;
    otherwise `self.app.pop_screen()`.
    **Revision:** the plan's `len(self.app.screen_stack) > 1` check to
    detect "the main menu, so exit instead of pop" doesn't work — Textual's
    `App` always keeps an implicit base `Screen` under everything the app
    itself pushes, so the stack is at length 2 (not 1) even when
    `MainMenuScreen` is the only screen the app put there. `MainMenuScreen`
    instead overrides `action_back_or_quit` directly to call
    `self.app.exit()` (see group 3a).
  - `action_panel_prev` / `action_panel_next`: default no-op. Screens with
    multiple panels override these (see groups 3 and 4).
- Added `PanelAwareInput(Input)` to the same module (not in the original
  plan — discovered necessary during implementation): overrides
  `shift+left`/`shift+right` (which `Input` binds by default to
  extend-selection) to dispatch to `screen.panel_prev`/`screen.panel_next`.
  Without this, a focused `Input` swallows shift+arrow itself before it ever
  reaches the screen — the same is true of a plain `H`/`L` keystroke,
  intercepted as text before any binding runs, which is why letter-based
  switching can only ever move focus *into* a form, never out of one. Used
  for every text field in the app (`entry.py`'s five fields,
  `browse.py`'s two filters).
- Updated `MainMenuScreen` and `PlaceholderScreen` to subclass
  `NavigableScreen` instead of `Screen`.
- Removed `PlaceholderScreen.BINDINGS` (`escape` → `pop_screen`) and its
  `action_pop_screen` method entirely — superseded by the inherited `q`.

## 2. hjkl on OptionList and Tree

- Added `VimOptionList(OptionList)` in `base.py` with `BINDINGS` aliasing
  `j`→`cursor_down`, `k`→`cursor_up` (`OptionList`'s own action names for the
  arrow keys it already binds). `h`/`l` omitted — `OptionList` has no
  left/right concept to alias.
- Swapped `MainMenuScreen.compose`'s `OptionList` for `VimOptionList`.
- Swapped `BrowseScreen.compose`'s results `OptionList` for `VimOptionList`.
- Updated `EntryTree` (`entry.py`):
  - Removed `Binding("right", "select_cursor", "Select", show=False)`.
  - Added `j`→`cursor_down`, `k`→`cursor_up`.
    **Revision:** `h`/`l` are *not* aliased to `cursor_left`/`cursor_right`
    — those actions don't exist on `Tree` (confirmed: `Tree.BINDINGS` has no
    plain `left`/`right` entry to begin with, only `shift+left`/
    `shift+right` for parent/ancestor jumps — the Sprint 1 override existed
    specifically because plain right otherwise did nothing useful). Per "h/l
    do whatever the arrow key already does," and the arrow key does
    nothing, h/l are correctly left unbound.
  - Added `shift+left` → `screen.panel_prev`, `shift+right` →
    `screen.panel_next`, overriding `Tree`'s own defaults for those two keys
    (cursor-to-parent / cursor-to-next-ancestor) so the screen's
    panel-switch conventions take precedence, dispatched via Textual's
    `"namespace.action"` binding syntax.

## 3. Entry screen panel switching

- `EntryScreen` subclasses `NavigableScreen`.
- Removed the `escape` binding (`focus_tree`) from `EntryScreen.BINDINGS`.
- `action_panel_prev` / `action_panel_next` both call one `_switch_panel`
  helper (they do the same thing since there are only 2 panels — a toggle):
  if `self.focused` is the tree, focus the first visible form field
  (`_focus_first_field`); otherwise focus the tree.
- Swapped all five `Input` fields for `PanelAwareInput` (group 1).
- Updated `FOOTER_HINT` to drop `Esc back to tree`, describing `Shift+H`
  instead. (Full M2 footer rewrite is out of scope — only the stale `Esc`
  reference needed to go.)

### 3a. Main menu quit override

- `MainMenuScreen.action_back_or_quit` overrides the inherited pop behavior
  to call `self.app.exit()` directly — see the screen_stack revision in
  group 1. No Input-focus guard needed here (the main menu has none).

## 4. Browse screen panel cycling

- `BrowseScreen` subclasses `NavigableScreen`.
- Fixed panel order: `#filename-filter`, `#tag-filter`, `#results`.
- `action_panel_next` / `action_panel_prev` find the focused widget's index
  in that list and focus the next/previous one, wrapping around at both
  ends (`% 3`). No-op if focus isn't currently on one of the three.
- Swapped both filter `Input`s for `PanelAwareInput`, and the results
  `OptionList` for `VimOptionList` (groups 1 and 2).
- No changes needed to `_refresh_results` or the filtering logic.
- Added `AUTO_FOCUS = "#results"`. **Not in the original plan** — Textual's
  default `AUTO_FOCUS` (`"*"`) lands on the first focusable widget in
  compose order, which was the filename filter (an `Input`). That left a
  freshly-opened browse screen unreachable via `q` alone (typing "q" is
  indistinguishable from any other letter until focus moves off the
  `Input`), failing the roadmap's "driven end to end with hjkl, enter and q
  alone" bar right at the screen's default state. Verified the fallback
  works with zero results too (`#results` is still focusable when empty).

## 5. stack.md documentation

- Added a "Navigation conventions" section to `specs/stack.md` recording:
  - The key map table: `hjkl`, `enter`, `q` (with the main-menu exception
    and the Input-focus guard), and the two ways to switch panels (`H`/`L`
    only outside an `Input`; `shift+←`/`shift+→` including from inside one).
  - `NavigableScreen`, `VimOptionList`, `PanelAwareInput`, and why each
    exists (the Input-interception behavior that makes `PanelAwareInput`
    necessary is the least obvious part, so it's spelled out there).
  - That `escape` is not bound anywhere in the app.

## 6. Cleanup check

- `grep -rn "escape" src/idiomas/` → only an unrelated `_escape()` LaTeX
  helper in `compile.py` remains; no binding.
- `grep -rn "pop_screen" src/idiomas/tui/` → only the one call inside
  `NavigableScreen.action_back_or_quit` itself.
