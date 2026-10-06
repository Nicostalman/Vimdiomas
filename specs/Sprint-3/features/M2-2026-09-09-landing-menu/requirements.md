# M2 · Landing menu — Requirements

## Roadmap anchor

From `specs/Sprint-3/roadmap-sprint-3.md`:

**Deliverable.**

- A new screen shown at launch, before the notebook menu: one entry per language
  plus *Settings*. With Chinese and German registered, that reads *Chinese
  notebook*, *German notebook*, *Settings*.
- *Chinese notebook* opens the existing notebook menu, against `tree-Chinese/`.
- *German notebook* is an inert dummy. Multi-language plumbing is not built this
  sprint.
- *Settings* opens a submenu whose items are **all dummies** — add a language,
  remove a notebook, and whatever else fits.
- `q` on the landing menu exits the app; `q` on the notebook menu now returns to
  the landing menu rather than exiting. `design.md`'s navigation section is
  updated in place.

**Done when.** Launching the app lands on the language menu; *Chinese notebook*
reaches the notebook menu and `q` comes back; *German notebook* and every
*Settings* item are visibly present and do nothing; `q` on the landing menu
exits; and `design.md` reflects the new screen order.

## Scope

- A new `LandingMenuScreen`, pushed by `IdiomasApp.on_mount` instead of
  `MainMenuScreen` (the notebook menu). It becomes the app's root screen.
- A new `SettingsScreen`, reached from the landing menu's *Settings* entry.
- `MainMenuScreen` (the notebook menu) stops being the root screen: it no longer
  overrides `action_back_or_quit` to exit, so `q` there falls back to
  `NavigableScreen`'s default pop, returning to the landing menu.
- `design.md`'s navigation table and implementation notes are updated to reflect
  that the landing menu, not the notebook menu, is now the root screen.

## Decisions (from the spec interview, 2026-09-09)

| Decision | Rationale |
| --- | --- |
| The language list is a **hardcoded module-level constant** (name + whether it's functional), not read from `Config` | The wizard, not this milestone, owns real language registration (`backlog.md` · *Landing menu*; `notes-sprint-3.md`'s Postponed table). A constant is the simplest thing that satisfies "German is inert" without inventing config surface the wizard will redo. |
| The Settings submenu lists exactly the two items the backlog names — **"Add a language"** and **"Remove a notebook"** — nothing extra | The backlog's "whatever else fits" is not a requirement; the two named items are enough to demonstrate the submenu shape without guessing at a third. |
| The notebook menu's existing **"Quit" option is removed outright**, not repurposed | `q` already returns to the landing menu now that the notebook menu isn't root. A "Quit" menu item that actually quit the app would be a dead-end inconsistent with `q`'s new meaning; renaming it to "Back" would just duplicate `q` under another label. |
| The landing menu, notebook menu, and Settings submenu share their look through a new `MenuScreen` base (CSS class `menu-screen`) rather than each carrying its own styling | Raised by the dev after manual testing: the landing/Settings screens hadn't picked up the notebook menu's centered, bordered look, since `app.tcss` targeted `MainMenuScreen` by name. The dev wants to be able to change every menu's aesthetic together in the future — the same "one place to change them all" reasoning as M3's tree widget — so this is a shared base now rather than three copies of the same CSS block. |

## Out of scope

- Any real functionality behind *German notebook*, *Add a language*, or *Remove a
  notebook* — all three are dummy destinations (a `PlaceholderScreen`).
- Reading the language list from `Config` or any wizard-owned source.
- Changes to `MainMenuScreen`'s own entries beyond removing "Quit" — M4 (Inspect
  Tree functional / removing the "Notebook" entry) is a separate milestone.
