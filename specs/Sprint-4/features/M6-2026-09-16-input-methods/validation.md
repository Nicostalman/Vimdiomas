# M6 · Input methods — validation

The acceptance bar for branch `2026-09-16-m6-input-methods`. Everything below
is checkable; the hand-tested rows are the dev's, and the milestone isn't done
until they say so.

## Automated

```sh
pytest
```

Passes with no failures, no skips that weren't already skipped, and no new
warnings. The suite must include, and pass:

| Area | Case |
| --- | --- |
| `tests/test_platform.py` | A keyboard layout maps to `com.apple.keylayout.<Name>` |
| | An `Input Mode` entry maps to its `Input Mode` value verbatim |
| | A `Keyboard Input Method` container is dropped when an `Input Mode` shares its `Bundle ID`, and kept when none does |
| | `Non Keyboard Input Method` entries never appear |
| | Duplicate IDs collapse; OS order is otherwise preserved |
| | `defaults` missing → `[]`, no exception |
| | Unparseable output → `[]`, no exception |
| `tests/test_config.py` | `input_method` round-trips through `save_config`/`load_config` |
| | A language entry with neither key loads both as `""` |
| | `hanzi_input_method` in a file is ignored, not read as a fallback |
| | `Config.language()` returns the entry, or `None` |
| `tests/test_tui_panels.py` | `enter` on a focused `SelectField` expands its list |
| | `enter` on an option sets the value and collapses |
| | `esc` on the open list collapses without changing the value, and does **not** reach the panel |
| | `esc` on the collapsed field focuses the panel |
| | Blurring an open field collapses it |
| `tests/test_tui_wizard.py` | One input-method step per chosen language, in order |
| | The written config carries both IDs for every language |
| | `q` from the first input-method step returns to tree location, root intact |
| | Folders are created on `Finish`, not before |
| | One available source → both fields preselect it, wizard still finishes |
| | Zero available sources → advisory shown, wizard still finishes, IDs stored as `""` |
| `tests/test_tui_settings.py` | Settings lists *Input methods* plus the two existing dummy items |
| | The language menu lists exactly the registered languages |
| | Fields open prefilled from the config |
| | `Save` writes both keys to disk and updates `app.config` in place |
| `tests/test_tui_entry_screen.py` | Focusing hanzi switches to the configured `input_method` |
| | Blurring switches to the configured `translation_input_method` |
| | A language with neither configured switches nothing |
| | The `from_app_focus` / `app_focus` round-trip guard still suppresses the reswitch |

## Verified against the real machine

Not automated — these are the roadmap's "the dev's real enabled input sources"
condition, and they touch the actual OS.

1. `python -c "from idiomas.platform import list_input_sources; print(list_input_sources())"`
   lists the machine's real sources and nothing else. On the dev's machine as of
   2026-09-18 that is exactly two: `com.apple.keylayout.USInternational-PC` and
   `com.apple.inputmethod.SCIM.ITABC`.
2. No option is cut off at the panel's width — checked by rendering the
   screen and reading its text back, since a truncation is easy to miss by
   eye.
3. `macism <id>` succeeds for every ID the listing returns — i.e. the listing
   never offers something the switcher can't accept. Check with `macism` (no
   arguments), which prints the current source.

## Hand-tested by the dev

| # | Check |
| --- | --- |
| 1 | With the config moved aside, `idiomas` opens the wizard; after tree location it asks for Chinese's input methods, with the machine's real sources in both lists |
| 2 | A field expands its list on `enter`, moves with `j`/`k`, chooses with `enter`, and collapses on `esc` leaving the previous choice untouched |
| 3 | Choosing German too gives a second input-method step, and `Finish` is on the last one only |
| 4 | `q` walks back through both steps and then to tree location, with every answer still filled in |
| 5 | The written `~/.config/idiomas/config.toml` has `input_method` and `translation_input_method` under each `[[languages]]` entry |
| 6 | Relaunching skips the wizard and lands on the configured Chinese notebook |
| 7 | In Entry, focusing the hanzi field switches the system input source to the chosen one; leaving it switches back to the chosen translation source — visible in the menu bar |
| 8 | Editing those two IDs in the config by hand and relaunching changes what Entry switches to, with no code edit |
| 9 | Settings → Input methods → Chinese opens prefilled; changing a choice and saving takes effect in Entry **in the same session**, without relaunching |
| 10 | Entry is otherwise unchanged — the same fields, the same keys, no stutter on focusing hanzi |

## Not required to pass

- Anything about German's notebook working. Its IDs are stored and unused.
- `macism` being installed. With it absent, every switch is a silent no-op and
  the wizard, Settings and Entry all still work — this is Sprint 2's guarantee
  and it must not have regressed.
- A pretty name for every possible input source. An unrecognised source shows
  its raw ID and is fully usable.

## Merge gate

`pytest` green, the two real-machine checks done, all ten hand-tested rows
confirmed by the dev, and `design.md` / `stack.md` updated per `plan.md` group 8
before the PR is opened.
