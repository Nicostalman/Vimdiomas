# M8 · Remove a language — validation

The acceptance bar for merging `2026-10-01-m8-remove-a-language`. It is the
roadmap's done-when, made checkable.

## Automated

- [ ] `pytest` passes in full.
- [ ] **Settings:** the options read *Input methods*, *Add a language*,
      *Remove a language*, each with a description that fits the legend (the
      existing legend test covers every menu).
- [ ] **Picker:** it lists the registered languages in config order. With
      none, the placeholder says "There is no language to remove."
- [ ] **Two separate confirmations:** `n`/`esc` on the first changes nothing.
      `y` then `n`/`esc` removes the language and keeps every file under
      `tree-<Language>/`, PDFs included. Only `y` then `y` deletes the folder.
      `enter` confirms neither dialog.
- [ ] **Persistence:** after a removal, both `load_config()` and
      `app.config` no longer hold the language. A failed save leaves both,
      and the folder, unchanged.
- [ ] **Cache:** a kept folder keeps its cache entries. A deleted folder's
      entries are purged, and other languages' are untouched.
- [ ] **Without relaunching:** the landing menu and the Input methods picker
      drop the language on return.
- [ ] **Zero languages:** the landing menu shows only *Settings*, with "Add a
      language to start a notebook." Both pickers show their placeholders.
      `idiomas compile` and `idiomas doctor` exit 0.
- [ ] **Re-add:** remove (keep) → add the same language restores its notes
      untouched, and its notebook menu opens.

## By hand (the dev)

Do this on a language you can afford to lose, or on a copy of your tree.
Adding Italian through M7 first is the easy way.

- [ ] Settings › *Remove a language* lists your languages. Choose Italian,
      press `y`, then `n` at the folder question. You land on Settings with
      "Italian removed. Its notes are still in …".
- [ ] Without relaunching, the landing menu has no *Italian notebook*, and
      Input methods doesn't list it. `tree-Italian/` is still on disk with its
      files and PDFs.
- [ ] *Add a language* › Italian: the keyboard question is asked again, and
      once added, the Italian notebook has its old notes.
- [ ] Remove Italian again, this time `y` at the folder question:
      `tree-Italian/` is gone.
- [ ] Optional: remove every language on a throwaway config. The landing menu
      shows only *Settings*, and adding one brings it back.
