# M4 · macOS input-method switching — plan

## 1. The switching module

- Add `src/idiomas/input_method.py`.
- Module-level constants: `PINYIN_SIMPLIFIED_SOURCE_ID = "com.apple.inputmethod.SCIM.ITABC"`
  and `ENGLISH_INTERNATIONAL_SOURCE_ID = "com.apple.keylayout.USInternational-PC"`
  — both confirmed live against `macism` on the programmer's machine (see
  `requirements.md` Decisions).
- A single internal helper, `_select_source(source_id: str) -> None`, that:
  - No-ops immediately if `platform.system() != "Darwin"`.
  - Otherwise runs `subprocess.run(["macism", source_id], ...)`, catching
    `FileNotFoundError` (macism not installed) and `subprocess.CalledProcessError`
    (source id not found/available) and swallowing both as a no-op. Do not
    catch broader exceptions blindly.
- Two public functions built on the helper: `switch_to_pinyin()` and
  `switch_to_english_international()`. Keep the public surface to these two —
  callers should never need to pass a source id themselves, since the MVP
  only ever switches between this one hardcoded pair.

## 2. Wiring into the entry screen

- Find the hanzi field's `Input` widget in `tui/screens/entry.py` (M2 already
  reshuffled this screen — confirm the current widget id, likely `#hanzi`).
- On focus (`on_input_changed` won't fire on focus; use the widget's
  `Focus`/`Blur` events or `on_focus`/`on_blur` handlers, whichever Textual
  exposes on `Input` — check what M1's `PanelAwareInput` already overrides
  before adding another override on top of it): call `switch_to_pinyin()`.
- On blur: call `switch_to_english_international()`.
- Keep this wiring thin — the screen calls the two module functions and does
  nothing else input-method-specific. All platform/tool logic stays inside
  `input_method.py`.

## 3. Tests

- `tests/test_input_method.py`, runnable on any platform:
  - Non-Darwin: `switch_to_pinyin()` / `switch_to_english_international()` do
    nothing and raise nothing — patch `platform.system` to return e.g.
    `"Linux"` and assert `subprocess.run` is never called.
  - Darwin, `macism` present: patch `platform.system` to `"Darwin"` and mock
    `subprocess.run`; assert it's called once with the right source id for
    each function.
  - Darwin, `macism` missing: mock `subprocess.run` to raise
    `FileNotFoundError`; assert no exception propagates.
  - Darwin, source id rejected: mock `subprocess.run` to raise
    `subprocess.CalledProcessError`; assert no exception propagates.
- No new test infrastructure needed — this follows the existing pytest +
  `unittest.mock` conventions already used elsewhere in `tests/`.

## 4. Manual verification (programmer's machine only)

- Done. `macism` installed via `brew tap laishulu/homebrew; brew install
  macism`. Both source ids confirmed live (see `requirements.md`
  Decisions) — no Accessibility-permission prompt was needed on this
  machine, so that path remains untested.
- First hand-test through the actual entry screen found a bug: focusing the
  hanzi field switched the input source but then kept toggling it
  continuously, only stopping when `escape` moved focus off the field. Root
  cause and fix in §5. Re-tested after the fix — see §5's last bullet.

## 5. Bug: continuous switching while focused (found during hand-testing)

**Symptom.** Focusing the hanzi field switched to Pinyin Simplified as
intended, but the input source then kept flipping back and forth on its own
— observed as the system's input-source indicator changing repeatedly —
until `escape` defocused the field.

**Root cause.** `macism` switches the input source by simulating the OS's
own input-switching hotkey (this is also why it needs Accessibility
permission), and that simulated keypress makes the terminal application
briefly lose and then regain OS-level window focus. Textual's terminal
driver reports that round trip as an `AppBlur`/`AppFocus` pair
(`textual/_xterm_parser.py`, from the terminal's own xterm focus-reporting
escape codes), and `App._watch_app_focus`
(`textual/app.py`) responds to it by unfocusing and then refocusing
whatever widget currently has focus — in our case, `HanziInput` itself. That
unfocus/refocus was indistinguishable, from `HanziInput`'s original
`_on_focus`/`_on_blur` overrides, from a real user-driven focus change: blur
triggered `switch_to_english_international()`, which triggered its own
`AppBlur`/`AppFocus` round trip, which triggered `switch_to_pinyin()` again
— an unbounded loop. `escape` broke it only because it moves focus to
`FormPanel`, a widget with no such override, so the next app-refocus landed
somewhere inert.

**Fix.** Textual already distinguishes an app-level refocus from a genuine
one: `Focus.from_app_focus` is `True` only when the app itself regained OS
focus (not a real focus-in), and `App.app_focus` is already `False` by the
time a widget's `Blur` fires as a result of `AppBlur` (both set
synchronously in `App._watch_app_focus` before either event reaches the
widget). `HanziInput._on_focus` now skips the switch when
`event.from_app_focus` is true; `HanziInput._on_blur` now skips it when
`self.app.app_focus` is false. A real focus/blur (user tabbing into or out
of the field) leaves `app_focus` untouched throughout, so neither guard
affects it.

**Verified**, both automatically and by hand:
- `tests/test_tui_entry_screen.py::test_os_focus_roundtrip_does_not_reswitch_input_method`
  posts a real `AppBlur`/`AppFocus` pair at the running app while the hanzi
  field has focus and asserts neither switch function fires a second time.
- Re-tested manually: focusing the hanzi field switches once and holds
  steady; blurring switches back once; no more toggling loop.

## 6. Follow-up: stutter on focus/blur (found during the re-test)

`macism` takes 80-300ms per call (measured directly on the programmer's
machine) because it simulates a keypress rather than calling a silent API.
Run synchronously inside `_on_focus`/`_on_blur`, that blocked Textual's
entire event loop for the same span — felt as a stutter right when the
field gained or lost focus. Fixed by running both switches in a worker
thread via `self.app.run_worker(..., thread=True, group="input-method")` —
`self.app`, not `self`, so a blur-triggered switch still completes even if
the screen (and this widget) is torn down immediately after, mirroring
M3's `run_worker` ownership decision in this same file. Tests updated to
`await pilot.app.workers.wait_for_complete()` after triggering a
focus/blur change, since the switch call is no longer synchronous.
