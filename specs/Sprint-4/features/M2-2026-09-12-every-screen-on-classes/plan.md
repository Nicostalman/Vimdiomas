# M2 · Every screen on the new classes — plan

Task groups in dependency order. Each group ends with the test suite green.

## 1. `panels.py`: the flat-menu case

`Backpanel` currently assumes it always has `Panel` children. Menus give it
zero, so its `escape`/`enter`/`tab` bindings need a second branch.

1. **`Backpanel.panels()` returning `[]`** already makes `edge_panel()` and
   `neighbour()` return `None` — no change needed there; shift+hjkl on a menu
   are already no-ops through the existing "no panel in that direction" path.
2. **`Backpanel.action_escape`**: today's body is "swallow, do nothing." Add
   the guard M1 gave `Panel`: if focus is on `self`, do nothing (unchanged);
   if focus is inside `self` (content, with no intervening `Panel`), focus
   `self`. With at least one child `Panel`, that inner content's `esc` is
   already caught by the `Panel` first, so this branch is only ever reached
   from a panel-less screen — no behavior change for Entry/Browse/Inspect
   Tree.
3. **`Backpanel.action_enter`/`action_tab`**: today, "focus `first_panel()`'s
   content." When `panels()` is empty, focus the backpanel's own first
   focusable/enabled/displayed descendant instead (the same descendant-search
   `Panel.focus_content()` already implements — factor it onto a shared
   function or `Backpanel` reuses `Panel`'s implementation directly).
4. **CSS: distinguish "backpanel accent while its own content has focus"
   (flat menus) from "backpanel accent only when literally focused" (every
   other screen).** Add a `.backpanel-flat` class, set by `MenuScreen` (or
   whatever the new menu base is called) on its `Backpanel`:
   `.backpanel-flat:focus-within { border: round $accent; }` alongside the
   existing `.backpanel:focus`. Plain `.backpanel` screens keep today's rule
   unchanged since `:focus-within` is never true there without also matching
   a `.panel` first (which already has its own accent rule).
5. **Unit tests**, added to `tests/test_tui_panels.py`, on a new small host
   screen with a `Backpanel` and **no** `Panel` children (just a focusable
   `Static`-like stub or an `OptionList`): opening focuses the content
   directly; `esc` from content focuses the backpanel; `esc` again does
   nothing; `enter`/`tab` from the backpanel refocus the content; shift+hjkl
   are no-ops at both levels.

## 2. Menus flat

New shared base for the three menu screens — name it `MenuScreen` still
(replacing the old `NavigableScreen`-based one in `base.py`; it's deleted in
group 6).

1. Add `MenuScreen(PanelScreen)` to `panels.py`: `compose()` is left to
   subclasses, but a class-level convention wraps whatever `OptionList` they
   yield in a bare `Backpanel` with `.backpanel-flat` — simplest as a
   `compose()` template method: subclasses implement `menu_options()`
   returning the list of `Option`s (matching today's `compose` bodies
   closely), `MenuScreen.compose()` yields
   `Backpanel(VimOptionList(*self.menu_options()), classes="backpanel-flat")`.
2. `LandingMenuScreen`, `SettingsScreen` (`landing.py`) and `MainMenuScreen`
   (`main_menu.py`) subclass the new `MenuScreen`, implementing
   `menu_options()` instead of `compose()`. Their `on_option_list_option_selected`
   handlers, `action_back_or_quit` override (landing menu exits the app), and
   all push-screen logic are unchanged.
3. CSS: `.menu-screen` (old class, tied to the old `MenuScreen`) is retired;
   `.backpanel-flat` (group 1.4) plus `.backpanel-flat VimOptionList { border:
   none; width: 40; height: auto; }` replace `.menu-screen` and `.menu-screen
   OptionList`'s width/height/border rules, mirroring `.panel VimTree`'s
   border removal. Centering (today's `align: center middle`) moves to
   `.backpanel-flat`.
4. Tests: rewritten in `tests/test_tui_landing_menu.py` and
   `tests/test_tui_main_menu.py` — only navigation/focus assertions change
   (see § 4); item-list, selection, and push-screen tests are unchanged.

## 3. Browse and Inspect Tree

### Browse (`browse.py`)

1. `BrowseScreen(PanelScreen)`. `compose()`: `Backpanel()` → one
   `Panel(id="browse-panel")` holding, in order: filename-filter `TextField`,
   tag-filter `TextField`, results `VimOptionList`, empty-state `Static`.
   `PanelAwareInput` → `TextField`.
2. Delete `PANEL_IDS`, `_switch_panel`, `action_panel_prev`,
   `action_panel_next`, `AUTO_FOCUS = "#results"`. `PanelScreen`'s own
   landing/`esc` rules cover all of it.
3. CSS: `#results`'s own `border: round $accent` is dropped in favour of
   `.panel VimOptionList { border: none; }` (group 5); `height: 1fr` and the
   empty-state padding stay, now scoped to `#browse-panel` where they were
   `BrowseScreen`-scoped.
4. Footer hint: add one (Entry and Inspect Tree both have one; Browse
   currently doesn't) — `Esc go out · Enter select` is enough, since there's
   only one panel and nothing to switch to.

### Inspect Tree (`inspect.py`)

1. `InspectTreeScreen(PanelScreen)`. `compose()`: `Backpanel()` → one
   `Panel(id="inspect-panel")` holding the mode badge, the tree, and the
   footer hint, in that order (badge and footer sit above/below the tree
   today; kept).
2. `InspectTree(VimTree[NodeData])` instead of `SupaTree[NodeData]`, with the
   same shift-arrow-to-no-op override `EntryTree` got in M1 (group 2.4 of
   M1's plan) — copy the four `Binding`s and `action_nothing`, or factor them
   onto a small mixin both trees use (dev's "one place to change every X"
   applies here too; a `NoShiftArrowsMixin` or similar, used by both
   `EntryTree` and `InspectTree`).
3. `SupaTree` is now unused anywhere — deleted from `base.py` in group 6.
4. CSS: `InspectTreeScreen InspectTree`'s `height: 1fr` moves to scope under
   `#inspect-panel`; the tree's own border rules (`mode-pdf`/`mode-md`
   red/blue) are unaffected — they're about mode, not focus, and stay as
   `InspectTree.mode-pdf`/`.mode-md`, layered under `.panel VimTree {
   border: none }`'s removal the same way Entry's tree already works.

## 4. Tests: navigation/focus only

Every non-navigation test (item lists, filtering, file operations, dialogs,
compile, autocompile, mode toggling) must pass **unchanged**. Only these
change or are added:

**Browse** (`tests/test_tui_browse_screen.py`):

| Today | Becomes |
|---|---|
| `test_capital_l_from_results_wraps_to_filename_filter` | `test_capital_l_from_results_panel_does_nothing` (one panel, no wraparound) |
| `test_shift_left_from_input_cycles_panels` | `test_shift_left_from_input_does_not_switch_panel` |
| `test_q_from_results_pops_the_screen` | Kept |

New: `test_opening_focuses_filename_filter`, `test_escape_from_filename_filter_focuses_panel`,
`test_escape_from_tag_filter_focuses_panel`, `test_escape_climbs_panel_then_backpanel_then_stays`,
`test_q_from_a_filter_field_types_q`.

**Inspect Tree** (`tests/test_tui_inspect_tree.py`):

New: `test_opening_focuses_the_tree`, `test_escape_climbs_tree_panel_then_backpanel_then_stays`,
`test_shift_arrows_on_tree_do_not_move_the_cursor` (same intent as Entry's M1
test), `test_tab_toggles_mode_from_tree_content` (renamed from
`test_tab_toggles_mode` if the old name no longer fits), `test_tab_from_panel_focuses_the_tree`.

**Menus** (`tests/test_tui_landing_menu.py`, `tests/test_tui_main_menu.py`):

New per screen: `test_opening_focuses_the_list`, `test_escape_focuses_the_backpanel`,
`test_escape_from_backpanel_does_nothing`, `test_enter_on_backpanel_refocuses_the_list`,
`test_shift_hjkl_do_nothing`. `test_jk_move_*_highlight` (existing) unchanged —
`j`/`k` are `VimOptionList`'s own cursor movement, untouched by any of this.

**`test_tui_panels.py`**: the new flat-`Backpanel` cases from plan § 1.5.

No test count drop below 309 apart from the one-for-one replacements named
above.

## 5. Modularity pass

1. **Shared directory walk.** A function in a shared home (`store.py`, since
   it already owns `DirNode`/`walk`, or a new small module if `plan.md`
   iteration finds that awkward) that walks a `DirNode` recursively, adding a
   directory node per `DirNode.dirs` entry, and calling a passed-in
   `on_file(tree_node, file_node)` callback per `DirNode.files` entry.
   `entry.py`'s `_add_dir_children` becomes that callback adding
   category/uncategorized/new-category leaves; `inspect.py`'s becomes the
   callback adding the file leaf directly. `build_tree` in each module stays
   (sets root data, calls the shared walk with its own callback, expands the
   root).
2. **Shared `_compile_one`.** Move to `compile.py` (already owns
   `compile_file`) or `store.py`; both `entry.py` and `inspect.py` import it.
   Keep the notify message generic ("Compile failed for {name}: {exc}") — the
   "Autocompile failed" wording in `entry.py`'s version was the only
   difference and isn't load-bearing.
3. **CSS.** `#entry-form Input { margin-bottom: 1 }` and `BrowseScreen Input
   { margin-bottom: 1 }` become one `TextField { margin-bottom: 1; }` rule
   (both screens' fields are `TextField` now); `#entry-form Input`'s `width:
   40` stays screen-scoped since Browse's fields want full panel width, not
   40. `.panel VimOptionList { border: none; }` added alongside `.panel
   VimTree` (group 3, Browse). Per-screen sizing that's genuinely specific
   (`#entry-form`'s 60% width and padding) is left alone.

## 6. Retire the old classes and docs

1. Delete `NavigableScreen`, `PanelAwareInput`, `SupaTree`, and the old
   `MenuScreen` from `base.py` (verified unreferenced once groups 2-3 land).
   `VimTree`, `VimOptionList`, `FooterHint`, `ConfirmDialog`, `PromptDialog`
   stay.
2. `specs/current/design.md`: delete the *Transition* section and its key
   table entirely (not merged — nothing runs on the old model anymore). Add
   the flat-menu vocabulary/behavior (this file's § *The menu model*) to the
   model section, and the `.backpanel-flat` mechanism to *Implementation*.
3. `specs/current/stack.md`: drop the note about the "older trio" still
   being in use; the *Screen composition* section from M1 is now the whole
   story.
4. This folder's three files, kept in step with anything that changes during
   implementation.

## 7. Verification

1. `pytest` — full suite.
2. Launch the app and walk `validation.md`'s manual checks for all four
   screen kinds.
3. Hand off to the dev for the by-eye check. No PR before their go-ahead.
