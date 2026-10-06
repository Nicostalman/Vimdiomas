# M4 · macOS input-method switching — requirements

## Roadmap anchor

From [`../../roadmap-sprint-2.md`](../../roadmap-sprint-2.md#m4-macos-input-method-switching):

**Deliverable.** On macOS, focusing the hanzi field switches the system input
source to Pinyin Simplified; leaving it switches back to English
International. A no-op on every other platform, and a no-op — not a crash —
when an expected input source is not installed.

The MVP supports exactly these two keyboards, and only for the Chinese
notebook. The intended architecture is a future installation wizard that asks
the user for their local and international keyboards; this milestone
hardcodes the wizard's would-be answers instead of building that wizard.

**Done when.** Typing hanzi on the programmer's machine needs no manual
keyboard switch; the app runs unchanged on a machine with neither input
source installed; and the switching module imports and tests without a Mac.

## Scope

**In scope**

- A new, isolated module (`src/idiomas/input_method.py` or similar) with two
  operations: switch-to-Pinyin, switch-to-English-International. Called from
  the entry screen's hanzi field focus/blur.
- macOS-only behavior. Every other platform (checked via `platform.system()`
  or `sys.platform`) is a no-op — the module still imports and its functions
  are still callable, they just do nothing.
- Graceful handling when the expected input source isn't installed/found: a
  no-op, not a crash or a visible error to the user. Same treatment for a
  missing switching mechanism (see Decisions) or missing Accessibility
  permission — none of these are distinguished from each other in the MVP;
  they all resolve to "the switch silently didn't happen."
- Unit tests that run on any platform (mocking the macOS-specific parts), per
  the roadmap's "imports and tests without a Mac" bar.

**Explicitly deferred (not this milestone)**

- The installation wizard itself (`#1`, roadmap *Later*). This milestone
  hardcodes its answers; it does not build the thing that asks the question.
- A main-menu config option to change the keyboard pair after the fact
  (`#23`, roadmap *Later*).
- Any in-app flow that proactively requests Accessibility permission from the
  user (e.g. triggering the system permission dialog). The MVP assumes the
  permission is already granted, exactly as it assumes both input sources are
  already installed — both are the same class of "environment not fully set
  up" case, and both degrade the same way (no-op). Revisit if hand-testing
  shows this is confusing rather than harmless.
- Support for any keyboard pair other than Pinyin Simplified / English
  International, and for any notebook language other than Chinese.

## Decisions

| Decision | Rationale |
| --- | --- |
| Switch mechanism: shell out to the `macism` CLI (`laishulu/macism`), via `subprocess` | Considered three options with the programmer: PyObjC/Carbon TIS calls directly (fastest, but a heavy dependency and fiddly CF/ObjC bridging for a two-input-source MVP), AppleScript via `osascript` (no extra install, but slow and fragile for input-source switching specifically), and `macism` (a small, purpose-built, already-proven tool for exactly this). `macism` wins on simplicity: one subprocess call per switch, and "binary not found" collapses naturally into the same no-op path as "source not installed" — `FileNotFoundError` on `subprocess.run` is easy to catch and matches the roadmap's no-op requirement without extra plumbing. Cost: requires `macism` installed separately (e.g. `brew install laishulu/tap/macism`), which the app cannot install for itself — worth a Homebrew note in the module's docstring / README, not app-managed. |
| Input source identifiers are **discovered on the programmer's own machine**, not guessed, and hardcoded as constants | Read via `defaults read ~/Library/Preferences/com.apple.HIToolbox.plist AppleEnabledInputSources` during this spec conversation: Pinyin Simplified is `com.apple.inputmethod.SCIM.ITABC`; English International's id was inferred from Apple's `com.apple.keylayout.<Name>` convention as `com.apple.keylayout.USInternational-PC`. Both are now **confirmed** — after installing `macism` (`brew tap laishulu/homebrew; brew install macism`), running it with no arguments prints the *current* input source id, and it reported `com.apple.keylayout.USInternational-PC` before any switch, and `com.apple.inputmethod.SCIM.ITABC` right after `macism com.apple.inputmethod.SCIM.ITABC`. Both `input_method.switch_to_pinyin()`/`switch_to_english_international()` were exercised live and produced the expected switch each time. |
| Missing-permission and missing-input-source are **not distinguished** in the MVP | Both are "the environment isn't fully set up" and both must be non-fatal per the roadmap. Telling them apart would need inspecting `macism`'s stderr/exit code and deciding what to do differently for each — no requirement calls for that distinction yet. If hand-testing shows the silent failure is confusing, that's a follow-up, not a blocker for M4. |
| Called from **focus/blur on the hanzi `Input`** specifically, not from screen-level mount/unmount | Matches the roadmap's own wording ("focusing the hanzi field... leaving it..."). The hanzi field is the only one that should ever be in Pinyin; every other field (including navigating the tree, or focusing translation/tags) should be in English International, so blur is the natural "switch back" trigger rather than trying to track it at the screen level. |

## Assumptions (carried and new)

- Both input sources are already installed on the target machine — inherited
  from the roadmap's own "Assumption on record", now further narrowed:
  specifically `com.apple.inputmethod.SCIM.ITABC` and (pending verification)
  `com.apple.keylayout.USInternational-PC`.
- `macism` is installed separately by the programmer before this feature is
  useful to them; the app does not install it. New assumption from this
  spec conversation — recorded in `agent-notes.md`.
- Accessibility permission for whatever process invokes `macism` (the
  terminal, or the packaged app later) is already granted. New assumption
  from this spec conversation, raised by the programmer — recorded in
  `agent-notes.md`.
