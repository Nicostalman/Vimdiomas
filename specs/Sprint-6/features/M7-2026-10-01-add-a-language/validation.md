# M7 · Add a language — validation

The acceptance bar for merging `2026-10-01-m7-add-a-language`. It is the
roadmap's done-when, made checkable.

## Automated

- [ ] `pytest` passes in full, including the real-pandoc tier.
- [ ] **Registry:** `LANGUAGES` is Chinese, German, Italian, French, English,
      Spanish, with Chinese `CHARACTER_PHONETIC` and the rest `ALPHABETICAL`,
      all functional. No language's hints match another's source IDs.
- [ ] **No per-language code:** no executable string in `src/` outside
      `languages.py` and the platform display-name tables names Italian,
      French, English or Spanish (`test_languages.py` checks it on the AST; a
      plain `grep` also finds one historical docstring in `input_method.py`).
- [ ] **doctor:** a German-only `missing_for` ignores a missing xeCJK and
      font; a Chinese one returns them; a missing `pandoc` is returned for
      any language set. `idiomas doctor` exits 0 for a German-only config
      without xeCJK.
- [ ] **Wizard:** step 3 shows six checkboxes in registry order, *Next*
      still inside an 80×24 screen; step 1 never
      blocks on the CJK pair; German-only proceeds with xeCJK missing;
      Chinese with xeCJK missing shows the install offer, and declining
      refuses with the command shown.
- [ ] **Install offer:** no command means refusal without a dialog; accepting
      runs exactly the platform commands without a shell and proceeds only
      when the recheck is clean; an `OSError` is reported, not raised.
- [ ] **Settings › Add a language:** the picker lists only unregistered
      languages; with all six registered the placeholder says "Every
      supported language is already added."; adding Italian creates
      `tree-Italian/Vocabulary` and `tree-Italian/Grammar`, appends it to the
      saved and the running config, returns to Settings with "Italian added.",
      and an existing `tree-Italian` is adopted with its files untouched; a
      failed save leaves `app.config` unchanged.
- [ ] **Without relaunching:** after the add, the landing menu lists
      *Italian notebook* last before *Settings*, opening it pushes the
      notebook menu, and Input methods lists Italian.
- [ ] **On arrival:** for each of Italian, French, English, Spanish, a word
      added through Entry parses back, and a vocabulary and a grammar deck
      compile with real pandoc.
- [ ] Every new menu option is a `MenuOption` whose description fits the
      legend's two lines (the existing legend test covers every menu).

## By hand (the dev)

- [ ] In the running app, Settings › *Add a language* lists the four
      languages you don't have. Add one (e.g. Italian), answering the
      input-method question, and land back in Settings with "Italian added."
- [ ] Without relaunching, the landing menu shows *Italian notebook*. Open it,
      enter a word with accents through Entry, and compile. The PDF looks
      like German's.
- [ ] Settings › Input methods lists the new language.
- [ ] `idiomas wizard` (the dev escape hatch) offers all six at step 3. Back
      out with `q` before *Finish*, so your real config is not overwritten.
- [ ] Optional, if you want to see the install offer: on the Linux OrbStack
      container from Sprint 5 M7, without `texlive-lang-chinese`, add Chinese
      and accept the offer.
