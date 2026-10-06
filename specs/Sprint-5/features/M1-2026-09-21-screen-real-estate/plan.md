# M1 · Screen real estate — plan

## 1. General overflow CSS on `Panel` and `Backpanel`

- In `app.tcss`, add `overflow-y: auto` to `.panel` and `.backpanel` (the
  classes `Panel`/`Backpanel` carry per `panels.py`'s `DEFAULT_CLASSES`).
  This is Textual's own "scrollbar only on overflow, no reserved gutter
  otherwise" behaviour — no custom scrollbar code.
- Remove `.select-list`'s `max-height: 8` (and its now-stale comment in
  `app.tcss`) per the Decisions in `requirements.md`. Keep `height: auto`
  so it still sizes to its content; it now relies on the panel it sits in
  (or the backpanel) to scroll when it's tall on top of everything else,
  rather than capping itself.
- Sanity-check every other `height: auto`/fixed-height rule in `app.tcss`
  (`.wizard-panel`, `.select-field`, `.dialog`) — none of these are the
  per-screen overflow band-aids the roadmap describes, so they're expected
  to need no change; confirm rather than assume.

## 2. Scroll-into-view on focus

- In `panels.py`, add a handler for `textual.events.DescendantFocus` on
  `Panel` and `Backpanel` (or a small shared mixin/base the two use, if that
  reads cleaner than duplicating the handler) that calls
  `event.widget.scroll_visible()` — bringing whatever just gained focus into
  view within any scrollable ancestor, including the panel/backpanel itself.
- Verify this fires for every way focus can land inside a panel today:
  `Panel.focus_content()`/`Backpanel.focus_content()`, `action_move`/
  `action_focus_edge` (shift+hjkl), `FormScreen.action_next_field` (`tab`
  cycling), and a screen's own `on_mount` landing focus. `DescendantFocus`
  bubbling should cover all of these without touching those call sites, but
  confirm with a quick manual check before relying on it.
- Do not add scroll handling to `Tree`/`OptionList`/`VimTree`/
  `VimOptionList` themselves — their own cursor/highlighted-row movement
  already scrolls within their own viewport in stock Textual, per
  `requirements.md`'s Context section.

## 3. Sweep and remove other per-screen overflow workarounds

- Grep `app.tcss` and every screen module for other height-capping or
  overflow-hiding rules introduced as one-off fixes (the roadmap's framing
  suggests there might be more than `.select-list`; confirm the actual count
  during implementation and update `requirements.md`'s Context note if it
  turns out to be more than one).
- Where a cap serves a real design purpose unrelated to overflow (e.g. a
  fixed width, not a height fix), leave it alone — only overflow-avoidance
  rules are in scope.

## 4. `design.md`: state the convention

- Add the scrollbar-on-overflow and scroll-into-view rules to
  `specs/current/design.md`, in the same section as the existing focus/`esc`
  conventions (the *Navigation conventions* section, near *The focus look*).
  State it once as a standing rule: every panel and backpanel scrolls rather
  than clips, a scrollbar takes no space unless content overflows, and
  whatever gains focus is scrolled into view — with the "no widget-identity
  change, no minimum panel height" clarifications from `requirements.md`'s
  Decisions.
- Mention `Panel`/`Backpanel`'s `overflow-y: auto` and the `DescendantFocus`
  handler in the *Implementation* subsection, alongside the existing notes on
  `Panel.focus_content()` etc.

## 5. Tests

- Add or extend tests in `tests/test_tui_panels.py` covering: a panel with
  more content than fits gets a scrollbar (via Textual's own overflow state,
  not a custom flag) and one that fits doesn't; focusing a widget below the
  visible region scrolls it into view (assert scroll offset changes, or that
  the widget's screen region is within the panel's visible region after
  focus).
- Confirm existing navigation tests (`esc`/`enter`/shift+hjkl, backpanel
  reachability) still pass unmodified — this milestone must not change that
  behaviour.

## 6. Hand-test pass at a small terminal

- Run the app at a deliberately short terminal (e.g. via Textual's
  `--size` test harness or a resized real terminal) against the five
  screens the roadmap names: Entry's form panel with every field shown,
  Browse's results on a long match list, Inspect Tree on a deep tree, the
  wizard's dependency checklist, and Settings' input-method form.
- Confirm for each: no scrollbar when content fits, a scrollbar appears
  when it doesn't, and moving focus/cursor to an off-screen row brings it
  back into view.
- This is the dev's own confirmation per `validation.md` — the agent's pass
  here is a pre-check, not a substitute for it.
