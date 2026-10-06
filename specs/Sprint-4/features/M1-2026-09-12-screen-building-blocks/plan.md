# M1 · Screen building blocks — plan

Task groups in dependency order. Each group ends with the test suite green.

## 1. The new module and its classes

New module `src/idiomas/tui/screens/panels.py`. `base.py` stays as it is; M2
retires what it replaces.

1. **`TextField(Input)`** — the app's text field for screens on the new model.
   No `escape` binding of its own: it bubbles to the panel. shift+left/
   shift+right are bound to a no-op, overriding `Input`'s own default (extend
   the text selection) — dev feedback, hands-on: shift-arrows must mimic
   H/L/J/K exactly, including doing nothing on content (see group 2.4's
   equivalent fix on `EntryTree`, and `requirements.md` § *Shift-arrows mimic
   the letter keys*). A class of its own anyway, so every field's look and
   any future shared behaviour live in one place (the backlog asks for
   exactly this).
2. **`Panel(Vertical)`** — `can_focus = True`, CSS class `panel`.
   - `focus_content()`: focus the first descendant in the screen's focus chain
     that is focusable, enabled and displayed; otherwise focus `self`.
   - Bindings: `escape` → if focus is inside (not on self), focus self; if on
     self, focus the backpanel. `enter`/`tab` → `focus_content()`, active only
     when self is focused (so `enter`/`tab` on content still reaches the
     content first — the content's own binding wins by bubbling order anyway,
     but the guard keeps a non-binding content widget from falling through to
     the panel). Guard-fail raises Textual's `SkipAction` rather than a plain
     `return`, so the key keeps bubbling — needed for `tab`, since a screen's
     own field-cycling binding (Entry's `action_next_field`) must still see
     it once focus is on a field, not the panel. (Dev feedback, hands-on:
     `tab` originally only worked on the form panel, via a special case in
     `EntryScreen`; generalizing it here onto `Panel` fixed the tree panel
     too and let that special case be deleted.)
     `H`/`shift+left`, `L`/`shift+right`, `J`/`shift+down`, `K`/`shift+up` →
     `move("left"|"right"|"down"|"up")`, **acting only when `self.has_focus`**
     (same `SkipAction` guard-fail).
   - `move(direction)`: ask the backpanel for the neighbour in that direction;
     if there is one, call its `focus_content()`.
3. **`Backpanel(Container)`** — `can_focus = True`, CSS class `backpanel`, the
   screen's single root child.
   - `panels()`: every `Panel` descendant in DOM order.
   - `edge_panel(direction)`: the extreme panel in that direction by region
     (leftmost/rightmost/topmost/bottommost), ties broken by the other axis
     (leftmost for a vertical direction, topmost for a horizontal one, same
     as `first_panel`'s own tie-break). `first_panel()` is now
     `edge_panel("left")`.
   - `neighbour(panel, direction)`: among panels whose region lies strictly on
     that side of `panel`'s region, the nearest by edge distance, ties broken
     by distance between the two regions' centres on the other axis. `None` if
     there are none (no wraparound).
   - Bindings: `escape` → nothing (swallowed, so it never reaches the screen).
     `enter` → `first_panel().focus_content()`, active only when self is
     focused. `H`/`shift+left`, `L`/`shift+right`, `K`/`shift+up`,
     `J`/`shift+down` → `focus_edge("left"|"right"|"up"|"down")`, same guard.
     Dev feedback, hands-on, added alongside the border below: reaching only
     the *first* panel from the backpanel, never the last or a vertical one,
     felt like a gap once the backpanel was a real place to be.
4. **`PanelScreen(Screen)`** — the screen base for the new model.
   - Carries `q` with the same text-field guard as `NavigableScreen`
     (`isinstance(self.focused, Input)` → type, don't leave).
   - `on_mount` (after subclasses compose): land in the first panel's content
     via `call_after_refresh`, since regions aren't known until the first
     layout pass. `AUTO_FOCUS = ""` so Textual doesn't focus something else
     first — verified against Textual 8.2.8 that `AUTO_FOCUS = None` would
     *not* do this: a screen's `None` falls back to `App.AUTO_FOCUS` (`"*"`
     by default) rather than disabling auto-focus; only a falsy non-`None`
     value does.
   - `tab`/`shift+tab` are not bound here; screens that want field cycling
     bind their own (Entry already does).
5. **CSS in `app.tcss`**, one block for the model rather than per screen:
   `.panel { border: round $panel; }`,
   `.panel:focus, .panel:focus-within { border: round $accent; }`,
   `.panel VimTree { border: none; }` (see group 2.4 for `VimTree`),
   `.backpanel { border: round $panel; }`,
   `.backpanel:focus { border: round $accent; }` — a permanent border (never
   absent) so focusing the backpanel doesn't shift the layout by the border's
   width the way an appearing-only border would; dev feedback, hands-on, adds
   this once H/L/J/K make the backpanel worth seeing.
6. **Unit tests** in a new `tests/test_tui_panels.py`, on a small host screen
   with three panels laid out as a row plus one below. They cover: open lands
   in first panel's content; escape content→panel→backpanel→stays; enter
   backpanel→first content, panel→content; `tab` on a panel focuses its
   content, same as `enter`; H/L/J/K from the backpanel focus the
   leftmost/rightmost/topmost/bottommost panel's content; spatial neighbours
   in all four directions, including edges doing nothing; shift+hjkl inert
   while content has focus, capital H into a field types an H; landing on an
   all-disabled panel focuses the panel; `q` leaves from a panel and types in
   a field.

## 2. Entry on the new classes

1. `EntryScreen` subclasses `PanelScreen` instead of `NavigableScreen`.
2. `compose`: `Backpanel` → `Horizontal` → `Panel(id="tree-panel")` holding
   `EntryTree`, and `Panel(id="entry-form")` holding the same widgets as today.
   `FormPanel` is deleted from `entry.py` (nothing else imports it except
   tests, which change in group 3).
3. The form's `PanelAwareInput`s become `TextField`s; `HanziInput` subclasses
   `TextField`, focus/blur logic unchanged.
4. `EntryTree` stops getting shift+left/right panel dispatch: it subclasses a
   new binding-free split of `SupaTree`. Concretely: move `SupaTree`'s j/k
   into a `VimTree(Tree)` base that both use; `SupaTree(VimTree)` keeps its
   shift-arrow dispatch for Inspect Tree until M2; `EntryTree(VimTree)`. The
   `SupaTree` CSS rule is renamed to target `VimTree` so both trees keep the
   shared look, and `.panel VimTree { border: none; }` drops the border inside
   a panel. `design.md`'s tree bullet is updated to match.
   `EntryTree` additionally overrides `Tree`'s own shift+left/shift+right/
   shift+up/shift+down bindings (parent/ancestor/sibling jumps) to a no-op —
   dev feedback, hands-on, same fix as `TextField`'s above. The override
   lives on `EntryTree`, not `VimTree`, so `SupaTree` (Browse, Inspect Tree)
   keeps `Tree`'s shift+up/down defaults unchanged until M2.
5. Delete from `EntryScreen`: `action_panel_prev`, `action_panel_next`,
   `_switch_panel`, `action_defocus_panel`. The general rules replace them.
6. Keep: `tab` → `action_next_field` for cycling between an already-focused
   field and the next one, wrapping. Its old special case for "tab on the
   form panel focuses the first field" is gone — `Panel`'s own `tab` binding
   (group 1.2) now covers that generally, for both panels, so
   `action_next_field` is only ever reached with a field or the create
   button already focused. Tree selection → `_focus_first_field`; everything
   about targets, create and autocompile unchanged.
7. CSS: `#entry-form`'s own `border`/`:focus` rules are removed in favour of
   `.panel`; its width and padding stay. `EntryScreen EntryTree { max-width:
   60% }` moves to `#tree-panel` together with `width: auto`.
8. Update the footer hint to the new keys: `Enter go in · Esc go out ·
   Shift+H/L switch panel · Tab next field · Enter on Create: save`.

## 3. Entry's tests

In `tests/test_tui_entry_screen.py`. Only focus/navigation tests change; every
tree, target, create, autocompile and input-method test must pass **unchanged**.

Rewritten to the new model (same names where the intent survives, renamed
where it doesn't):

| Today | Becomes |
|---|---|
| `test_capital_h_from_tree_focuses_form` | `test_capital_l_from_tree_panel_lands_in_form` — escape to the tree panel, `L` → hanzi. Plus `test_capital_h_from_tree_panel_does_nothing` (left edge). |
| `test_shift_left_from_form_input_returns_focus_to_tree` | `test_shift_left_from_form_input_does_not_switch_panel` — focus stays on hanzi. |
| `test_shift_right_from_tree_focuses_form` | `test_shift_right_from_tree_panel_lands_in_form` — from the panel, not the tree. Plus `test_shift_right_from_tree_content_does_nothing` and `test_shift_arrows_on_tree_content_do_not_move_the_cursor` (dev feedback, hands-on: all four shift-arrows now leave the cursor alone, not just shift+right). |
| `test_escape_defocuses_field_to_the_panel` | Kept, asserting the `Panel` with id `entry-form`. |
| `test_q_from_defocused_panel_pops_the_screen` | Kept. |
| `test_shift_left_from_defocused_panel_focuses_tree` | Kept (form panel → tree panel's content = the tree). |
| `test_tab_from_defocused_panel_focuses_first_field` | Kept. |

New:

- `test_opening_focuses_the_tree`
- `test_escape_climbs_tree_panel_then_backpanel_then_stays`
- `test_enter_on_backpanel_lands_in_tree`
- `test_enter_on_form_panel_lands_in_first_field`
- `test_tab_from_tree_panel_focuses_the_tree` (dev feedback, hands-on — see
  `requirements.md` § *Going in*)
- `test_shift_right_with_no_target_rests_on_form_panel`
- `test_capital_h_typed_into_field_is_text` (typing "H" in translation)
- `test_escape_from_hanzi_switches_input_method_back` (monkeypatched, like the
  existing input-method tests)

Imports change from `FormPanel` to `Panel`.

## 4. Docs

1. `specs/current/design.md` — rewrite *Navigation conventions*: the vocabulary
   table, the key table from `requirements.md`, landing/going-in rules, the
   focus look. Rewrite *Implementation* for `panels.py`, keeping the bullets for
   classes M1 doesn't touch (dialogs, `FooterHint`, `MenuScreen`,
   `VimOptionList`) and adding `VimTree`. A short **Transition** paragraph:
   Browse, Inspect Tree and the menus still run on `NavigableScreen`/
   `PanelAwareInput`/`SupaTree` with the old key table until Sprint 4 M2; the
   old table is kept there, marked as such, to be deleted in M2.
2. `specs/current/stack.md` — a short *Screen composition* section under TUI:
   backpanel → panels → content, focus handled by bubbling bindings and
   geometry, one module.
3. This folder's three files, kept in step with anything that changes during
   implementation.

## 5. Verification

1. `pytest` — full suite.
2. Launch the app and walk `validation.md`'s manual checks, including the
   input-method switch on `esc` from hanzi.
3. Hand off to the dev for the by-eye check. No PR before their go-ahead.
