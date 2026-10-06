# M5 · Language kinds — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-6.md`](../../roadmap-sprint-6.md), *M5 · Language
kinds*:

> **Deliverable.**
>
> - **A language kind is a first-class thing**: a small module describing, per
>   kind, how many word fields an entry has and what they are called, whether a
>   phonetic field exists and whether it is auto-filled, and which font the
>   renderer uses.
> - **Chinese is expressed in it and nothing else changes.** The existing
>   behaviour (hanzi with pinyin guessed from it, the three-column vocabulary
>   table, the stacked grammar triads, Songti SC) is reproduced exactly,
>   verified against the dev's real tree by compiling it before and after and
>   diffing.
> - **Every hardcoded Chinese assumption is routed through it**, including
>   `config.FUNCTIONAL_LANGUAGES`, the wizard's `LANGUAGE_CHOICES`, Entry's
>   pinyin auto-fill, and `compile.py`'s per-language font, so that M6 adds a
>   language rather than editing ten call sites.
> - **The parser and writer stay compatible with every existing file.** The
>   storage format does not change in this milestone.
>
> **Done when.** Chinese behaves exactly as before by hand and by test; the
> dev's real tree compiles to byte-identical PDFs across the refactor; adding a
> language of an existing kind is demonstrably a table entry rather than a code
> change; and the full test suite passes.

Source: [`backlog.md`](../../guidelines/backlog.md)'s *Implement german* ("no
equivalent to hanzi, so the text field should not appear"; "recycle elements
from chinese and not repeat code … new classes only if they add more
functionality than complexity") and *Implement add a language* ("All languages
that will be supported fall under the german category (alphabetical only) or
chinese category (character and phonetic)").

## Settled with the dev (2026-10-01)

These are the four open questions the roadmap left for this conversation. The
dev took the recommended option on each.

| Question | Decision |
| --- | --- |
| **`models.Entry`'s field names** | **Renamed to neutral names: `word`, `reading`, `translation`** (plus `note` and `extra_fields`, which keep their names). For Chinese, `word` is the hanzi and `reading` the numbered pinyin. For an alphabetical language, `word` is the word and `reading` is always `""`. "Hanzi" and "Pinyin" survive only as the labels the Chinese kind gives those fields in the UI. This is a code rename only: the on-disk row is still `word<TAB>reading<TAB>translation`, byte for byte. |
| **Whether a kind is data or a class** | **Data.** One frozen dataclass, `LanguageKind`, with exactly two instances: `CHARACTER_PHONETIC` and `ALPHABETICAL`. There is no subclass per kind. Code that differs by kind branches on the kind's fields (`has_reading` above all), following the backlog's "classes only if they add more functionality than complexity". |
| **Where a language's kind comes from** | **A built-in table in code** that maps a language name to its kind. `config.toml` doesn't change: no `kind` key and no migration. M7 extends the same table from two entries to six. |
| **Whether "functional" survives** | **As a flag on each table entry.** `config.FUNCTIONAL_LANGUAGES` is deleted. Each registered language has `functional: bool`: Chinese is `True`, and German is `False` until M6 flips it. |

## Scope

### 1. The `languages` module

A new module, `src/idiomas/languages.py`, is the one place a language's
behaviour is described.

**`LanguageKind`** is a frozen dataclass with these fields:

| Field | Meaning | `CHARACTER_PHONETIC` | `ALPHABETICAL` |
| --- | --- | --- | --- |
| `name` | A human-readable name for the kind, used in docs and error messages | `"character and phonetic"` | `"alphabetical"` |
| `word_label` | The placeholder of Entry's word field | `"Hanzi"` | `"Word"` |
| `reading_label` | The placeholder of Entry's reading field, or `None` when the kind has no reading | `"Pinyin"` | `None` |
| `guess_reading` | The function that fills the reading from the word as the user types, or `None` | `pinyin.guess` | `None` |
| `cjk_font` | The CJK face the template sets, or `None` | `platform.CJK_FONT_NAME` | `None` (provisional; M6 chooses German's typography) |

It also has one derived property, `has_reading`, which is `reading_label is
not None`. If `guess_reading` is set, the reading field is read-only and
auto-filled, as pinyin is today.

**`Language`** is a frozen dataclass with these fields:

| Field | Meaning |
| --- | --- |
| `name` | The name stored in the config and shown on the landing menu, e.g. `"Chinese"` |
| `kind` | One of the two `LanguageKind`s |
| `input_hints` | The substrings that mark an input source as this language's (moved from `input_methods.LANGUAGE_HINTS`) |
| `functional` | Whether the notebook opens. `False` shows the placeholder, as today |

**`LANGUAGES`** is the registry: a tuple of `Language`, in the order the
wizard offers them.

```python
LANGUAGES = (
    Language("Chinese", CHARACTER_PHONETIC,
             input_hints=("SCIM", "TCIM", "Pinyin", "Zhuyin", "Cangjie", "Wubi", "Shuangpin")),
    Language("German", ALPHABETICAL, input_hints=("German",), functional=False),
)
```

**`get_language(name) -> Language | None`** returns the registry entry for a
name, or `None` for a name that isn't in the registry. A config edited by hand
can hold such a name. It is treated exactly as a non-functional language is
today: it is listed on the landing menu, "Not available yet.", and opens the
placeholder. It is never an exception.

**`is_functional(name) -> bool`** is a convenience for the three places that
read `FUNCTIONAL_LANGUAGES` today.

### 2. The model, parser and writer

- `models.Entry` becomes `Entry(word, reading, translation, note=None,
  extra_fields=[])`. The field order is unchanged, so positional construction
  still means the same thing.
- `parser.parse` unpacks a row's first three fields into `word`, `reading`,
  `translation`. Nothing else about it changes, and it stays kind-agnostic:
  the storage format doesn't change in this milestone, so the parser doesn't
  need to know the kind.
- `writer` writes `word`, `reading`, `translation`, then the extras, as
  today. Its field-check error names the fields by their new names (`word`,
  `reading`, `translation`) and identifies the entry by `entry.word`.
- **What the parser and writer do with an alphabetical language's row on disk
  is M6's question**, not this milestone's (roadmap: "What a German entry's
  row looks like on disk, which follows from M5's field decision").

### 3. The kind reaches every screen and the compiler

- **`NotebookConfig`** gains `kind: LanguageKind`. It is filled in by
  `MainMenuScreen._notebook_config()` from the registry. Every notebook screen
  already receives a `NotebookConfig`, so this is how the kind reaches Entry
  and its autocompile. **Inspect Tree** takes only a `tree_root`, not a
  `NotebookConfig`, so it gains a required keyword, `InspectTreeScreen(tree_root,
  *, kind)`, which `MainMenuScreen` fills from the same config (found while
  implementing). Browse compiles nothing and is unchanged.
- **Entry** builds its word and reading fields from `config.kind`:
  - The word field's placeholder is `kind.word_label`, and the reading field's
    is `kind.reading_label`.
  - The reading field is composed only when `kind.has_reading`. When it is
    composed, it is disabled and skipped by `tab` exactly as `#pinyin` is
    today.
  - The word field's `Input.Changed` handler fills the reading with
    `kind.guess_reading(word)` when the kind has one, and does nothing
    otherwise.
  - Widget ids become `#word` and `#reading` (from `#hanzi` and `#pinyin`),
    and `HanziInput` becomes `WordInput`. The input-source switching on
    focus and blur is unchanged.
  - Every string the user sees is unchanged for Chinese: the placeholders
    still read "Hanzi" and "Pinyin", and "`<word>` added successfully!" still
    names the hanzi.
- **The compiler** takes the kind as a required keyword, `kind=`, on
  `compile_all`, `compile_file`, `render_source` and `render_markdown`, and
  `autocompile_one` passes it on. It is deliberately not optional: a silent
  Chinese default is exactly the hardcoding this milestone removes.
  - `_run_pandoc` passes `-V cjkfont=<kind.cjk_font>`, and `_stamp_for`
    hashes `kind.cjk_font`, in place of the module-level `CJK_FONT_NAME`.
    For Chinese the bytes are identical, so **no existing stamp changes** and
    the dev's next Compile after the refactor rebuilds nothing.
  - `render_markdown` uses the vocabulary table and the grammar triads (today's
    `_render_table`, `_render_grammar_table` and `_pair_hanzi_pinyin`,
    unchanged in output) when `kind.has_reading`. For a kind without a reading
    it raises `NotImplementedError` with a message naming M6. This is
    unreachable from the app in M5, because the only alphabetical language
    isn't functional, and it is the exact seam M6 fills.
  - The callers that have a language (`idiomas compile` per language, the
    notebook menu's Compile, Entry's and Inspect Tree's autocompile, and
    Inspect Tree's PDF-mode fallback) pass the kind they already know.
- **Autocompile of a kind without a reading** reaches the same
  `NotImplementedError` (Entry's on-exit and Inspect Tree's autocompile call
  `compile_file`). Like `render_markdown`'s, it is unreachable from the app in
  M5, and M6 fills it. The Entry test that pins the alphabetical routing clears
  the screen's dirty-file set so it doesn't trigger it.
- **`idiomas compile`** skips languages that aren't functional, using
  `is_functional` in place of `FUNCTIONAL_LANGUAGES`.
- **The landing menu** decides "functional or placeholder" with `is_functional`.
- **The wizard's** `LANGUAGE_CHOICES` becomes the registry's names, in
  registry order. It is still `["Chinese", "German"]`, so the wizard is
  unchanged. Offering all six is M7.
- **Settings › Input methods** reads `language.input_hints` from the registry
  in place of `LANGUAGE_HINTS`. A language that isn't in the registry gets no
  hints, so no option starts preselected, which is today's behaviour for an
  unknown language.

### 4. What stays as it is

- **`pinyin.py`**, `_pair_hanzi_pinyin`, the `\HanziPinyin` template macro, and
  `pinyin.is_hanzi`. They are genuinely about Chinese, and they are now
  reached only through the character-and-phonetic kind. Renaming them would be
  churn with no meaning.
- **The template** (`templates/xecjk.tex`), its name, and its unconditional
  `\usepackage{xeCJK}`. Whether an alphabetical notebook gets a different
  template, or a conditional in this one, is M6's typography question.
- **`platform.CJK_FONT_NAME`** and **`doctor`'s CJK font check.** The font
  name is platform-specific and stays in the platform layer. The Chinese kind
  references it. `doctor` still checks for it, since Chinese is a language
  every install can choose.
- **The config format**, the tree layout (`<root>/tree-<Language>`), and every
  user-visible string and keybinding.

### 5. Docs

- `stack.md` gains a short *Languages and kinds* section. It describes the
  registry, the two kinds, which fields each has, that the kind is not stored
  in the config, and that adding a language of an existing kind is one
  registry entry. Its *Storage* section notes that the three columns are
  `word`, `reading`, `translation` in code.
- `design.md` is **not** changed: nothing the user sees changes.

## A correction to the roadmap's done-when

The roadmap asks for "byte-identical PDFs across the refactor". **That bar
can't be met even by a change that does nothing.** It was checked on
2026-10-01 against this machine's pandoc and xelatex: compiling
`tests/fixtures/Food.md` twice from the same markdown, with
`SOURCE_DATE_EPOCH=0` and `FORCE_SOURCE_DATE=1`, produced two PDFs that differ
in about 14,000 bytes, including their `/ID`. pandoc runs xelatex in a fresh
temporary directory every time, and that path ends up in the output. Pinning
it down would mean changing how the app calls pandoc, in a milestone whose
whole point is that the app's behaviour doesn't change.

The same experiment showed what *is* stable: the two PDFs rasterise
(`pdftoppm -r 100`) to **pixel-identical** pages, and `pdftotext` gives
identical text. So the done-when is met by two checks, which together are
stronger than byte identity:

1. **Identical input to pandoc.** For every file in the dev's real tree, the
   markdown handed to pandoc, the full pandoc command line, and the stamp are
   identical before and after the refactor. This covers every byte that leaves
   the app. Since the stamp is unchanged, the dev's own Compile after the
   refactor reports "Everything is up to date."
2. **Identical pages.** Every PDF compiled from the real tree before and
   after rasterises to pixel-identical pages.

The roadmap's M5 section gets a dated correction note pointing here, the same
way M1's scope correction was recorded.

## Out of scope

- **Anything that makes German work**: its row on disk, its Entry form, its
  renderer, its typography, flipping its `functional` flag. All of that is M6.
  M5 only gives German an `ALPHABETICAL` kind that nothing reaches yet.
- **The four new languages, and the wizard offering them.** That is M7.
- **A user-extensible registry.** It is already in the sprint's Postponed
  table.
- **Renaming any file, template or user-visible label.**

## Context

- **Where the kind is needed today.** Ten call sites hardcode Chinese:
  `models.Entry`; `parser`'s unpack; `writer._render_entries` and
  `_check_field`; `compile`'s `_render_table`, `_render_grammar_table`,
  `_run_pandoc` and `_stamp_for`; `config.FUNCTIONAL_LANGUAGES` (read by
  `__main__` and `landing`); `wizard.LANGUAGE_CHOICES`;
  `input_methods.LANGUAGE_HINTS`; and Entry's hanzi and pinyin fields, their
  auto-fill and their tab-skip set.
- **What M3 left for this milestone.** The sprint notes say "Moving
  per-language fonts into the stamp is M5's to decide, and it happens in
  `_stamp_for`." Decided: the stamp hashes `kind.cjk_font`, which for Chinese
  is the same bytes it hashes today.
- **The sprint's assumption that "nothing in the sprint changes the on-disk
  format for existing Chinese files"** holds: the rename is code-only.
- **Tests.** About 50 test lines construct or read `Entry` by its old field
  names, and the compile tests call `compile_all` and `compile_file` without
  a kind. They are updated mechanically as part of the rename, with no test
  dropped and no assertion weakened.
