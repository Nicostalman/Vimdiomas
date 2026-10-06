# M3 · Search by content — validation

The acceptance bar for the branch. Section numbers (§) refer to
[`requirements.md`](requirements.md). Checks marked **auto** are tests in the
suite. The rest are run once and reported.

## 1. The suite (auto)

- [x] `pytest` passes in full. Integration tests run where pandoc and xelatex
      exist.
- [x] Every pre-existing filename-mode Browse test passes after only the
      `#filename-filter` → `#query` rename, except the two §4 of `plan.md`
      replaces on purpose.
- [x] Inspect Tree's tests pass, with the same assertions, after `_open_pdf`
      moves (§3.6) — only two tests' monkeypatch target moves from
      `idiomas.tui.screens.inspect` to `idiomas.tui.screens.base`.

## 2. Matching (auto, unit)

`fold`:

| Input | Output |
| --- | --- |
| `Über` | `uber` |
| `Straße` | `strasse` |
| `nǐ hǎo` | `ni hao` |
| `ESSEN` | `essen` |
| `café` | `cafe` |
| `番茄` | `番茄` |
| `[b]x` | `[b]x` |

`pinyin_key`:

| Input | Output |
| --- | --- |
| `ni3hao3` | `nihao` |
| `nǐ hǎo` | `nihao` |
| `NI3` | `ni` |
| `lu:4` | `lu` |
| `lv4` | `lu` |
| `Xi'an` | `xian` |
| `3` | `` (empty) |

`search_content` over a fixture tree holding a Chinese vocabulary file (one
uncategorized entry, a category `Saludos` with `你好	ni3hao3	hola` and
`番茄	fan1qie2	tomate`), a Chinese grammar file (category, subtitle
`copulative conjunction`, an entry under it), and a German tree (`Über	about`,
category `Essen`):

| Query | Hits |
| --- | --- |
| `你好` | the `你好` entry only |
| `番` | `番茄` |
| `ni`, `ni3`, `nǐ`, `NI`, `nihao`, `ni hao`, `nǐhǎo` | the `你好` entry (plus any other `ni` reading in the fixture, in tree order) |
| `hola` | the `你好` entry |
| `salu` | the `Saludos` category row |
| `copulative` | the subtitle row |
| `3` | no reading hits |
| a word in an entry's **note** only | nothing |
| a **tag** only | nothing |
| German `uber`, `über`, `about` | the `Über` entry |
| German `essen` | the `Essen` category row |
| `   ` (spaces only) | the empty-query state, not a search |

- [x] An entry matching on word and translation at once appears once.
- [x] Hits come in §3.4's order: across files, and within a grammar file
      (category row, direct entries, subtitle row, its entries).
- [x] With `tagged`, only files carrying the tag contribute, uncompiled ones
      included.
- [x] `ContentIndex` re-parses only a file whose mtime changed, drops a deleted
      file, and skips an unreadable one without raising.

## 3. Navigation (auto, Textual pilot)

- [x] Opening Browse: filename mode, `#query` focused, badge `FILENAME MODE`,
      filename footer hint.
- [x] The panels stack top to bottom as query, results, then tag (the tag field
      is last).
- [x] `tab` from `#query`, `#tag-filter` and `#results` toggles the mode and
      keeps focus. The badge, the placeholder and the footer hint follow.
- [x] `tab` from `#results` into a mode with no results focuses `#query`.
- [x] `tab` on a focused panel focuses its content (no toggle).
- [x] `enter` in `#query` focuses `#results` when it has results, and
      `#tag-filter` when not. `enter` in `#tag-filter` does nothing (it is
      the last panel).
- [x] `esc` from a field focuses its panel. `esc` again focuses the backpanel.
- [x] `J`/`K` and shift+`↓`/`↑` from a panel move between the three panels in
      order (query, results, tag) and land in their content. Capital `J`/`K`/`L` typed in a field type.
- [x] `q` in a field types `q`. `q` in the results leaves Browse.
- [x] Re-opening Browse starts in filename mode again.
- [x] Filename mode: the filter, ranking, tag filter, empty state, first-row
      highlight and Enter → `open_pdf` all behave as before (the existing tests).

## 4. Content mode (auto, Textual pilot)

- [x] Empty query: `Type to search entries and categories.` and no list, with
      or without a tag.
- [x] A Chinese tree: `你好`, `nihao` and `hola` each list the same entry row,
      showing `你好  nǐhǎo  hola` and its location `Vocabulary/<file> › Saludos`.
- [x] A German tree: `Über` and `about` each list the `Über` entry, with no
      reading column.
- [x] A category query lists `Saludos` in bold with the file as its location.
      A subtitle query lists `copulative conjunction` in bold with file ›
      category.
- [x] A query matching nothing shows `No matches.`
- [x] Text typed in filename mode is still in `#query` after `tab`, and
      content mode searches it at once.
- [x] The tag filter limits content hits to tagged files.
- [x] `enter` on an entry row, on a category row, and on a row from a file
      with no PDF calls the opener with the right `.pdf` path. For the
      uncompiled file, the compile is called first. A compile failure notifies
      with severity `error` and opens nothing.
- [x] A row with brackets (`[b]x`) shows them literally.
- [x] `format_row`: the cases in `plan.md` §2, and its width never exceeds
      `W` for `W` from 8 to 120.

## 5. On the dev's trees (manual)

Run by the agent with the app pointed at `~/Documents/Idiomas` and reported,
then confirmed by the dev:

- [x] Chinese: a hanzi, its pinyin (with and without tones) and its
      translation each find the same entry (e.g. `你好` / `nihao` / `hola`).
- [x] German: a word and its translation each find their entry.
- [x] A category name finds its category, and a subtitle in
      `Grammar/Conjunctions` finds its subtitle.
- [x] The long `Presentación individual` row is cut to one line with `…`, and
      its location stays readable.
- [x] Enter on a result opens that file's PDF.
- [x] Filename mode looks and works as before, apart from the three panels.
- [ ] **The dev confirms by hand**, on their own trees.
