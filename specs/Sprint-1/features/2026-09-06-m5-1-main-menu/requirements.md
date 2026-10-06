# M5.1 · Main menu — Requirements

## Roadmap anchor

M5 as a whole: **The TUI** — "The point of the whole thing." `tui/`, styled with `app.tcss`.

**M5.1 deliverable.** A focusable list: *Enter vocabulary*, *Browse*, *Compile*, *Notebook*, *Inspect tree*, *Quit*. *Notebook* and *Inspect tree* are placeholders that display their resolved path; changing the shell's working directory is out of scope.

M5's overall **Done when** (spans all three sub-phases, only partially checkable here): *Twenty words can be entered into one category without touching the tree; a new category can be created and immediately filled; an empty category name produces an uncategorized entry above the first `##`; and the resulting file's formatting and tag placement survive inspection.*

## Scope

M5 is split into three sub-phases with their own branch/spec each (confirmed with the user, given how different M5.1/M5.2/M5.3 are in size and complexity). This spec covers **M5.1 only**.

In scope:

- `src/idiomas/tui/app.py` — `IdiomasApp`, a Textual `App` holding the resolved `Config` (source/notebook roots), pushing `MainMenuScreen` as its initial screen.
- `src/idiomas/tui/app.tcss` — stylesheet for the app (per the roadmap's own file naming).
- `src/idiomas/tui/screens/main_menu.py` — `MainMenuScreen`: a focusable list (Textual `OptionList`) with, in this exact order: *Enter vocabulary*, *Browse*, *Compile*, *Notebook*, *Inspect tree*, *Quit*.
  - *Enter vocabulary* and *Browse* → placeholder screens for now (their real screens are M5.2/M5.3's job, confirmed with the user).
  - *Compile* → **wired for real**: calls M4's `compile_all(config.source_root, config.notebook_root)` and shows the result (files compiled vs. "everything up to date"). `compile_all()` already only recompiles a `.md` whose `.pdf` is missing or stale (mtime-based) — never blindly rebuilds everything; confirmed with the user this mtime check is exactly the "only compile flagged files" behavior they wanted, no separate flagging mechanism needed.
  - *Notebook* → placeholder screen displaying `config.notebook_root`'s resolved absolute path.
  - *Inspect tree* → placeholder screen displaying `config.source_root`'s resolved absolute path.
  - *Quit* → exits the app (`app.exit()`).
- `src/idiomas/tui/screens/placeholder.py` — one reusable `PlaceholderScreen(message: str)` used for all four placeholder cases above (Enter vocabulary, Browse, Notebook, Inspect tree), each given its own message. `Escape` (or a visible "back" hint) returns to the main menu.
- **`__main__.py` change:** `python -m idiomas` with **no subcommand now launches the TUI** (confirmed with the user — M5 is "the point of the whole thing," superseding M0's original "does nothing" done-when). `compile` and `doctor` remain as separate, non-interactive CLI subcommands, unchanged, and continue to work exactly as in M4.
- **Config loading happens before the TUI takes the screen.** `load_or_prompt_config()` (M4) uses plain `input()`, which cannot coexist with Textual's alternate-screen-buffer rendering. So the no-arg path in `__main__.py` calls `load_or_prompt_config()` *before* constructing/running `IdiomasApp`, and passes the resolved `Config` into the app. No screen ever prompts for config itself.
- Automated tests using Textual's `Pilot` (headless run), confirmed with the user (supersedes stack.md's "TUI is verified by hand" for this milestone, at least for interaction logic worth automating): menu renders all six items in order, each item navigates/acts correctly, Quit exits the app.

Explicitly deferred:

- The real entry screen (M5.2) and browse screen (M5.3) — placeholders only, in this phase.
- Any shell integration to actually `cd` for *Notebook*/*Inspect tree* — roadmap's own "Later" section defers this indefinitely; displaying the resolved path is the whole deliverable here.
- Async/background compilation — *Compile* calls `compile_all()` synchronously (blocking the UI briefly, a few seconds at most for a handful of files). If this becomes noticeably slow as the vocabulary grows, revisiting with a Textual worker/background thread is a natural follow-up, not something this phase builds preemptively.

## Decisions

- **Three separate sub-phase branches/specs for M5**, not one. Confirmed with the user given M5.2's density (tree nav, category creation, tab cycling, pinyin prefill) relative to M5.1/M5.3.
- **`python -m idiomas` (no args) launches the TUI.** Confirmed with the user. This is a real behavior change from M0–M4; `compile`/`doctor` subcommands are unaffected.
- **Config is resolved before the TUI starts**, never inside a screen — see Scope above. This is a hard technical constraint (input() vs. Textual's screen ownership), not a style preference.
- **Compile is wired for real in M5.1**, not stubbed — it was already fully implemented in M4 and needed no new logic beyond calling `compile_all()` and displaying its result, so there was no reason to defer it as a placeholder alongside the genuinely-not-yet-built entry/browse screens.
- **Automated Pilot tests for this phase's interaction logic**, on top of (not instead of) manual verification — confirmed with the user, who wants this for M5 generally, not just the trickier M5.2 logic.

## Context

- Builds on M4's `compile_all`/`Config`/`load_or_prompt_config` directly.
- `stack.md`'s "TUI — Textual" section already fixed the widget choice rationale (`Tree`, `Input`, `Horizontal`, focus chain over `prompt_toolkit` or raw `curses`) — this phase's menu uses Textual's `OptionList` for the focusable list, consistent with that reasoning.
- M5.2 and M5.3's specs will each replace one of this phase's placeholder screens with the real thing; `PlaceholderScreen` is deliberately generic (a message string) so it's trivial to stop using for a given menu item once its real screen exists.
