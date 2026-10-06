# M4 · macOS input-method switching — validation

Acceptance bar for this branch, grounded in the roadmap's own **Done when**
condition.

## Automated

- `uv run pytest tests/test_input_method.py -v` — all four cases pass (see
  `plan.md` §3): non-Darwin no-op, Darwin+macism-present switches, Darwin+
  macism-missing no-ops without raising, Darwin+source-rejected no-ops
  without raising.
- Full suite still green: `uv run pytest`.
- `tests/test_input_method.py` must be importable and runnable on a non-Mac
  CI runner without error — this is the "switching module imports and tests
  without a Mac" bar from the roadmap, made literal.
- `uv run pytest tests/test_tui_entry_screen.py -k input_method` — covers
  focus-in/blur-out switching, and the fixed continuous-switching bug
  (posting a real `AppBlur`/`AppFocus` pair while the hanzi field has focus
  must not re-trigger either switch function). See `plan.md` §5.

## Manual (programmer's machine, macOS only)

- With `macism` installed and Accessibility permission granted:
  1. Open the entry screen, focus the hanzi field. Confirm (visually, via the
     macOS menu-bar input indicator) the system input source switches to
     Pinyin Simplified **once**, and holds steady — it must not keep
     flipping back and forth (the bug found and fixed in `plan.md` §5).
  2. Type hanzi with no manual keyboard switch needed.
  3. Move focus off the hanzi field (tab to translation, or blur otherwise).
     Confirm the system input source reverts to English International.
- With `macism` temporarily renamed/removed, or Accessibility permission
  revoked: repeat the same focus/blur sequence and confirm the app does not
  crash or show an error — typing still works in whatever the OS defaults
  to, just without the automatic switch.

## Cross-platform

- Run the app (or at least import `idiomas.input_method` and call both
  functions) on a non-macOS machine or a `platform.system()`-patched
  environment, and confirm no exception and no attempt to invoke `macism`.

## Out of scope for this validation

- The installation wizard and the main-menu config option (`#1`, `#23`) —
  neither exists yet; nothing here should require them.
- Any keyboard pair other than Pinyin Simplified / English International, or
  any language other than Chinese.
