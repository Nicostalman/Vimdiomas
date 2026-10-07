# Tech stack

Every choice below is justified against the constraints in [mission.md](mission.md): a single-user terminal app for macOS and Arch Linux (the only supported platforms, Sprint 8 M1), plain-text storage, fast entry, generated PDFs.

## Summary

| Layer | Choice | Version |
|---|---|---|
| Language | Python | 3.14 |
| TUI | Textual | ≥ 0.80 |
| Pinyin | pypinyin | ≥ 0.53 |
| Storage | Markdown + tabs | — |
| PDF | pandoc → xelatex + xeCJK | pandoc 3.x, TeX Live 2026 |
| CJK font | Songti SC (macOS) / Noto Serif CJK SC (Arch Linux) | macOS built-in / Arch package |
| Tests | pytest | ≥ 8 |
| Packaging | `pyproject.toml`, src layout, venv | — |

## Language — Python 3.14

Already installed at `/opt/homebrew/bin/python3`. The workload is text munging plus a terminal UI, where Python's ecosystem is strongest and its speed is irrelevant — the largest file this program will ever parse is a few hundred lines.

Uses `dataclasses` for the model, `pathlib` throughout, and `os.replace` for atomic saves.

## TUI — Textual

The entry screen needs a tree, a form of focusable text inputs, a two-panel layout, and focus cycling. Textual provides all four as widgets (`Tree`, `Input`, `Horizontal`, the focus chain) and styles them with a CSS-like stylesheet, so layout is declarative and the borders are drawn by the framework rather than by hand.

It is a full-screen terminal application in the same family as curses — it takes over the alternate screen buffer, draws bordered panels, and handles keyboard and mouse. It is not printed ASCII.

**Rejected:**
- **prompt_toolkit** — excellent at forms, but the tree widget would be hand-rolled, including scrolling and expand/collapse.
- **Raw `curses`** (stdlib, zero deps) — everything above written from scratch, plus manual handling of CJK double-width cells. Wrong trade for an MVP.

### Screen composition

Every screen in the app (`vimdiomas.tui.screens.panels`, Sprint 4 M1-M2)
composes as **backpanel → panels → content**: one `Backpanel` per screen,
holding zero or more `Panel`s, each holding whatever content it needs (a
tree, a form's fields, a list). A menu holds zero panels — its list sits
directly inside the backpanel, which then plays the role a panel would
elsewhere (design.md's *Flat menus*). Focus and the `esc`/`enter`/shift+hjkl
keys are handled once, on `Panel`/`Backpanel`/`PanelScreen`, rather than per
screen — `Panel`'s bindings work from content without content having to
bind them itself because Textual bubbles key bindings from the focused
widget up through its ancestors, and a `Panel`'s spatial neighbours come
from the panels' actual on-screen regions (`Backpanel.neighbour`) rather
than a hardcoded per-screen order. See [design.md](design.md)'s *Navigation
conventions* for the full key model this implements, now covering every
screen and menu with no older model left running alongside it.

### User text reaches widgets through `literal()`

Textual parses a `str` given to `Static`, `Tree` or `Option` as markup, so
`[/]` in a translation raises `MarkupError` and `[b]x.md` draws as a bold `x`.
`vimdiomas.tui.screens.base.literal(text)` wraps text in a Rich `Text`, which no
markup parser sees, and is the one route for anything derived from the tree
(Sprint 6 M2). It is not a string escape: `textual.markup.escape` and
`rich.markup.escape` both double a backslash that ends a name or stands before
`[`. `app.notify` takes only a `str`, so a notification carrying user text
passes `markup=False`.

## Pinyin — pypinyin

Converts hanzi to numbered pinyin (`Style.TONE3`, `neutral_tone_with_five=True`) to prefill the pinyin field. It is a prefill, never an authority: context-dependent readings (了, 的, 还, 长) are wrong often enough that the field must stay editable, and it is.

The numbered ↔ tone-mark conversion in both directions is written locally — a small, exactly-specified transformation not worth a dependency.

**Tone marking never raises** (Sprint 6 M3). The syllabic consonants pypinyin
produces for 嗯, 呣, 噷, 哼 (`n`, `m`, `ng`, `hm`, `hng`) are marked on their `n`
or `m` with a combining diacritic and NFC-normalised — the precomposed glyph
(`ń`, `ḿ`) wherever Unicode has one, the combining form (`m̄`) otherwise. A
syllable with nothing to carry its tone prints as its bare letters and is
reported as a compile warning. Only lowercase letters form a syllable, so a
stray capital in a stored value is ignored.

**`guess()` emits syllables for hanzi only** (Sprint 6 M3): `T恤` is `xu4`,
`3D打印` is `da3yin4`. Each run of consecutive hanzi goes to pypinyin whole, so
readings still come from word context. `pinyin.is_hanzi` (CJK Unified
Ideographs and Extension A) is the one definition of hanzi, shared by the
guesser and the grammar renderer's character/syllable pairing.

## Storage — Markdown with tab-separated entries

Plain UTF-8 text. Greppable, diffable, editable in any editor, readable in fifty years.

Entries are **tab**-separated rather than pipe-tables or YAML because it is the least intrusive structure that a human can still type and realign by hand, and because commas, pipes and colons all occur inside English glosses while tabs do not.

Pinyin is stored **numbered** (`ni3hao3`), not tone-marked. It is ASCII-typeable without an input method, unambiguous, and sorts predictably; tone marks are a presentation concern applied at compile time.

**A file under the tree's top-level `Grammar/` folder gains a third heading
level (Sprint 5 M5):** `###` marks a **subtitle**, below the `##` category
and above its tab-separated triads — the same file format otherwise, so a
grammar file is byte-identical to a vocabulary one apart from this one extra
heading level. `store.is_grammar(path, tree_root)` decides which parser
behaviour applies from the path alone (any case, top level only — a nested
`Grammar/` doesn't count); `parser.parse`'s `grammar` keyword is what a
vocabulary file never sets, so a `###` line there stays what it always was:
an unrecognized line, dropped with a warning, its entries left in the
enclosing category. A grammar file's subtitles are optional and exactly one
level deep.

Because the separator is a tab, **no field may contain one** — nor a newline,
which would split the row in two. Both are stripped at the field (every text
field replaces each control character with a space as the user types, Sprint 6
M1) and refused at the writer, which raises rather than emitting a row it
could not read back. The reader is correspondingly exact: an entry row is
split on its tabs with only its line terminator removed, never with
`str.strip()`, which treats a tab as whitespace and so dropped an empty first
or last field before the split ever ran. Each field is then stripped of
spaces on its own, so a hand-realigned row reads the same as a written one.

**Tags are written the way `shlex` reads them.** `parser` reads a `## Tags`
line with `shlex.split`, so `writer._render_tag` emits the narrowest of three
forms that round-trips: `#tag`, `#"tag"`, or `shlex.quote`. The first two are
what it always emitted, kept byte-for-byte so a correctness fix doesn't
reformat the tag block of every existing file.

**A line the parser can't read is a warning, never an exception.** Both tree
screens parse every file in the tree to build themselves, so an exception
escaping the parser locks the user out of the whole tree over one bad row in
one file — the reason unparseable tag syntax and a malformed entry row are
warnings on that line (Sprint 6 M1).

**In code the three columns are `word`, `reading` and `translation`** (Sprint 6 M5; `models.Entry`). For Chinese the word is the hanzi and the reading the numbered pinyin; "Hanzi" and "Pinyin" survive only as the labels the Chinese kind gives those fields in the UI. The rename is code-only: a Chinese row on disk is still `word<TAB>reading<TAB>translation`, byte for byte.

**A kind with no reading is written as `word<TAB>translation`** (Sprint 6 M6) — two columns, extra fields after them as for Chinese, a note as the indented `*…*` line below, and tags, headings, subtitles and the `# Title` header unchanged. This is what a person types by hand. So the **parser and writer take the kind**: `parser.parse(text, stem, *, kind, grammar=False)` and `writer.write`/`save(…, *, kind)`, `kind` required with no default. A line is an entry row when it has at least as many tabs as the kind has columns minus one (two with a reading, one without), and the indented-note check runs first, so a tab-indented note is never misread as a one-tab row. For a kind with no reading `reading` is `""`, and the writer raises `ValueError` rather than silently drop one. `store.walk`, `store.tag_index`, `browse.paths_with_tag` and `BrowseScreen` take it too: `walk` needs it for a correct answer, because `has_uncategorized` depends on rows being recognised.

**Rejected:** SQLite (opaque to a text editor, breaks the whole principle), CSV (no room for categories or notes), YAML/JSON (unreadable in bulk, hostile to hand-editing).

## Languages and kinds (Sprint 6 M5)

`vimdiomas.languages` is the one place a language's behaviour is described. A **kind** (`LanguageKind`, a frozen dataclass — data, not a class per kind) says how an entry is shaped and rendered:

| Field | `CHARACTER_PHONETIC` (Chinese) | `ALPHABETICAL` (German, Italian, French, English, Spanish) |
| --- | --- | --- |
| `word_label` | `"Hanzi"` | `"Word"` |
| `reading_label` | `"Pinyin"` | `None` — no reading field |
| `guess_reading` | `pinyin.guess`, fills the read-only reading as the user types | `None` |
| `cjk_font` | `platform.CJK_FONT_NAME` | `None` — no CJK face; set in the template's own Latin Modern (Sprint 6 M6) |

`has_reading` (`reading_label is not None`) is what code branches on. A **language** (`Language`) is a name, a kind, the `input_hints` that preselect its input source, and a `functional` flag (`False` shows the placeholder instead of the notebook). `LANGUAGES` is the registry — Chinese, German, Italian, French, English, Spanish (Sprint 6 M7), in the order the wizard offers it and Settings › Add a language lists it, fixed in code, not user-extensible; `get_language(name)` returns `None` for a name outside it, which a hand-edited config can hold and which is treated as a language that isn't functional, never as an error.

**The kind is not stored in the config.** It is looked up by language name, so `config.toml` is unchanged. `NotebookConfig.kind` carries it to Entry, and Inspect Tree and the compiler take it as a required `kind=`, with no default — a silent Chinese default is exactly the hardcoding the registry removes. **Adding a language of an existing kind is one entry in `LANGUAGES`.**

Still Chinese by design: `pinyin.py`, `_pair_hanzi_pinyin` and the `\HanziPinyin` macro. They are reached only through the character-and-phonetic kind. The template loads `xeCJK` and the CJK main font **only for a kind with a `cjk_font`**, behind a pandoc `$if(cjkfont)$` conditional: `_run_pandoc` passes `-V cjkfont=…` only then, so a German PDF is plain fontspec + Latin Modern and never meets xeCJK. The template keeps its name, `xecjk.tex`.

A notebook's tree is created with its `Vocabulary/` and `Grammar/` folders by `store.ensure_tree`, which the wizard and the notebook menu both call; an existing folder of either name in any case is left as it is (Sprint 6 M6).

`doctor` knows which languages need what (Sprint 6 M7): a `Check` has `needed_for` (the registry languages whose kind sets a `cjk_font`, derived from `LANGUAGES`, for xeCJK and the font) and `install` (the platform's command, `""` when there is none). They are `required=False`; `required` keeps its meaning of "every install". `doctor.missing_for(checks, languages)` is the one rule for what blocks an install — every `required` check that failed, plus any needed by a given language — used by `vimdiomas doctor` (which reads the config if there is one and fails only on `missing_for` its languages, a German-only install passing without xeCJK), the wizard's languages step, and Settings › Add a language. `doctor.label(check)` is what is printed in brackets: `required`, `optional`, or the languages. The offer to install a missing dependency is `tui/screens/dependencies.py`, shared by the wizard and Settings; it suspends the TUI and runs the platform's command without a shell.

## PDF — pandoc → xelatex with xeCJK

pandoc is already installed and is the obvious markdown-to-anything tool; `xelatex` from TeX Live 2026 handles Unicode and system fonts natively.

`xeCJK` is what makes Chinese typeset correctly — line-breaking between hanzi, correct spacing at Latin/CJK boundaries, and font selection for the CJK range. **It is a prerequisite and is not in BasicTeX:**

```sh
sudo tlmgr install xecjk
```

The program's `doctor` command checks for it and prints exactly that line rather than surfacing a LaTeX error. (On Arch Linux, xeCJK comes with the `texlive-langchinese` package, and `doctor` prints that package's install line instead.)

The CJK font is **Songti SC** on macOS, present by default
(`/System/Library/Fonts/Supplemental/Songti.ttc`) — nothing needs
installing. Chosen by the dev (Sprint 5 M3) from a rendered comparison
against the four CJK faces installed on this machine; see
[design.md](design.md)'s *The compiled notebook* for the rest of the
notebook's typography. On Linux it is **Noto Serif CJK SC** (Sprint 5 M7),
the Ming/serif counterpart to Songti, found through fontconfig and installed
from Arch's Noto CJK package. PDFs from the two platforms are close
but not identical, which is accepted. The template takes the face as a
pandoc variable, so it's the same template on both. M2's staleness stamp
hashes the kind's font name (`kind.cjk_font`), so a tree compiled on one OS recompiles on the other.

**A compile failure is per file** (Sprint 6 M2). `compile_all` returns a
`CompileReport` (`compiled`, `failed`), catching `CalledProcessError` and
`OSError` per file. The rest of the run continues, the successes' stamps are
saved in a `finally`, and a failure carries the last `STDERR_TAIL_LINES` (10)
non-empty lines of stderr. `vimdiomas compile` exits 1 if any file failed.

**Every compile path records its stamp** (Sprint 6 M3). `compile_file` is the
one function that produces a PDF, and on success it records the stamp of what
it rendered: into the dict `compile_all` passes it (saved once per run), or
straight into the cache file when called alone (autocompile, Inspect Tree's
fallback). The cache therefore can never describe an older source than the PDF
beside it, which is what lets a single Compile trust it. The cache stays in
`~/.cache/vimdiomas/`, outside the notes tree, so deleting it stays safe.
`forget_tree(tree_root)` (Sprint 6 M8) drops the entries under a tree whose
folder Settings › Remove a language has just deleted; a kept folder keeps its
entries, so re-adding the language doesn't rebuild what hasn't changed.
`compile_all` renders each file once (`render_source`) and hands that render
to `compile_file`; the pandoc call itself is `_run_pandoc`, which is also the
seam tests fake.

**User text is escaped for where it lands** (Sprint 6 M3). Entry text goes
into the raw-LaTeX tables through `_escape`, a single-pass substitution
(so the `{}` of `\textbackslash{}` is never escaped again). Category and
subtitle headings stay *markdown*, so their level remains pandoc's and the
template's decision: `_escape_markdown` backslash-escapes ASCII punctuation
except `' " - .`, which pandoc's `smart` extension turns into typography and
which are never markup in a heading. The title goes through the same escape
and is then written as a YAML double-quoted scalar, unless it is plain letters
and single spaces, which YAML and markdown both read as themselves and which
keep ordinary files' stamps unchanged.

**Quotes and punctuation in a Chinese PDF** (Sprint 7 M2). xeCJK sets `’ ” — …`
as full-width punctuation and, after one, drops a typed space, so `a "b" c`
printed `a “b”c`. `xecjk.tex`, inside `$if(cjkfont)$`, rebinds xeCJK's
`\xeCJK_FullRight_and_Boundary:` without the `\ignorespaces` that ends it, so a
typed space after any full-width mark prints; a genuine `“你好”` is laid out
exactly as before. The edit is guarded by `\cs_if_exist:NT`: an xeCJK without
that internal keeps the old behaviour and never fails a compile. The same block
declares U+2026 `Default` class, so `...` in a heading is the Latin `…` and not
the CJK font's `⋯`. Separately, entry text is raw LaTeX, where TeX turns every
straight `"` into `”`; `_curl_quotes` (in `compile.py`, every language) writes
`“` or `”` into the intermediate markdown instead, on a field's word,
translation and note whole, before escaping and before a grammar word is split
into `\HanziPinyin` units. The source `.md` is never rewritten. Headings and the
title are curled by pandoc's `smart`, as before.

`CompileReport` also carries `warnings`: files that compiled, but with a
pinyin syllable printed without its tone mark. They describe the source, not
the run, so `compile_all` reports them for every file in the tree, including
files it did not need to rebuild.

**Rejected:** weasyprint (would need `brew install pango` and gives weaker typography for a printed reference sheet), plain HTML output (not the deliverable), headless Chrome (not guaranteed present).

## Search — a local fuzzy scorer

Subsequence matching with bonuses for contiguous runs and word-start hits, in about thirty lines. **`fzf` was rejected** because it is not installed on this machine and shelling out to an external binary for filtering a list of a few dozen filenames adds a hard dependency for nothing.

## Tests — pytest

The parser/writer round-trip is the correctness backbone: `parse(write(deck)) == deck` must hold for every fixture, including hand-edited and malformed input. That property plus the pinyin conversion table is where the test effort goes; the TUI is verified by hand.

## Prerequisites

Verified present on this machine except where noted.

| Requirement | Status |
|---|---|
| macOS, zsh | ✅ |
| Python 3.14.7 | ✅ `/opt/homebrew/bin/python3` |
| pandoc | ✅ `/opt/homebrew/bin/pandoc` |
| xelatex (TeX Live 2026 basic) | ✅ `/Library/TeX/texbin/xelatex` |
| **xeCJK** | ❌ **`sudo tlmgr install xecjk`** |
| Songti SC | ✅ system font |
| nvim | ✅ Inspect Tree's MD mode shells out to `nvim` directly (Sprint 3, M4) |

On Arch Linux (Sprint 5 M7), the reference machine is the Arch image in
[`docker/Dockerfile`](../../docker/Dockerfile), run under OrbStack on the
dev's Mac:

| Requirement | Arch package |
|---|---|
| Linux, bash | `archlinux:latest` (amd64; emulated on Apple Silicon) |
| Python ≥ 3.14 | `python` |
| pandoc | `pandoc-cli` |
| xelatex, fontspec/xcolor/caption, Latin Modern | `texlive-xetex`, `texlive-latexrecommended`, `texlive-fontsrecommended` |
| xeCJK | `texlive-langchinese` |
| Noto Serif CJK SC | `noto-fonts-cjk` (+ `fontconfig` for `fc-list`) |
| pdftoppm | `poppler` |
| fcitx5 or ibus | not in the image — no desktop session, so switching is unit-tested only |

Python dependencies install into a venv:

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Installation and config (Sprint 4 M4)

`vimdiomas` is a real console command (`[project.scripts]` in `pyproject.toml`),
runnable from any directory once installed — nothing depends on the repo's
location:

- **Config** lives at `~/.config/vimdiomas/config.toml`, independent of where
  the package is installed. It holds a user name, one root folder, and the
  registered languages — each with the input source that types the language
  (`input_method`) and the one that types translations
  (`translation_input_method`), both optional and meaning "don't switch" when
  absent (Sprint 4 M6; `input_method.py` reads them, replacing Sprint 2's
  hardcoded pair). Each language's tree is `<root>/tree-<Language>`,
  derived, not stored — there is one root folder for every language, not a
  location per language. `vimdiomas.config.load_config()` reads it and raises
  `ConfigNotFoundError` when it's missing; every subcommand catches that in
  one place and prints an actionable message. Nothing currently writes this
  file — it's hand-authored until Sprint 4 M5's installation wizard exists to
  write it, atomically (temp file + `os.replace`, matching this file's
  existing convention), the first time `vimdiomas` runs. Settings › Input
  methods rewrites it the same way afterwards (Sprint 4 M6), and also mutates
  the running `Config` in place so a change takes effect without a relaunch.

  **Serialization is a local TOML encoder** (`config._toml_string`, Sprint 6
  M1), not a dependency, for the same reason the numbered↔tone-mark
  conversion, the fuzzy scorer and the macOS plist reading are local: a small,
  exactly-specified transformation not worth one. What the config writes is
  two scalar types — a string and an array of tables — and the TOML string
  grammar for them is about ten lines. It replaced Python's `!r`, which agrees
  with TOML on ASCII letters and little else: a user named `O'Brien` finished
  the wizard and could not launch the app again. A value TOML can hold in a
  *literal* string is still written as one, which is byte-for-byte what `!r`
  produced, so no config that works today is reformatted; everything else is
  written as a TOML **basic** string with the grammar's own escapes (`\` and
  `"`, the named `\b\t\n\f\r`, and `\uXXXX` for any other C0 control or
  DEL). Literal-only was rejected: it cannot express an apostrophe, which is
  the failing case.

  **The document is validated before it replaces the file.** `save_config`
  parses its own output back with `tomllib` and compares the result against
  the `Config` that produced it; a mismatch raises and nothing is written, so
  a config the app could not read never reaches the disk. This catches an
  encoder bug — including a field added to `Config` without an encoder case
  for it — loudly at save time rather than silently at the next launch.

  **The stored `root` is always absolute.** The wizard resolves the path
  before storing it (Sprint 6 M1): a relative root is re-interpreted against
  whatever directory the process was launched from, so the same command found
  a different tree, or none, depending on where it was run. A config written
  before that fix is recovered on load by anchoring its relative root to
  `Path.home()` — the one fixed directory the app can name — so its meaning at
  least stops changing per launch. Loading is a read: the file itself is left
  alone, and the next `save_config` is what stores the resolved form.
- **Templates ship as package data.** `templates/xecjk.tex` lives at
  `src/vimdiomas/templates/xecjk.tex` and is resolved via
  `importlib.resources`, not by climbing from `__file__` — the latter breaks
  once the package is installed outside the repo (the former `PROJECT_ROOT`
  pattern).
- **Platform layer** (`vimdiomas.platform`): the sole caller of OS-specific
  tools. It dispatches on `platform.system()` at import time to
  `macos.py` or `linux.py` (Sprint 5 M7), and `linux.py` is the Arch module.
  Only macOS and Arch Linux (derivatives included) are supported (Sprint 8
  M1): `vimdiomas/supported_os.py`, stdlib only, is the gate that
  `__main__.py` runs before importing anything else, and it refuses every other
  system (see [design.md](design.md), *Supported platforms*). The layer itself
  raises `ImportError` on any other system, a backstop the gate makes
  unreachable, so another platform is one more module rather than a change at
  every call site. `__main__.py` is only that gate; the commands are in
  `cli.py`. Each module offers the same surface:
  - `open_file` (`open` / `xdg-open`);
  - `switch_input_source` and `list_input_sources` (`macism` / fcitx5 or
    ibus — Sprint 4 M6, Sprint 5 M7);
  - `CJK_FONT_NAME`, `CJK_FONT_PATH`, `CJK_FONT_URL` and
    `cjk_font_installed()` — the compiled notebook's face and how to check
    for it (a file on macOS, `fc-list` on Linux). This is the font name's
    single source of truth, which `compile.py` passes to the template;
  - `install_hint(dependency)` — the one-line install command `doctor`
    shows (`brew …`, or `pacman …` on Arch), or `None` when there isn't one;
  - `input_switcher()` — the `(name, available, url)` of the switching tool,
    for `doctor`'s optional check;
  - `user_bin_dir()` (`~/.local/bin` on both) and `DEFAULT_SHELL_CONFIG`
    (`.zshrc` / `.bashrc`) for the wizard's linking step.

  Presence checks that behave the same across operating systems
  (`shutil.which` for pandoc/xelatex/nvim) stay where they are, outside the
  layer. `tests/test_no_platform_leaks.py` fails if a string literal outside
  the layer names `brew`, `macism`, `/System/`, `/Library/`,
  `defaults export` or `xdg-open`.

  On Linux, the switching framework is probed once per process (fcitx5
  first, then ibus). fcitx5's sources come from the INI profile at
  `~/.config/fcitx5/profile`, ibus' from `gsettings get
  org.freedesktop.ibus.general preload-engines`, so neither needs D-Bus.
  With neither running, both calls are silent no-ops.

  On macOS, the source listing reads `defaults export com.apple.HIToolbox -`, whose XML
  plist `plistlib` parses directly — `defaults read` prints the old NeXTSTEP
  format, which the standard library can't parse, and no dependency is added
  for this. Its entries aren't the IDs `macism` takes: a `Keyboard Layout`
  needs the `com.apple.keylayout.` prefix on its name, an `Input Mode`
  already carries a full ID, a `Keyboard Input Method` is the container of a
  multi-mode IME and is only offered when none of its modes are enabled, and
  `Non Keyboard Input Method` (character palette, Press-and-Hold) is dropped.
  Display names come from a small table with the raw ID as the fallback,
  rather than the Carbon `TIS` API, which would need `pyobjc` for cosmetics.
- **`doctor`** labels each check required (pandoc, xelatex), needed for a
  language (xeCJK and the CJK font, for Chinese — Sprint 6 M7) or optional (the
  platform's input switcher, `nvim`, `pdftoppm`): a missing required tool
  blocks compiling; a missing language one blocks that language; a missing
  optional one only
  degrades one feature (input switching, Inspect Tree's MD mode, the PDF
  preview). The CJK font check reads `vimdiomas.platform.CJK_FONT_NAME`
  (`vimdiomas.compile.CJK_FONT_NAME` until Sprint 5 M7) rather than naming a
  face here, precisely
  because this line once lagged the template after a font change (Sprint 4
  M4 caught `doctor.py` still checking Songti SC long after the template had
  moved on to Heiti SC — Sprint 5 M3 closed that class of drift for good by
  giving the font name one source of truth in code).

## Distribution (Sprint 4 M7)

`pip install -e ".[dev]"` above is the **dev** setup — it only ever puts
`vimdiomas` on `PATH` inside that one venv, which is why it needs manual
activation to run from anywhere else. The end-user install path is a
documented **`git clone` + venv**, with the app putting itself on `PATH`:

```sh
git clone https://github.com/Nicostalman/Vimdiomas.git ~/.local/share/vimdiomas
cd ~/.local/share/vimdiomas && python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/vimdiomas          # first run, by full path: opens the wizard
```

The clone location is a suggestion, not a requirement — nothing has depended
on where the code lives since M4. Dependencies go in a `.venv` inside the
clone: self-contained, survives a `git pull`, and sidesteps PEP 668, which
refuses `pip install --user` on exactly the Homebrew/system Pythons this
README's reader is likely to have.

**The wizard's last step puts `vimdiomas` on `PATH` itself** (`install.py`): it
symlinks the running console script into `~/.local/bin`, so every run after
the first is plain `vimdiomas`. This is the chicken-and-egg the README can't
solve alone — the wizard is only reachable by running the app, so the first
run is by full path and the wizard fixes every run after it. If
`~/.local/bin` isn't on `PATH`, the step **appends the one line needed** to
the user's shell config (named from `$SHELL`, falling back to `~/.zshrc` on
macOS and `~/.bashrc` on Linux), checked against that file's
own contents first so a second wizard run never duplicates it, and touching
nothing else in it. An occupied `~/.local/bin/vimdiomas` is never overwritten —
the user is shown the command to replace it themselves. M5's rule that
quitting before the last step writes nothing covers the symlink too: the
final step creates the link, the tree folders and the config together.

**Rejected:** `pipx` (M7's own original choice, dropped by the dev in favour
of a clone they can read and `git pull`), a neofetch-style
`make PREFIX=... install`, and a `curl | sh` installer — the latter two are
patterns suited to a dependency-free script or a prebuilt binary, neither of
which fits a Python package with real dependencies; either would just wrap
`pip` under the hood. Brew packaging (the backlog's own eventual hope) stays
unscheduled. M4's `[project.scripts]` entry and packaged `templates/*.tex`
are what make the console script and the symlink work at all.

## Publishing (Sprint 7 M6)

The project is public at <https://github.com/Nicostalman/Vimdiomas>, under
**GPL-3.0** (`LICENSE`). It was called Idiomas until M6. The rename covers
the package, the command and the config and cache folders.
`config.migrate_legacy_paths()` runs first on every start and moves an older
install's `~/.config/idiomas/` and `~/.cache/idiomas/` to the new names. It also
removes the old `~/.local/bin/idiomas` link once that link dangles.

**`scripts/leak_check.sh [ref [base]]`** is run before any push to the public
repo. It scans the tree at `ref` for the dev's global git email, home folder
and user name, token shapes, and local-only files (backlogs,
`postponedfeatures.md`, bug reports). It also checks the author emails on the
commits `base` doesn't have. The patterns are read from the machine at run
time, so the script itself holds nothing personal. Commits to the public repo
use the GitHub noreply email, set as the clone's local `user.email`.

## UX/UI conventions

Navigation, keybindings, layout, and every other user-facing convention live in
[design.md](design.md), not here. This file covers technology choices and
architecture only.
