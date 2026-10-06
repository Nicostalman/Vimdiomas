# M3 · Search by content — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-7.md`](../../roadmap-sprint-7.md), *M3 · Search by
content*:

> **Deliverable.** A mode switch on Browse. In content mode, a query matches
> across every field of every entry and every category name in the notebook's
> tree, grammar files included. Each result says where it was found, and
> selecting it takes the user there. The mode convention is written into
> `design.md` once, since Browse is now the second screen with modes.
>
> **Done when.** In a Chinese notebook, searching by a hanzi, by its pinyin and
> by its translation each find the same entry. In the German notebook, the word
> and its translation each find theirs. A category name finds the category.
> Selecting a result does what the spec settled on. Filename mode behaves exactly
> as Browse does today. The dev confirms on their own trees, and the full test
> suite passes.

From the backlog's *Search for entries* (local-only, `guidelines/backlog.md`):
"Browse should have modes analogous to md and pdf modes. The first mode is
'search by filename', the default one just like pdf. The second mode is 'search
by content', and the user can search for category names and entries, in any
format (hanzi, pinyin, translation, or equivalent)."

This milestone narrows and widens the roadmap's text where the spec conversation
settled it (see *Decisions*). Where the two differ, **this file wins**:

- "Every field of every entry" means the **word, reading and translation**.
  **Notes are not searched** and tags stay a filter only.
- **Subtitle names** in grammar files are searchable, like category names.
- "Takes the user there" means **opening the file's PDF**, as filename mode
  does. It does not open the PDF at the entry's position.
- "Filename mode behaves exactly as Browse does today" covers **what it
  matches, how it ranks and what Enter does**. Browse's **layout and field
  navigation change in both modes** (§1). The dev chose that change.

## Decisions

Settled with the dev on 2026-10-03.

| Decision | Rationale |
| --- | --- |
| **`tab` toggles the mode**, on every screen with modes | Dev's choice. It is Inspect Tree's key already, so it becomes the convention rather than a second key. |
| **Browse splits into three stacked panels**: query, results, tag | Dev: "the correct way is pressing esc and then jk". `tab` no longer moves between fields, so the panel convention (`esc` up to the panel, `J`/`K`/shift+`↑`/`↓` to the next panel) does that instead. No new navigation rule is invented. The tag field sits **below** the results, not above them: dev's choice, made before M3 merged. |
| **`enter` in a text field moves to the next panel's content** | Dev: "pressing enter jumps to the next field just like tab does right now". Query field → results when there are any, otherwise the tag field. The tag field is the last panel, so `enter` there does nothing. |
| **One query field, shared by both modes; its text is kept across a toggle** | Dev's choice. Typing `你好` and then pressing `tab` searches the same text in the other mode. Only the placeholder changes. The tag field is shared too. |
| **A content result is one flat row**: an entry's fields, or a category or subtitle name alone, shown in bold, with its location after it | Dev's choice. No grouping, no note line. The bold name replaces an earlier `¶` marker: the dev saw the `¶` as a stray special character. |
| **Enter on a content result opens the file's PDF** | Dev's choice, the same action as filename mode. It compiles the file first if it has no PDF, exactly as Inspect Tree's PDF mode does. |
| **Matching is normalized substring**: case, accents and tones ignored, results in tree order | Dev's choice over fuzzy, which matches almost everything on a short query, and over ranked. |
| **Notes are not searched** | Dev's choice. |
| **The tag filter applies in content mode** | Dev's choice. It limits hits to files that carry the tag. |
| **Subtitles are searchable, like categories** | Dev's choice. |
| **An empty query shows a hint, not the whole tree** | Dev's choice. |
| **A row that does not fit is cut with `…`**. The location is cut last | Dev's choice. Every hit stays one line. Grammar rows can run past 100 characters. |
| **Parsed files are cached in memory for the life of the screen, keyed by mtime** | Dev's choice. It works like `tag_index`. The dev's trees hold about 50 rows today. **Persisting the tag cache stays postponed.** |

Decided by the agent, within what the dev settled. Flagged and confirmed by
the dev at spec review on 2026-10-03:

| Decision | Rationale |
| --- | --- |
| **The reading is shown with tone marks** in a result row (`nǐhǎo`, not `ni3hao3`) | That is how the PDF shows it. Matching does not depend on this. |
| **The mode badge reads `FILENAME MODE` (red) and `CONTENT MODE` (blue)** | Inspect Tree's badge is red for its default mode and blue for the other one. Browse follows the same pattern, and the pattern goes into `design.md`. |
| **Traditional and simplified hanzi are not converted** | `飲` does not find `饮`. Nobody asked for it, and conversion needs a dependency. |

## 1. Layout and navigation (both modes)

Browse becomes three stacked `Panel`s inside the backpanel, top to bottom:

1. **Query panel** (`#query-panel`): one `TextField`, `#query`. Its placeholder
   reads `Filter by filename` in filename mode and `Search entries and
   categories` in content mode. It replaces `#filename-filter`.
2. **Results panel** (`#results-panel`): the mode badge (`#mode-badge`) on
   top, then the results list (`#results`) or the empty-state message
   (`#empty-state`), then the footer hint (`#footer-hint`). It takes the
   remaining height. `#results` loses its own border: the panel's border is
   the frame, per *The focus look*.
3. **Tag panel** (`#tag-panel`): one `TextField`, `#tag-filter`, with the
   placeholder `Filter by tag`, at the bottom of the screen. Both modes use it.

The query and tag panels are each one row of content tall.

Keys. Everything not listed here follows `design.md`'s *Keys* table, so it
behaves as on Entry and Inspect Tree:

| Key | Where | Does |
| --- | --- | --- |
| `tab` | A text field or the results list | Toggles the mode. Focus stays where it is, except as in the next row |
| `tab` | The results list, when the new mode has no results | Toggles the mode and moves focus to `#query`, since the hidden list cannot keep focus |
| `tab` | A panel or the backpanel | Unchanged: focuses the content, per the *Keys* table (Inspect Tree behaves the same way) |
| `enter` | `#query` | Focuses `#results` if there are any results. Otherwise focuses `#tag-filter` |
| `enter` | `#tag-filter` | Does nothing: it is the last panel |
| `enter` | `#results` | Opens the highlighted result (§2, §3) |
| `esc` | Any content | Focuses its panel |
| `esc` | A panel | Focuses the backpanel. With three panels it is now **reachable**, which changes today's "esc twice does nothing" |
| `J`/`K`, shift+`↓`/`↑` | A panel or the backpanel | Moves between the three panels in their top-to-bottom order (query, results, tag), landing in their content |
| `q` | A text field | Types `q`, unchanged |
| `q` | The results list, a panel or the backpanel | Leaves Browse, unchanged |

On opening, Browse is in filename mode with `#query` focused, as today.

The footer hint has one text for each mode:
- Filename mode: `Tab: search by content · Enter: next field / open PDF · Esc then J/K: move between panels`
- Content mode: `Tab: search by filename · Enter: next field / open PDF · Esc then J/K: move between panels`

The mode is screen-local and is reset to filename mode every time Browse is
opened, like Inspect Tree's.

## 2. Filename mode

What it lists, how it filters and ranks, and what Enter does are **unchanged**:
`list_pdfs`, `fuzzy` on the query, `paths_with_tag` on the tag, `No matches.`
when nothing is left, the first result highlighted, and Enter opening the PDF
with `open_pdf`. Only the field it reads is renamed (`#query`).

## 3. Content mode

### 3.1 What is searched

Every `.md` file under the tree root, vocabulary and grammar, parsed with
`parse(..., kind=, grammar=is_grammar(path, tree_root))`. In each file:

- every **category** name,
- every **subtitle** name (grammar files),
- every **entry**: uncategorized, directly under a category, and under a
  subtitle. Its **word**, its **reading** (Chinese kind only) and its
  **translation** are searched. Its note, its extra fields and the file's tags
  are not.

A file that cannot be read or decoded contributes nothing and raises nothing,
the same rule `store._parse_file` follows. No notification is shown: Inspect
Tree already reports the problem.

### 3.2 Matching

The query is stripped of leading and trailing whitespace. An empty query shows
the hint `Type to search entries and categories.` in `#empty-state`, and no
list.

Two normal forms, both in `store.py`, both pure functions:

- **`fold(text)`**: NFKD, drop combining marks (Unicode category `Mn`),
  `casefold()`, then NFC. `Über` → `uber`, `nǐ` → `ni`, `Straße` → `strasse`,
  `ESSEN` → `essen`. Hanzi and spaces pass through unchanged.
- **`pinyin_key(text)`**: `fold(text)` with ASCII digits, whitespace, `:`, `'`
  and `’` removed and `v` replaced by `u`. `ni3hao3` → `nihao`, `nǐ hǎo` →
  `nihao`, `lu:4` → `lu`, `lv4` → `lu`, `Xi'an` → `xian`.

A field matches when:

| Field | Matches when |
| --- | --- |
| word, translation, category name, subtitle name | `fold(query)` is a substring of `fold(field)` |
| reading | `pinyin_key(query)` is not empty and is a substring of `pinyin_key(reading)` |

An entry is a hit when any of its three fields matches. It appears once, even
when several fields match.

Consequences the tests pin down (see `validation.md` §2):
- `番` finds `番茄`. `你好` finds `你好嗎？…`.
- `ni`, `ni3`, `nǐ`, `NI`, `nihao`, `ni hao`, `ni3hao3` and `nǐhǎo` all find the
  reading `ni3hao3`. Tones are ignored both ways: `ni3` also finds `ni2`.
- `uber` and `über` both find `Über`. `uber` finds `über` in a translation.
- `3` finds no reading (its `pinyin_key` is empty). It can still find a word or
  translation that contains a `3`.
- `cafe` finds `café` and `Cafe`.

### 3.3 The tag filter

When `#tag-filter` is not empty, hits are limited to files that `tag_index`
reports as carrying that tag, using the same exact-tag rule filename mode uses.
A file with no compiled PDF is **not** excluded: content mode searches sources,
not PDFs. (Filename mode excludes it only because it lists PDFs.) A tag on its
own lists nothing: with an empty query the hint shows, whatever the tag field
holds.

### 3.4 Order

Results come in tree order. Files are ordered the way `store.walk` orders them
(names sorted at each level, so `Grammar/` comes before `Vocabulary/`). Within a
file, hits follow the document: uncategorized entries first, then for each
category its own row (if it matches), its direct entries, then for each
subtitle its row (if it matches) and its entries. There is no ranking and no
cap. The list scrolls.

### 3.5 A result row

One line per hit, built as plain text: no markup, so brackets show as typed,
per *Text from the tree is shown as typed*.

- **Entry, Chinese kind**: `word  reading  translation`, with the reading
  converted by `pinyin.to_tone_marks`.
- **Entry, alphabetical kind**: `word  translation`.
- **Category**: the name alone, in bold.
- **Subtitle**: the name alone, in bold.

Bold is what tells a category or subtitle row from an entry. No marker
character is added in front of it.

The **location** follows, dim, separated by at least two spaces and aligned
right. It is the file's path relative to the tree root without `.md`, then
` › ` and the category, then ` › ` and the subtitle, as far as they apply:

- an uncategorized entry: `Vocabulary/Repaso clase 2`
- an entry or subtitle row under a category: `… › Saludos`
- a category row: just the file
- a subtitle row: the file and its category
- an entry under a subtitle: the file, its category and its subtitle

Empty fields are skipped, along with their separator. An entry with no
translation shows `word  reading`.

**Fitting the row** to the list's content width `W`, measured in terminal cells
(`rich.cells.cell_len`, so a hanzi counts as 2):

1. If the whole row fits, it is shown whole.
2. Otherwise the fields are cut first. Each is cut to its share of the space
   left after the location, with a trailing `…`. Space is shared out by
   repeatedly capping the longest field, so short fields stay whole. No field
   goes below 1 cell plus `…`.
3. If it still doesn't fit with every field at that minimum, the location is
   cut from the left with a leading `…`, so the deepest part (the category)
   stays visible.

`format_row(fields, location, width) -> Text` is a pure function. Its result
never exceeds `width` cells when `width >= 8`. Rows are rebuilt when the list
is resized.

### 3.6 Selecting a result

`enter` on any content row (entry, category or subtitle) opens its file's PDF,
`compile.notebook_path_for(source)`. If that PDF does not exist, the file is
compiled first and then opened. A compile failure shows the same error
notification Inspect Tree shows and opens nothing. This is Inspect Tree's
`_open_pdf`, moved to one shared function that both screens call, so the two
cannot drift apart.

### 3.7 The cache

`store.ContentIndex` holds `path → (mtime, Deck)`. On every refresh, each `.md`
under the tree root is `stat`ed and re-parsed only if its mtime changed. Files
that are gone are dropped. One instance lives on the `BrowseScreen`, so leaving
Browse discards it. Nothing is written to disk.

## 4. `design.md`

Updated in place, once:

- **A new section, *Screen modes***: a screen with modes switches between them
  with `tab` from its content. The first mode is the default, and the mode is
  reset every time the screen opens. A badge shows the mode, red for the
  default and blue for the other. The footer hint names what `tab` switches to.
  Inspect Tree (PDF/MD) and Browse (filename/content) are the two screens with
  modes.
- **The *Keys* table's `tab` row**: "Screen-specific" now lists Entry (next
  field) and screens with modes (toggle the mode).
- **Backpanel reachability and *Flat menus***: Browse now has three panels, so
  `esc` reaches its backpanel and `J`/`K` move between its panels. Today's text
  says Browse has one panel.
- **A Browse paragraph** covering the layout (§1), `enter` moving to the next
  field, and content mode's results (§3.5–§3.6).

## Out of scope

- Opening the PDF at the entry's page or position, or opening the source in
  `nvim` at the entry's line.
- Searching notes, tags or extra columns.
- Fuzzy or ranked content matching.
- Traditional ↔ simplified conversion.
- Persisting any cache to disk (still in *Postponed*).
- Any change to Inspect Tree beyond moving `_open_pdf` into the shared
  function.
