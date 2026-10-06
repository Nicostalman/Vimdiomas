# M1 · Screen building blocks — requirements

Sprint 4 · M1. Source: [`backlog.md`](../../guidelines/backlog.md) § *Classes
rework*; roadmap: [`roadmap-sprint-4.md`](../../roadmap-sprint-4.md) § M1.

## Anchor: the roadmap's text

**Deliverable.** Backpanel, Panel and text field classes in a shared home, with
panels separate from the content inside them. Opening a screen focuses the
*content* of its leftmost or topmost panel. `esc` goes up one level of nesting
(content → panel → backpanel) and does nothing on the backpanel. Panel movement
is spatial (shift+h/j/k/l) and only works on panels. Entry is rebuilt on these
classes and, apart from the intended key changes, looks and behaves exactly as
before. `design.md` and `stack.md` document the model.

**Done when.** Entry opens with the tree focused; `esc` steps tree → panel →
backpanel and then does nothing; shift+hjkl move between panels only when a
panel has focus; the same holds from inside a form field; the dev confirms by
eye that Entry is otherwise unchanged; `design.md` documents the model; and the
full test suite passes.

## Vocabulary

From the backlog, used throughout:

| Term | Meaning | On Entry |
|---|---|---|
| **Backpanel** | The screen's outermost container, holding every panel | Holds the tree panel and the form panel |
| **Panel** | A bordered region of a screen | Left: tree panel. Right: form panel |
| **Content** | The focusable things inside a panel: trees, text fields, buttons, lists | The tree; the category-name, hanzi, translation and note fields; Create |

## Scope

### In

1. **New classes, alongside the old ones.** `Backpanel`, `Panel` and
   `TextField`, plus a screen base that composes them (name it in `plan.md`),
   in a new module. The existing `NavigableScreen`, `PanelAwareInput`,
   `SupaTree` key bindings and `FormPanel` stay untouched for the screens
   that still use them. *(Dev decision: Browse and Inspect Tree keep today's
   behaviour until M2, which moves them and deletes the old classes.)*
2. **Entry is rebuilt on the new classes.**
3. **The focus model**, below.
4. **The focus look**, below.
5. **Docs:** `design.md`'s navigation section is rewritten for the new model,
   with a short note that Browse, Inspect Tree and the menus follow the old
   conventions until M2. `stack.md` gets the screen-composition architecture.

### Out (deferred)

- **Browse, Inspect Tree, menus, placeholders, dialogs** — M2.
- **How menus fit the panel model** (backpanel → panel → list, or flatter) — M2's
  spec conversation. M1's classes shouldn't rule out either answer.
- **The standalone new-category form** — M3. M1 keeps Entry's current
  new-category behaviour (name + word together) unchanged.
- The broader modularity pass (duplicate tree builders, autocompile workers,
  per-screen CSS) — M2.

## The focus model

Four levels are involved: backpanel, panel, content, and — inside content —
whatever the widget already does (tree cursor, text caret).

### Keys

| Key | On the backpanel | On a panel | On content |
|---|---|---|---|
| `esc` | Nothing | Focus the backpanel | Focus its panel |
| `enter` | Focus the first panel's content (see *Going in*) | Focus the panel's content | Unchanged: whatever the widget does (tree: select node; Create: press) |
| `H`/shift+`←`, `L`/shift+`→` | Focus the leftmost/rightmost panel's content | Move to the panel on the left/right, landing in its content | Nothing — see *Shift-arrows mimic the letter keys*, below |
| `J`/shift+`↓`, `K`/shift+`↑` | Focus the bottommost/topmost panel's content | Move to the panel below/above, landing in its content | Nothing — same |
| `q` | Leave the screen | Leave the screen | Leave the screen, **except** in a text field, where it types |
| `tab` | Nothing | Focus the panel's content — same as `enter` | Screen-specific (Entry: next field / Create, wrapping, today's behaviour, kept) |

- **Spatial.** "The panel on the left" means the nearest panel whose region lies
  left of the current one; likewise right/up/down. **No wraparound**: at the
  edge, the key does nothing. Neighbours are worked out from the panels'
  on-screen geometry, not a per-screen list, so M2's stacked Browse layout
  needs no extra code.
  - On Entry: from the tree panel, shift+l goes to the form; shift+h does
    nothing. From the form panel, shift+h goes to the tree; shift+l does
    nothing. shift+j/k do nothing anywhere.
  - *This changes today's behaviour*: `H` and `L` currently both toggle between
    the two panels.
- **Only on panels — and the backpanel.** shift+hjkl act only when the panel
  or backpanel **itself** has focus, never when content does. A capital H
  typed while the tree has focus must not move panels, even though the tree
  doesn't consume it and it would otherwise reach the panel's (then the
  backpanel's) binding. *(Backlog: "I want the keybindings discussed
  (shift+jkhl) to work only when focusing the panels.")*
- **From the backpanel, H/L/J/K jump to the edge-most panel** in that
  direction — leftmost, rightmost, bottommost, topmost — landing in its
  content, the same way `enter` already reaches the first (leftmost, then
  topmost) one. *(Dev feedback, hands-on, added alongside the backpanel
  border below: once the backpanel was a visible place to be, only being able
  to reach the first panel from it — not the last, and not vertically — felt
  like a gap.)* Ties on the cross-axis break the same way `enter`'s "leftmost,
  then topmost" does: leftmost for a vertical jump, topmost for a horizontal
  one.
- **Shift-arrows mimic the letter keys exactly, including on content.**
  shift+`h`/`j`/`k`/`l` do precisely what `H`/`J`/`K`/`L` do at every level —
  move panels when a panel or the backpanel itself has focus, and **nothing**
  on content. *(Dev feedback, hands-on: the first drop of this milestone left
  `Tree`'s and `Input`'s own shift-arrow defaults in place on content — a
  tree cursor jumping to its parent on shift+left, a field extending its text
  selection — while the letter keys did nothing there. Confirmed as
  inconsistent rather than intended, so `EntryTree` and `TextField` now
  override those defaults to a no-op. This gives up `Tree`'s shift-arrow
  parent/sibling jump and `Input`'s shift-arrow text-selection while inside a
  panel on this model.)*

### Landing in content

"Land in a panel's content" (from shift+hjkl, from `enter` on a panel, or when
the screen opens) means: **focus the panel's first focusable, enabled,
visible content widget. If it has none, focus the panel itself.** *(Dev
decision: shift+hjkl land straight in content, not on the panel.)*

- Tree panel → the tree.
- Form panel with a valid target → its first enabled field (category-name for
  `(new category)`, hanzi otherwise), as today.
- Form panel **with no target** (a directory or file highlighted): every field
  and Create are disabled, so focus rests on the form panel. This matches
  today's `_switch_panel` special case, which now falls out of the general
  rule instead of being coded per screen.

### Going in

*(Dev decision: `enter` goes one level in, the mirror of `esc`.)*

- `enter` on the backpanel lands in the **first panel's** content: leftmost,
  then topmost.
- `enter` on a panel lands in that panel's content.
- `enter` on content is untouched. On Entry's tree it still selects the node
  and, for a valid target, jumps to the form's first field (today's
  behaviour, kept).

*(Dev feedback, hands-on: the first drop of this milestone only let `enter`
reach a panel's content — pressing `tab` on the tree panel did nothing,
while `tab` on the form panel already focused its first field, a
special case coded directly in `EntryScreen`. Fixed by having `Panel` bind
`tab` to the same `focus_content()` as `enter`, generally, rather than
leaving it to each screen. A panel's `tab` binding raises Textual's
`SkipAction` when the panel itself isn't focused, so a screen's own
field-cycling `tab` binding — Entry's `action_next_field` — still sees the
key once focus has moved onto a field.)*

### On opening

The screen lands in the first panel's content: on Entry, the tree. *(Backlog:
"when entering a screen, the cursor should focus on the content inside a panel,
not the panel itself, not the backpanel.")*

## The focus look

*(Dev decision: "accent = active, dim = rest".)*

- The panel you're in — the panel itself focused, **or** content inside it
  focused — has an **accent** border.
- Every other panel has a **dim** border.
- The **backpanel** itself has a border too, on the same convention: dim
  normally, accent when the backpanel itself has focus — every panel goes dim
  at the same time. *(Dev feedback, hands-on: added once the backpanel got
  H/L/J/K above, so that "being at the backpanel" is visible on screen, not
  just inferable from every panel going dim. Given a permanent, always-round
  border — never absent — so focusing the backpanel doesn't shift the layout
  by the border's width the way an appearing-only border would.)*
- Panel focused vs content focused is shown by the content itself: the tree's
  cursor line dims when the tree loses focus (Textual's own
  `$block-cursor-blurred-*` styling, already in place); a text field's caret
  disappears.
- The border belongs to the **panel**, not to the tree inside it. Entry's tree
  loses its own border, so there's no double frame.

**Intended visual changes from today** — everything else must look the same:

- The tree panel's border goes dim when the tree panel isn't active. Today the
  tree border is always accent.
- The form panel's border stays accent while a field inside it has focus. Today
  it only lights up when the form panel itself has focus.
- The whole screen now has a border (dim, or accent when the backpanel itself
  has focus) — new, per dev feedback above. It insets Entry's content by one
  cell on every side; nothing had a screen-edge border before.

Sizes are unchanged: the tree panel is content-sized with a 60% cap, the form
panel is 60% wide, fields are 40 wide.

## Constraints and context

- **Textual 8.2.8.** `:focus-within` is supported, so the accent border needs
  no Python. `escape` has no default binding: `App.ESCAPE_TO_MINIMIZE` only
  affects maximized widgets, and none are used. Disabling Textual's own
  auto-focus takes `Screen.AUTO_FOCUS = ""`, not `None`: `None` means
  "unset" and falls back to `App.AUTO_FOCUS` (`"*"` here, since `IdiomasApp`
  doesn't override it), so `None` on `PanelScreen` would still auto-focus the
  first focusable widget in DOM order before `on_mount`'s own landing logic
  runs. Verified empirically against the installed Textual version.
- **Bindings bubble** from the focused widget up through its ancestors. A
  binding on `Panel` therefore also sees keys pressed while its content has
  focus, which is why `esc` works from content without each content class
  binding it. The shift+hjkl actions still have to check that the panel itself
  is focused.
- **`HanziInput`** keeps its input-method switching on focus/blur (Sprint 2 M4)
  and becomes a `TextField` subclass. Its focus/blur guards must survive the
  new classes. `esc` from hanzi to the panel is a real blur and switches back
  to English International, as leaving the field does today.
- **`ConfirmDialog`/`PromptDialog`** are not touched. `PromptDialog`'s plain
  `Input` already avoids any app-level `escape` binding.
- **The old classes stay importable and unchanged in behaviour** so Browse and
  Inspect Tree's existing tests keep passing untouched.
