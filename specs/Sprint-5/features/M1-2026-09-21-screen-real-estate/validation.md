# M1 · Screen real estate — validation

Grounded in the roadmap's done-when: *"No screen shows a scrollbar it doesn't
need; every screen that overflows gets one; moving the cursor to a row
outside the visible region brings it into view on every tree, list and form
in the app; the dev confirms each screen by hand at a short terminal;
`design.md` states the rule; and the full test suite passes."*

## Automated

- `pytest` — the full suite passes, including whatever's added/extended in
  `tests/test_tui_panels.py` for this milestone (overflow-only scrollbar
  presence, scroll-into-view on focus) and the existing navigation tests
  (`esc`/`enter`/shift+hjkl, backpanel reachability) unmodified.
- A regression check specifically for the fixed bug: a panel whose content
  fits the terminal shows no scrollbar; the same panel with content that
  doesn't fit shows one — both asserted programmatically, not just by eye.

## Manual — by the dev, at a deliberately short terminal

For each of the five screens the roadmap names, resize to a small terminal
(short enough that the screen's content doesn't fit) and confirm:

1. **Entry — form panel with every field shown.** No field is silently
   clipped; a scrollbar appears on the form panel; `tab`-cycling to a field
   below the fold scrolls it into view.
2. **Browse — results on a long match list.** The results list scrolls
   (already true today, via `OptionList`'s own behaviour) and the panel
   around it never clips the list's border/footer; moving the highlighted
   result off-screen brings it back into view.
3. **Inspect Tree — a deep tree.** The tree scrolls its own cursor line
   into view (already true today, via `Tree`'s own behaviour); the panel
   around the tree never clips it.
4. **The wizard — dependency checklist.** A checklist longer than the
   terminal gets a scrollbar on its panel, not a silent clip; `tab`-cycling
   through checkboxes scrolls the focused one into view.
5. **Settings — input-method form.** Same as the wizard's own version of
   this form (`design.md`'s stated rule: the wizard and Settings share the
   same widgets for the same choice) — no clipping, scrollbar on overflow,
   focus follows into view.

Also confirm, on any one of the above:

- At a **generously sized** terminal (content fits), no screen shows a
  scrollbar it doesn't need — no reserved gutter, no visual change from
  today's behaviour.
- The **navigation model is unchanged**: `esc`/`enter`/shift+hjkl, backpanel
  reachability, and the focus look (accent/dim borders) all behave exactly
  as before. A scrollbar is never a focus stop — shift+hjkl and tab must
  skip over it.
- A panel shrunk smaller than one row of content shows a clipped partial
  view rather than crashing or corrupting the layout.

## Spec state

- `specs/current/design.md` states the scrollbar-on-overflow and
  scroll-into-view rule as a standing convention, in the same place the
  focus/`esc` rules live.
- `requirements.md`/`plan.md` reflect the actual implementation — including
  the real count of ad-hoc overflow rules found and removed in `app.tcss`
  (`requirements.md`'s Context currently names one, `.select-list`; update it
  if the sweep in `plan.md`'s step 3 finds more).

## Done when

All automated checks pass, the dev has confirmed all five screens plus the
two additional checks above by hand at a short terminal, and `design.md`
reflects the shipped convention. The dev's sign-off — not the agent's own
tests passing — is what closes this milestone, per the project's working
agreements.
