# M1 · Screen real estate — requirements

## Anchor

From [`../../roadmap-sprint-5.md`](../../roadmap-sprint-5.md):

**Deliverable.** Scrollbars appear only when content overflows, on every panel
and every flat menu, and take no space when it doesn't — a property of `Panel`
and `Backpanel` rather than per-screen CSS. Focus follows the cursor into
view: when a focused widget, or the selected row inside it, scrolls out of the
visible region, the screen scrolls it back into view. Every screen is checked
by hand at a small terminal. `design.md` gains the convention as a standing
rule. The navigation model is unchanged.

**Done when.** No screen shows a scrollbar it doesn't need; every screen that
overflows gets one; moving the cursor to a row outside the visible region
brings it into view on every tree, list and form in the app; the dev confirms
each screen by hand at a short terminal; `design.md` states the rule; and the
full test suite passes.

Backlog source ([`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Screen real estate*): "Every screen should automatically move the focus and
add a scrollbar only when the content does not fit the screen."

## Scope

In scope:

- Every `Panel` and `Backpanel` (per `design.md`'s model) gets scrollbar
  behaviour that appears only on overflow, general rather than per-screen.
- Scroll-into-view for whatever gains focus, so `tab`-cycling through a form
  (Entry, the wizard's steps, Settings' input-method form) never leaves the
  newly focused field off-screen.
- A pass over every screen at a small terminal: Entry's form panel with every
  field shown, Browse's results on a long match list, Inspect Tree on a deep
  tree, the wizard's dependency checklist, Settings' input-method form.
- `design.md` gains the convention as a standing rule, stated once, alongside
  the existing focus/`esc` rules.
- Removing the ad-hoc CSS this milestone's general rule replaces (the
  `.select-list` deployed list's own `max-height: 8` is the only one found in
  `app.tcss`; see Decisions).

Out of scope / explicitly unchanged:

- The navigation model: `esc`/`enter`/shift+hjkl, backpanel reachability, and
  the focus look are unchanged from Sprint 4 M1–M2.
- A scrollbar is not a panel and is never a focus stop.
- No widget's own internal cursor-scroll behaviour is touched (`Tree` and
  `OptionList` already scroll their own cursor/highlighted-row into view
  within their own viewport in stock Textual 8.2.8 — this milestone adds the
  *outer* panel/backpanel scroll-into-view for whatever holds the focus,
  layered on top, not a replacement for it).

## Decisions

Settled with the dev during this milestone's spec conversation, 2026-09-21.

| Decision | Rationale |
| --- | --- |
| **"Move the focus into view" means scroll-into-view only** — the focused widget itself never changes because it scrolled off-screen | Dev's choice. Matches `design.md`'s existing focus model: nothing about *which* widget has focus changes here, only what's visible. A bigger change (focus relocating to a different, currently-visible widget) isn't implied by the backlog wording and isn't built. |
| **The `.select-list` deployed list's `max-height: 8` cap is removed**, not kept on top of the general rule | Dev's choice, against keeping it as a deliberate cap. The list now grows with its content like every other panel and gets a scrollbar only when the *terminal* is too short for it, same as everywhere else — no more special-cased shorter cap. |
| **A panel too short to show even one full row just shows whatever partial content fits, clipped — no crash, no enforced minimum height** | Dev's choice. Standard scrollable-container behaviour; no special-casing for the degenerate case, and no minimum-size enforcement that would squeeze other layout to compensate. |
| **Textual's built-in `overflow-y: auto` is the mechanism**, not a hand-rolled scrollbar | Verified against the installed Textual 8.2.8 (`stack.md` requires ≥ 0.80): `overflow-y: auto` shows a scrollbar only when content overflows and reserves no gutter space when it doesn't — exactly the "appears only on overflow, takes no space otherwise" requirement, as a CSS rule on `Panel`/`Backpanel` rather than a rule per screen. |
| **Scroll-into-view is done via Textual's `DescendantFocus` event + `Widget.scroll_visible()`** | Both are stock Textual 8.2.8 APIs (`textual.events.DescendantFocus` bubbles to every ancestor when a descendant gains focus; `Widget.scroll_visible()` scrolls every scrollable ancestor so the widget is visible). Handling `DescendantFocus` once, on `Panel`/`Backpanel`, covers every way focus can land inside them (tab-cycling, shift+hjkl panel moves, `enter` landing in content, a screen's own focus calls) without a hook at each call site. |

## Context

- Today's ad-hoc state, from the roadmap: `app.tcss` gives a few widgets
  `height: auto` with a hand-picked `max-height: 8` — in the current codebase
  this is exactly one rule, `.select-list` (the deployed list `SelectField`
  shows; see [`panels.py`](../../../../src/idiomas/tui/screens/panels.py)).
  No other ad-hoc overflow rule exists in `app.tcss` today; this milestone's
  "one rule per place someone noticed a problem" is smaller in practice than
  the roadmap's framing suggested, but the principle — a general property of
  `Panel`/`Backpanel` instead of any per-screen rule — still applies.
- `Panel` and `Backpanel` are both `textual.containers.Vertical`/`Container`
  subclasses in `panels.py` — CSS `overflow-y: auto` on their shared classes
  (`.panel`, `.backpanel` in `app.tcss`) is a minimal, general change.
- `Tree` and `OptionList` (and their app subclasses `VimTree`/`VimOptionList`)
  are themselves `ScrollView`-based in Textual and already scroll their own
  cursor/highlighted row into view inside their own viewport — verified
  against Textual 8.2.8. This milestone's scroll-into-view code is for the
  *panel* around such a widget, or around a stack of plain widgets like
  Entry's form fields, not a reimplementation of what `Tree`/`OptionList`
  already do internally.
- The five screens the roadmap names as regression cases — Entry's form
  panel, Browse's results, Inspect Tree, the wizard's dependency checklist,
  Settings' input-method form — are this milestone's hand-test list (see
  `validation.md`).
