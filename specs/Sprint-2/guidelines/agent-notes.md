# Sprint 2 — agent notes

Agent-maintained companion to
[`motivation.md`](motivation.md), which is written by the programmer and is the
authoritative statement of intent. This file does not restate it; it tracks two
things across the sprint:

1. **Proposed features** raised in the motivation document — what was deferred,
   what was accepted into the sprint roadmap, and what has landed.
2. **Assumptions** the work rests on, so they can be revisited instead of
   silently inherited.

Update this file whenever a proposal changes status or a new assumption is made.

## Proposed features

| # | Item | Source section | Status |
| --- | --- | --- | --- |
| 1 | Installation wizard: PATH install, tree location, user name, language selection | *installation wizard* | **deferred — Later**, explicitly last in priority |
| 2 | Greeting on the landing menu: `[name]'s chinese notebook` | *installation wizard* | **deferred — Later** (part of #1) |
| 3 | Multi-language / multi-notebook support; German as an inert dummy entry | *installation wizard* | **deferred — Later**; waits for the wizard |
| 4 | `idiomas` runnable from anywhere, plug-and-play from a fresh clone | *installation wizard* | **deferred — Later**; a vision, not a commitment. Raised during M4 (2026-09-07): system-level dependencies (pandoc, xelatex, `macism`) should install transparently rather than by hand — a packaged distribution (e.g. a Homebrew formula with `depends_on`) is one way, not decided. Idea only, not scoped. |
| 5 | Sprint-based `specs/` restructuring and skill updates | *spec driven development guidelines and folder restructuring* | **done** — this structure |
| 6 | Stop tracking `notebook/` (and its contents) in git; remove what is already pushed | *git treatment* | **deferred — Later**; postponed while hand-testing, needs a go-ahead; see Risks |
| 7 | Vim navigation (`hjkl`) everywhere arrows work; `enter` selects; `q` goes back / exits from the main menu | *vim commands* | **done — M1**; see [`2026-09-06-m1-navigation-conventions`](../features/2026-09-06-m1-navigation-conventions/) |
| 8 | Entry screen: `shift`+`l`/`r` (arrows or `h`/`l`) switches panels; `esc` removed; `q` goes back | *enter vocabulary menu* | **done — M1**; see [`2026-09-06-m1-navigation-conventions`](../features/2026-09-06-m1-navigation-conventions/) |
| 9 | Right panel inaccessible with a "choose a category" notice when the cursor is not on a leaf | *enter vocabulary menu* | **done — M2**; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 10 | `(uncategorized)` shown for every file, not only files that already hold loose entries | *left panel* | **done — M2**; reverses a Sprint 1 decision (M5.2); see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 11 | Root tree node renamed from `source` to `[language] notebook` | *left panel* | **done — M2**; needs `Config.language`; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 12 | Remove the bottom scrollbar; the tree view sizes to its content | *left panel* | **done — M2**; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 13 | Footer instructions updated to match the new key map | *right panel* | **done — M2**; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 14 | Replace the thick input cursor ("beam") with something lighter, everywhere inputs appear | *right panel*, *other menus* | **done — M2**; app-wide `.tcss`, covers browse too; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 15 | Pinyin field read-only and skipped by `tab` (hanzi → translation) | *right panel* | **done — M2**; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 16 | Rename the `gloss` field to `translation` | *right panel* | **done — M2**, UI layer only; see [`2026-09-06-m2-entry-screen-corrections`](../features/2026-09-06-m2-entry-screen-corrections/) |
| 17 | Automatic input-method switching, macOS only, between Pinyin Simplified and English International | *right panel* | **done — M4**; see [`2026-09-07-m4-macos-input-method-switching`](../features/2026-09-07-m4-macos-input-method-switching/); MVP hardcodes both keyboard names for Chinese only — see Decisions and Assumptions |
| 18 | Autocompile on file/category switch after at least one entry, and on leaving the entry screen | *autocompile* | **done — M3**, scope narrowed to exit-only (see Decisions); see [`2026-09-07-m3-autocompile`](../features/2026-09-07-m3-autocompile/) |
| 19 | `q` (not `esc`) exits every menu | *other menus* | **done — M1**; see [`2026-09-06-m1-navigation-conventions`](../features/2026-09-06-m1-navigation-conventions/) |
| 20 | Fuzzy finder panels switchable with the same `shift`+`hjkl` combination | *other menus* | **done — M1**; see [`2026-09-06-m1-navigation-conventions`](../features/2026-09-06-m1-navigation-conventions/) |
| 21 | A skill (or equivalent) encoding the panel/navigation conventions so they need not be restated | *other menus* | **done — M1**, as a section of `stack.md`; see Decisions and [`2026-09-06-m1-navigation-conventions`](../features/2026-09-06-m1-navigation-conventions/) |
| 22 | Entry screen real estate: the form panel's 5 fields + Create button don't all fit in a default-size terminal window (Create clips off the bottom) — needs a layout discussion (scroll the form, shrink field heights, resize threshold, etc.) | raised during M2 hand-testing, not from `motivation.md` | **deferred — Later**, first item in the deferred list; not yet a milestone — surfaced by the programmer while testing M2, not scoped or decided |
| 23 | Keyboard selection (local + international) as a main-menu config option, so it can be changed after the wizard without re-running it | raised during M4's spec conversation, not from `motivation.md` | **deferred — Later**; folded into the installation wizard's *Later* entry (#1) |

## Decisions

Made during the roadmap discussion, recorded because the motivation document
left them open.

| Decision | Rationale |
| --- | --- |
| The navigation conventions (#21) live as a **section of [`../../stack.md`](../../stack.md)**, not a `.claude` skill or a new file | Programmer's choice. A skill would be agent-only and invisible as documentation; a section keeps `specs/` small and the conventions readable by both of us. |
| `gloss` → `translation` (#16) is a **UI-layer rename only** | The widget id, field order, placeholder and tests change. `Entry.gloss` and the on-disk format keep the old name — renaming those reaches the parser, the writer and every fixture for nothing the user can see. |
| `Config` gains `language: str = "Chinese"` (#11) | The tree root needs a language to read. Defaults cleanly for the existing `.idiomas.toml`, and the wizard (#1) later writes it instead of inventing its own storage. |
| Sprint 2 is **four milestones**; #6 and #1–#4 go to *Later* | Git treatment is destructive and blocked on the testing question; the wizard is explicitly last by the programmer's own note. |
| M1's `q`/panel-switch handling lives in a shared base **`Screen` class** (`NavigableScreen`), not a mixin or per-screen duplication | Programmer's choice, made when M1's spec was scoped — Textual has no built-in "Input has focus" guard for `BINDINGS`, so centralizing it once avoids four copies of the same check. |
| `EntryTree`'s `right`→`select_cursor` override (a Sprint 1 decision) is **removed** in M1 | It predates `shift+l` as the panel-switch key and made plain `l`/right act like `enter`. With `shift+l` owning panel-switching, plain `l`/right reverts to `Tree`'s default (expand/no-op on pre-expanded leaves), leaving `enter` as the only way to choose. |
| Browse's three stacked panels cycle **linearly with wraparound** via `shift+h`/`shift+l` | Matches the entry screen, where toggling between only 2 panels is inherently a wraparound; keeps the convention uniform across screens rather than special-casing browse's 3-panel case. |
| M1 does **not** add compile-on-exit for the entry screen | Entries are saved to disk immediately on Create, so `q` never loses *entered* data — only a possibly-stale PDF. Full autocompile (per-file dirty-tracking, compile-on-navigation) is #18/M3's job; M1 only wires up keys. Recorded as a scope boundary between M1's "no silent loss" bar and M3's autocompile feature. |
| M1's panel-switch keys are **`H`/`L`** (capital letters), not `shift+h`/`shift+l` | Discovered during implementation: Textual reports Shift+H as key `"H"` — a letter already encodes case, so there is no separate `shift+h` key name to bind. Verified against `textual.events.Key` directly. |
| A new **`PanelAwareInput`** wraps every text field in the app | `Input` intercepts every printable character (including `H`/`L`) for itself before any screen-level binding runs, and separately claims `shift+left`/`shift+right` for its own text-selection. Neither can reach the screen unmodified, so `PanelAwareInput` overrides just `shift+left`/`shift+right` to dispatch to the screen's panel-switch actions — the only way to leave a focused field by keyboard. Cost: `Input`'s native shift-arrow text-selection no longer works inside any field in this app. |
| `MainMenuScreen` overrides `action_back_or_quit` directly (`self.app.exit()`) rather than `NavigableScreen` detecting "root screen" via stack length | `len(self.app.screen_stack) > 1` doesn't distinguish the main menu — Textual's `App` always keeps an implicit base `Screen` under everything the app pushes, so the stack is at length 2, not 1, even when `MainMenuScreen` is the only screen the app itself put there. |
| `BrowseScreen.AUTO_FOCUS = "#results"` | Textual's default `AUTO_FOCUS` ("*") lands on the first focusable widget in compose order — the filename filter, an `Input`. That left a freshly-opened browse screen unreachable via `q` alone until focus moved off the `Input` first, violating M1's "driven end to end with hjkl, enter and q alone" bar right at the screen's default state. Found via an end-to-end smoke test, not anticipated at spec time. |
| `escape` is **reintroduced**, post-M1, with narrower semantics: it defocuses the current field onto its containing panel (`NavigableScreen.action_defocus_panel`, overridden only by `EntryScreen` → a new focusable `FormPanel`), not "back to the tree" | Programmer's hands-on-testing feedback right after M1 merged: on the entry screen, `shift+h`/`H` are indistinguishable from ordinary keystrokes while any of the five form fields has focus, so there was no way to reach `q`/panel-switching without first tabbing all the way to a widget that isn't an `Input`. `escape` fills exactly that gap — a resting state between "editing a field" and "on the tree" — without reviving Sprint 1's old escape-goes-to-tree behavior. Single-field panels (a lone filter `Input`, an `OptionList`) have no such gap and leave `action_defocus_panel` as a no-op, so `escape` is inert there. `Tab` from the panel-focused state goes to the first field. |
| M2's inert-form state (#9) **disables the four fields + Create button, doesn't hide them**; the top slot swaps between `#category-name`, a "choose a category" warning, and (for `new_category`) nothing extra | Programmer's choice during M2's spec conversation — mirrors the existing `new_category` layout shape (message/field in the top slot + fields below) rather than adding a second, hide-based layout. |
| `EntryScreen.__init__` takes the whole `Config`, not just `source_root` (#11) | `Config.language` is needed for the tree-root label; passing the whole object avoids adding a second constructor parameter and keeps the call site future-proof for other `Config` fields the entry screen might need later. |
| `gloss` → `translation` (#16) rename also covers the **local Python variable** inside `_create_entry`, not just widget id/placeholder/tests | Programmer's choice during M2's spec conversation, for readability — `Entry.gloss` (the dataclass field) is unaffected; the renamed local is still passed as `Entry(gloss=translation, ...)`. |
| M2's thinner cursor (#14) uses `background: $accent 40%` over the character, not `background: transparent; text-style: underline` | The underline version, first shipped on this branch, rendered as an underline stamped on the *placeholder* text's first letter when a field was empty (looked like a keyboard-shortcut hint, not a cursor) — caught by the programmer via a screenshot during hand-testing, reproduced with a Textual `save_screenshot()` capture. A translucent block keeps the cursor legible over both placeholder and typed text while still being lighter than the default full-contrast block. |
| M3 (#18) implements **only** "compile on leaving the entry screen" — the roadmap's condition 2. "Compile on cursor move to a different file" (condition 1) is dropped, not deferred to *Later* | Programmer's choice during M3's spec conversation: condition 1 was a mechanism to compile sooner, not a feature people asked for on its own — compiling everything touched, once, on exit, reaches the same end state (an up-to-date PDF with no manual *Compile* visit) with far less tracking complexity. Still satisfies the roadmap's own "Done when" text, which only checks the state after leaving the screen. |
| M3's compile-on-exit worker is started with **`self.app.run_worker(...)`, not `self.run_worker(...)`** | Found in Textual's own source (`widget.py`'s `Widget._on_unmount` calls `self.workers.cancel_node(self)`): any worker owned by a widget/screen is cancelled the instant that node unmounts. A worker started on `EntryScreen` itself would be cancelled mid-compile the moment `q` pops the screen. Owning it on the `App` (which doesn't unmount on a screen pop) lets the compile actually finish after the user has already left. |
| M4's two keyboard names (`Pinyin Simplified`, `English International`) are **hardcoded constants**, not `Config` fields, and only apply to the Chinese notebook | Programmer's choice during M4's spec conversation. The real architecture is a future installation wizard that asks for the user's local and international keyboards (#1); until it exists, M4 hardcodes the wizard's would-be answers instead of half-building config plumbing for a single language. A per-language pair would differ for German or any future language — out of scope while only Chinese is functional. Changing the pair later is #23, deferred to *Later*. |
| `HanziInput._on_focus`/`_on_blur` **ignore app-level refocus/reblur** (`event.from_app_focus` and `self.app.app_focus`), not just widget-level focus changes | Found during M4 hand-testing: the programmer reported the input source switching continuously until pressing `escape`. Cause: `macism` switches input sources by simulating the OS hotkey, which makes the terminal briefly lose and regain OS window focus; Textual reports that as an `AppBlur`/`AppFocus` pair that unfocuses and refocuses whatever widget is currently focused (`App._watch_app_focus`), indistinguishable from a real blur/focus without checking these two flags — without the guard, each switch re-triggered the other, looping forever. See [`2026-09-07-m4-macos-input-method-switching/plan.md`](../features/2026-09-07-m4-macos-input-method-switching/plan.md) §5. |

## Closing note

Sprint 2 closed on 2026-09-09, when Sprint 3 was opened.

| | |
| --- | --- |
| **Landed** | All four roadmap milestones: M1 navigation conventions, M2 entry screen corrections, M3 autocompile (exit-only scope), M4 macOS input-method switching. Every one has a spec folder in [`../features/`](../features/) and a section in [`../../current/changelog.md`](../../current/changelog.md). |
| **Dropped** | Nothing from the roadmap. Within M3, condition 1 (compile on cursor move to a different file) was dropped rather than deferred — see the Decisions table. |
| **Carried forward** | Sprint 3's roadmap is written strictly from its own backlog. The programmer's standing deferred list — installation wizard (#1–#4), keyboard selection in settings (#23), entry screen real estate (#22), and Sprint 1's own deferred items — is theirs to manage in `postponedfeatures.md`, not something Sprint 3 inherits by default. Of Sprint 2's *Later* list, only git treatment (#6) reappears in Sprint 3, because the programmer put it in the Sprint 3 backlog. |


## Assumptions

| Assumption | Origin | Notes |
| --- | --- | --- |
| Both macOS input sources — Pinyin and English International — are already installed | motivation · *right panel* | Stated by the programmer. Behaviour when one is missing is undefined; needs a fallback before shipping #17. |
| Input-method switching is macOS-only | motivation · *right panel* | Linux/other platforms simply do nothing. |
| Source tree and notebook tree always move together; one location covers both | motivation · *installation wizard* | "no exception". |
| Only Chinese is functional; German is a menu entry that does nothing | motivation · *installation wizard* | Guards against building multi-language plumbing early. |
| `q` never destroys unsaved work — saving/compiling happens on the way out | motivation · *vim commands* | Edge-case handling left to the agent's judgement; recorded here because it is a correctness commitment, not a UI detail. |
| The programmer is mid-hand-testing on a real notebook | motivation · *git treatment* | Any change touching `notebook/` or `source/` must be non-destructive to local content. |
| An existing `.idiomas.toml` without a `language` key still loads, defaulting to `"Chinese"` | M2 spec conversation | `Config.language` is new in M2; the default keeps the programmer's current (untracked, hand-edited) config file working without a manual update. |
| `macism` (the `laishulu/macism` CLI) is installed separately by the programmer; the app does not install it | M4 spec conversation | Installed on the programmer's machine mid-implementation via `brew tap laishulu/homebrew; brew install macism` (not in `homebrew-core`, needs the author's tap). Both hardcoded source ids confirmed live against it — see [`2026-09-07-m4-macos-input-method-switching/requirements.md`](../features/2026-09-07-m4-macos-input-method-switching/requirements.md). |
| Accessibility permission is already granted to whatever process invokes `macism` | M4 spec conversation | Programmer raised in-app permission-prompting as an option; deferred for the MVP. Missing permission degrades the same way as a missing input source: silent no-op. Untested so far — the live verification on this machine didn't trigger a permission prompt, so the no-op path for a *missing* grant is still unexercised. |

### Inherited from Sprint 1, now under revision

Sprint 1 is closed and its notes are not edited. These are its assumptions that
Sprint 2 reopens, restated here so the change of mind lives in this sprint.

| Sprint 1 assumption | Reopened by | Now |
| --- | --- | --- |
| Only one language (Chinese) exists, so no notebook selection is needed | #1, #3 · *installation wizard* | The wizard asks for a language; German exists as an inert entry. Multi-language plumbing is still out of scope. |
| The notebook and source trees are tracked in git | #6 · *git treatment* | To be untracked and removed from the remote — private content. Postponed until hand-testing ends. |
| `(uncategorized)` is shown only for files that hold loose entries | #10 · *left panel* | To be shown for every file. |

## Carried over from Sprint 1

Sprint 1 closed with one milestone unimplemented. Its own files are frozen, so
the verdict is recorded here.

| Item | Verdict |
| --- | --- |
| M6 · Seed content — a starter tree so a fresh clone is not empty | **Dropped.** Hand-testing with a real notebook took its place. A fresh clone starts empty. Note the interaction with #6: if `notebook/` and `source/` stop being tracked in git, nothing ships starter content, so a fresh clone will be empty by design. |

## Risks

- **#6 (git treatment) is destructive.** It means untracking and removing already
  pushed private content, and it interacts with whatever the tests read. Do not
  act on it without an explicit go-ahead, and settle the testing question first.
- **#10 contradicts a Sprint 1 decision** (M5.2 deliberately hid
  `(uncategorized)` when a file had no loose entries). Treat it as an
  intentional reversal and record it above, under *Inherited from Sprint 1* —
  Sprint 1's own files stay as they were written.
