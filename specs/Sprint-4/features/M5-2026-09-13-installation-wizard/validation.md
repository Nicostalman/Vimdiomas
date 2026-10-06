# M5 · Installation wizard — validation

Grounded in the roadmap's own done-when condition.

## Automated

Run from the repo root:

```sh
pytest
```

All of the following must pass, in particular:

- `tests/test_config.py` — `save_config()` round-trips through
  `load_config()`; creates `~/.config/idiomas/` (patched via `tmp_path`) if
  missing; writes atomically (no partial file left if interrupted, verified
  via the temp-file-then-`os.replace` sequence); `validate_tree_root()`
  rejects a path inside the installed package and an unwritable path, and
  accepts a normal writable path.
- `tests/test_tui_wizard.py` (new) — every case in `plan.md`'s Task Group 7:
  dependency blocking and recheck (including the inline-spinner
  transition), the `missing`/`url` display replacing the raw message,
  name/language minimum-selection refusal, tree-folder creation
  (including German's), back navigation via `q`, the confirm dialog on
  step-1 abort, and the full happy path producing a config file that
  `load_config()` reads back identically.
- `tests/test_doctor.py` — `Check.url` present on every check but Heiti
  SC; pandoc's points at its GitHub repo.
- `tests/test_tui_panels.py` — the new `MenuScreen` `tab`-no-op regression
  test passes; no existing test regresses: `test_tui_landing_menu.py`,
  `test_tui_main_menu.py` unchanged in behaviour.

## Manual — the dev's own machine

This milestone's real acceptance bar, per the roadmap ("the dev runs it
fresh against their real tree and lands on a working Chinese notebook").

**For a quick look at the wizard's screens** without touching the real
config at all, run:

```sh
idiomas wizard
```

It opens the wizard even with a config already in place. Back out with
`q` before `Finish` to leave the real config untouched (finishing still
overwrites it, same as the real flow). This is a dev-only escape hatch —
it never appears in `idiomas --help` and isn't part of the CLI's
documented surface.

**For the real acceptance pass** (the one that has to happen at least
once, since it's what "runs it fresh against their real tree" means):

1. **Move the config out of the way**, so the wizard has something to run
   against: `mv ~/.config/idiomas/config.toml ~/.config/idiomas/config.toml.bak`.
2. **Launch `idiomas`** (as the installed command, or `python -m idiomas`
   if not yet on `PATH` in this environment). The wizard opens on the
   Dependencies step, not the landing menu.
3. **Dependencies.** Confirm the "Dependencies" title and its prompt line
   are visible above the check list, and the list matches `idiomas
   doctor`'s output (required: pandoc, xelatex, xeCJK, Heiti SC; optional:
   macism, nvim), with every status **aligned in one column** and colored
   green (`ok`). Click `Recheck` (or tab to it and press enter/space):
   confirm a small spinner animates **inline, next to each dependency's
   own name** — not one big indicator replacing the whole list — before
   settling back to the (re-)checked results; this should read as a
   deliberate touch, not a flash. Then temporarily rename a required
   tool's binary (e.g. `mv $(which pandoc) $(which pandoc).bak`) and
   `Recheck` again: confirm that check now shows red `missing <-- ` and a
   link (its GitHub repo for pandoc/xelatex/xeCJK/macism/nvim; Heiti SC
   has none, since it's bundled with macOS) — the **full line must be
   visible**, wrapping onto a second line rather than being cut off —
   and `Next` is blocked. Restore the tool (`mv $(which pandoc).bak
   $(which pandoc)`) and `Recheck` once more to confirm it unblocks
   without restarting the wizard. Then press `q`: confirm a "Quit the
   installation wizard?" dialog appears rather than the app closing
   immediately; `n`/`escape` cancels back to this screen unchanged, `y`
   exits the wizard.
4. **User name.** Confirm the "Your name" title/prompt are visible, an
   empty/whitespace submission is refused, then enter a real name and
   proceed.
5. **Languages.** Confirm the "Languages" title/prompt are visible, both
   checkboxes render at the same width regardless of "Chinese"/"German"'s
   length, and `space` on a focused checkbox does nothing while `enter`
   toggles it. Confirm proceeding with nothing checked is refused. Check
   both Chinese and German, proceed.
6. **Tree location.** Confirm the "Tree location" title/prompt are
   visible and the field is pre-filled with `~/Documents/Idiomas`. Point
   it at the dev's **actual existing** tree parent directory (the one
   holding the real `tree-Chinese/`) instead of the default, and finish.
7. **Confirm on disk:**
   - `~/.config/idiomas/config.toml` now exists with the dev's real name,
     root, and both languages.
   - The existing `tree-Chinese/` directory's contents are **untouched**
     (no files added, removed, or altered).
   - A new empty `tree-German/` directory now exists alongside it.
8. **Confirm the handoff.** The app continues straight into the landing
   menu (same process, no relaunch) showing both Chinese and German;
   opening Chinese reaches a working notebook against the dev's real
   entries; German stays inert per this sprint's scope. **On the landing
   menu, press `tab`**: confirm the option list stays focused (highlighted
   row visible) rather than the highlight disappearing — this is the
   app-wide `MenuScreen` fix from Task Group 6, not specific to the
   wizard, so also worth a quick check on the main menu once inside a
   language.
9. **Confirm the wizard doesn't run again.** Quit and relaunch `idiomas` —
   it goes straight to the landing menu, config already in place.
   **Every screen's backpanel border** (the outermost box) should be the
   same accent/orange color whether or not anything on the screen
   currently has focus — Task Group 6's other app-wide fix.
10. **Confirm abort-writes-nothing.** Move the config aside again, launch
    `idiomas`, and quit (`q`) from the Dependencies step before finishing
    anything. Confirm no `config.toml` was written. Relaunch and confirm
    the wizard starts over from Dependencies with no memory of the aborted
    attempt.
11. **Restore**, if step 1's backup is still needed:
    `mv ~/.config/idiomas/config.toml.bak ~/.config/idiomas/config.toml`
    (only if the dev doesn't want to keep the freshly-wizard-written one).

## Done-when checklist

- [ ] With no config, launching `idiomas` opens the wizard.
- [ ] A missing required dependency stops the wizard from continuing.
- [ ] A missing optional dependency only warns and allows continuing.
- [ ] Finishing the wizard writes a config that `IdiomasApp` runs from
      immediately, in the same process.
- [ ] Relaunching `idiomas` after finishing skips the wizard.
- [ ] The dev has run the wizard fresh against their real tree and reached
      a working Chinese notebook, with the existing tree untouched.
- [ ] The full test suite passes.
