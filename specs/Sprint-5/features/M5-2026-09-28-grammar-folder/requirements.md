# M5 · The grammar folder — format and entry — requirements

## Anchor (from the roadmap)

**Deliverable.** Grammar files are recognised as grammar by living under the
tree's top-level `Grammar/` folder. Subtitles become a third level in the file
format, below the category and above the triads (`models.py` gains whatever
holds them). The round trip `parse(write(deck)) == deck` still holds, including
a grammar file with no subtitles, a subtitle with no entries, and a category
mixing loose entries with subtitled ones; existing grammar files keep parsing
unchanged. Entry's right panel changes for a grammar file: a grammar target
also has a subtitle, and a subtitle can be created the way `(new category)` is.
It is reached through the same *Enter vocabulary* menu. Nothing about
vocabulary changes.

**Done when.** A grammar file with categories and subtitles round-trips through
`parser.py`/`writer.py` with no loss; the dev's existing `Grammar/*.md` files
still parse unchanged; opening a grammar file in Entry shows the grammar panel
and a vocabulary file shows the normal one; a subtitle can be created and
entries added under it from the app; compiling a grammar file still produces a
PDF (the old layout is fine — M6 is the new one); the dev confirms by hand; and
the full test suite passes.

Backlog source: [`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Grammar folder* — "The grammar folder will be special and managed
differently. Though it will still be managed through the enter vocabulary
menu. The visual difference is the right panel changes from the rest of the
folders." and "entries have subtitles (inferior to the category). For example,
inside the category "Conjunctions", some subtitles might be "copulative
conjunction", "disjuntive conjunction", etc." Everything about the PDF in that
section is M6.

## Decisions from the spec conversation (2026-09-28)

| Decision | Rationale |
| --- | --- |
| **The grammar marker is the folder:** a file is grammar iff its path relative to the notebook's tree root starts with a directory named `Grammar` (case-insensitive), at any depth below it | Dev's choice. The backlog states it as a folder, and the dev's tree already has `tree-Chinese/Grammar`. No per-file header, no config. |
| **A `Grammar/` folder nested deeper than the top level does not count** | Dev's choice. One rule, one place: `<tree root>/Grammar/`. |
| **A grammar file moved out of `Grammar/` becomes vocabulary again**; its `###` lines are treated as a vocabulary file treats them today (a parse warning, the line dropped, its entries staying in the category), so the subtitles flatten on its next save | Dev's choice, stated in the option they picked. Falls out of "nothing about vocabulary changes": a vocabulary parse is byte-for-byte today's. |
| **Subtitles appear in the form, not the tree.** The Entry tree is unchanged; for a grammar category, the right-hand form gains a **Subtitle** select field — `(none)`, the category's existing subtitles, `(new subtitle)` | Dev's choice. Matches the backlog's "the right panel changes from the rest of the folders" literally. |
| **`(new subtitle)` shows a subtitle-name field**, mirroring how `(new category)` shows a category-name field | Dev's choice (bundled with the above). |
| **Grammar entries keep the Note field** — hanzi, pinyin, translation, note, same as vocabulary | Dev's choice. How a note renders in a grammar PDF is M6's question. |
| **Subtitles are optional** inside a grammar category; a category may hold loose entries alongside subtitled ones | Dev's choice (*Minimal* scope). The dev's existing grammar files have none. |
| **Subtitles are exactly one level deep** — no `####` | Dev's choice (*Minimal* scope). |
| **Inspect Tree, Browse and the tag index do not change** | Dev's choice (*Minimal* scope). Tags and categories read identically either way. |
| **The PDF shows subtitles as plain headings** under their category until M6 | Dev's choice (*Minimal* scope); the roadmap already says the old layout is fine for M5. |

## Decisions taken while speccing (agent)

| Decision | Rationale |
| --- | --- |
| **`###` is the subtitle heading** | `##` is already the category heading, so `###` is the obvious next level down — the roadmap leaves it to the plan. |
| **In the model, a category's loose entries come first, then its subtitles, in file order.** `Category` gains `subtitles: list[Subtitle]`; `Subtitle` has `name` and `entries` | The file format forces this order: every entry after a `###` belongs to that subtitle until the next `###`/`##`, so a loose entry *after* a subtitle can't be written. Loose entries before the first subtitle are `Category.entries`, unchanged. |
| **`parse` takes a `grammar: bool = False` keyword**; only `grammar=True` recognises `###` | This is how "nothing about vocabulary changes" is enforced in code: with the flag off, the parser behaves exactly as it does today. Every caller that knows the path decides the flag with one helper, `store.is_grammar(path, tree_root)`. |
| **`###` before any category, or inside `## Tags`, is a parse warning** (the line is dropped), never an error | Same treatment as any other unrecognised line today. Subtitles only exist under a category. |
| **The writer needs no flag**: it writes whatever subtitles the deck has; a vocabulary deck never has any | Keeps the writer single-path. `parse(write(deck), grammar=True) == deck` is the round-trip property for grammar decks, and the existing property is unchanged for vocabulary. |
| **`render_markdown` emits `### <subtitle>` followed by that subtitle's table**, after the category's loose-entry table; an empty subtitle renders as a bare heading | Pandoc's `--shift-heading-level-by=-1` turns it into `\subsubsection`, unnumbered by the template's `secnumdepth` — a plain heading, as agreed. Vocabulary decks produce byte-identical intermediate markdown, so M2's stamp doesn't change and no vocabulary PDF recompiles. An empty subtitle as a bare heading matches how Sprint 4 M3 settled an empty category. |
| **`compile_file` gains `grammar: bool = False`**; `compile_all` decides it per file via `is_grammar`, and Entry / Inspect Tree pass it from their own `tree_root` | Every compile path has to parse `###`, or a grammar file compiled from the app would silently drop its subtitles. |
| **The Subtitle field only appears for a grammar file's named category.** `(uncategorized)` and `(new category)` in a grammar file look exactly like vocabulary | Subtitles live under a category. A new category starts empty; subtitles are added to it once it exists. |
| **Create with `(new subtitle)`:** a non-empty subtitle name creates the subtitle (or reuses an existing one of the same name in that category) and, if hanzi is filled, adds the entry under it. Hanzi empty → the subtitle is created empty. Subtitle name empty → no-op | Lets the dev create an empty subtitle the way `(new category)` creates an empty category, *and* lets the first entry go in the same keystroke. Reusing an existing name avoids two identical headings. |
| **After a Create, the Subtitle field stays on the chosen (or just-created) subtitle**; it resets to `(none)` only when the tree target changes | Entering several entries under one subtitle is the normal flow — it shouldn't need re-selecting after each one. |
| **A subtitle is created and saved by the same `save()` path as everything else**, and marks the file dirty for autocompile on leaving | Same as a new category today. |
| **`SelectField` gains `set_choices()` and a `Changed` message** | Its choices are fixed at construction today (Settings' input-method lists never change). Entry's subtitle list changes per category and after a create, and Entry has to show or hide the subtitle-name field when `(new subtitle)` is picked. |

## Decisions from dev feedback (2026-09-28, after hand-testing)

| Decision | Rationale |
| --- | --- |
| **Picking a Subtitle option auto-advances focus**: `(none)` or an existing subtitle moves focus to Hanzi; `(new subtitle)` moves focus to the subtitle-name field | Dev, after hand-testing on a real dummy `Grammar/` file: picking an option is a step forward in the form, same as `Tab` — leaving focus on the collapsed select made every add start with an extra manual `Tab`. Implemented on `SelectField.Changed`, which (per its own contract) only fires from a real user pick, not a value set in code, so this never fires from `_apply_target_state`'s own resets. |

## Context

- `parser.py` today: any line starting `## ` (other than `## Tags`) opens a
  category; a `### ...` line is an "unrecognized line" warning, and the
  entries after it stay in the current category. That is exactly the
  vocabulary behaviour kept under `grammar=False`.
- The dev's real grammar files (`~/Documents/Idiomas/tree-Chinese/Grammar/`):
  `Asking for directions.md` (loose entries and tags, no categories) and
  `Clasificadores.md` (five categories, one entry with a note, several empty
  categories). Neither has a `###`. Both must parse to the same `Deck` under
  `grammar=True` as they do today.
- `SelectField` (`panels.py`, Sprint 4 M6) is the app's standing select widget
  (list → field → panel → backpanel nesting, `enter` to deploy, `esc` to
  collapse). Reusing it keeps Entry within `design.md`'s navigation model with
  no new conventions.
- `Entry._visible_field_ids` currently assumes every field is an `Input`; the
  subtitle select is not, so the tab chain has to accept any focusable field.

## Out of scope (M6 or later)

- The grammar PDF layout: stacked triad, pinyin under each hanzi, spacing,
  subtitle heading style, note rendering — all M6.
- Showing grammar-ness or subtitles in Inspect Tree or Browse.
- Nested subtitles.
- Moving an existing entry between subtitles, renaming or deleting a subtitle
  from the app (the same is true of categories today; `nvim` via Inspect Tree
  covers it).
