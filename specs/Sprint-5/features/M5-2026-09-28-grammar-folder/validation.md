# M5 · The grammar folder — format and entry — validation

Grounded in the roadmap's done-when condition, made concrete.

## Automated

- `pytest` — full suite passes, including every new test in `plan.md`
  groups 1–5, and every pre-existing test unmodified.
- Specifically covered:
  - `is_grammar`: top-level `Grammar/` (any case, any depth below) is grammar;
    `Vocabulary/Grammar/`, a root-level `Grammar.md`, and paths outside the
    tree are not.
  - A grammar fixture with loose entries, subtitles, a noted entry, an empty
    subtitle, a subtitle-less category and tags round-trips:
    `parse(write(deck), grammar=True) == deck` and the text is byte-identical.
  - The same fixture under `grammar=False` behaves as today (`###` lines are
    warnings, entries flattened into their category).
  - Copies of the dev's `Asking for directions.md` and `Clasificadores.md`
    parse to identical decks with the flag on and off, with no new warnings.
  - `render_markdown` for a vocabulary deck contains no `###` and is
    unchanged; for a grammar deck it has each subtitle as a `###` heading.
  - A grammar file with subtitles compiles to a PDF (integration test, real
    pandoc/xelatex).
  - Entry: subtitle field present only on a grammar file's named category;
    entries land in `(none)` / an existing subtitle / a new subtitle as chosen;
    an empty new subtitle is creatable; an unnamed one is a no-op.

## Manual, by the dev

Against the real tree (`~/Documents/Idiomas/tree-Chinese`).

- [ ] Main menu → *Enter vocabulary*. Highlight a category in a file under
      `Vocabulary/`: the form is exactly as before — no Subtitle field.
- [ ] Highlight a category in `Grammar/Clasificadores.md`: the form shows a
      **Subtitle** field reading `(none)` above Hanzi.
- [ ] Highlight `(uncategorized)` or `(new category)` in a grammar file: no
      Subtitle field.
- [ ] On a grammar category, open the Subtitle field (`enter`), pick
      `(new subtitle)`: a subtitle-name field appears **and focus lands on
      it automatically**. Type a name, fill hanzi and translation, Create.
      The entry is added and the Subtitle field now shows the new subtitle.
- [ ] Open the Subtitle field and pick `(none)` or an existing subtitle:
      focus lands on Hanzi automatically, no extra `Tab` needed.
- [ ] Add a second entry straight away: it goes under the same subtitle
      without re-selecting it.
- [ ] Pick `(new subtitle)`, type a name, leave hanzi empty, Create: an empty
      subtitle is created and appears in the Subtitle list.
- [ ] Pick `(none)` and add an entry: it goes into the category directly,
      above the subtitles.
- [ ] `tab` cycles through Subtitle (and the name field when shown) along
      with the other fields; `esc`/shift+hjkl behave as before.
- [ ] Open the file in Inspect Tree (MD mode, `enter` → nvim): the file shows
      `### <subtitle>` headings with their entries beneath, and the rest of the
      file is unchanged.
- [ ] Leave Entry: the grammar file autocompiles; its PDF shows the subtitles
      as headings under their category (old table layout — M6 restyles it).
- [ ] *Compile all*: only the edited grammar file rebuilds; vocabulary PDFs
      are not rebuilt.

## Merge bar

All automated checks pass, and the dev confirms the manual list.
