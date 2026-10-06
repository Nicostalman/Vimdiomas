# M3 · Output correctness — requirements

## Anchor (from the roadmap)

The third tier: findings where the app stays up and the data is safe, but what
lands in the PDF is wrong — plus the two remaining low-priority ones. Last of
the three because nothing else in the sprint is blocked by them, except M4,
which needs #11.

**Findings in scope:** #4, #5, #10, #11, #13, #17, #19.

**Deliverable.**

- **Every compile path records what it rendered** (#11). `compile_all` skips on
  a cached stamp; `autocompile_one` rebuilds without writing one. The cache can
  therefore describe an older source than the PDF beside it, and Compile will
  skip a genuinely stale file with nothing telling the user. Every path that
  produces a PDF records its stamp — this is what makes M4's single Compile
  option trustworthy.
- **A heading is escaped like a table cell** (#13). Category and subtitle names
  reach pandoc raw: `Food {#drinks}` loses its suffix, `*Very* common` loses its
  asterisks, and `C:\new words` fails to compile outright.
- **A title is valid YAML** (#5). `Food: fruit` as a filename makes pandoc exit
  64; `Food # drink` silently truncates.
- **Guessed pinyin never crashes the renderer** (#4) and is never misattributed
  (#19). `嗯` and `呣` guess to syllabic consonants the tone renderer rejects;
  `T恤` guesses to `Txu4` and prints as `Txù`. Syllabic consonants are
  supported, non-hanzi segments are kept out of the syllable stream, and an
  unsupported syllable degrades with a diagnostic instead of an exception.
- **A literal backslash prints as a backslash** (#10). Escaping runs in one
  pass, so `a\b` stops rendering as `a\{}b`.
- **A case-only rename works on APFS** (#17). The collision check treats a
  target that resolves to the same file as free.

**Done when.** Each of the seven findings has a regression test, with the
report's real-Pandoc cases run against real Pandoc; the compile → autocompile →
revert → compile sequence rebuilds; `嗯` and `T恤` compile and print correctly;
the dev confirms the PDFs by eye; and the full test suite passes.

Backlog source:
[`../../guidelines/backlog.md`](../../guidelines/backlog.md)'s *Bug fixes*
section — "see the file bug-report" — so
[`../../guidelines/bug-report.md`](../../guidelines/bug-report.md) is the
requirement text, cited by finding number throughout.

## Depends on M2

- **`CompileReport`** (M2, #12) is the structure #4's diagnostic goes into: this
  milestone adds a third list to it rather than inventing a second reporting
  channel.
- **Per-file failure handling** (M2, #12) is what makes #13's and #5's
  compile-breaking cases non-fatal while this milestone fixes them. The two
  milestones meet here: M2 makes a broken heading survivable, M3 stops it being
  broken.
- **`store.validate_name`** (M2, #14) is the function #17's collision check sits
  beside; #17 does not change it.

## Feeds M4

The roadmap makes M4's single *Compile* option correct only because #11 is
fixed here — "before it, the cached path could skip a stale file, which is what
made a second option feel necessary." Nothing else in M4 depends on this
milestone.

## Decisions taken while speccing (agent)

The roadmap's four open questions for this milestone were delegated by the dev
("the feature spec for the bugs is up to you, unless it's an undefined design
decision"). All four are answered below, each marked.

### #11 — the staleness stamp

| Decision | Rationale |
| --- | --- |
| **Answering the roadmap's open question: the stamp stays in the central cache; it does not move next to the PDF** | A sidecar file next to every PDF puts a non-user file inside the user's own notes tree — a directory whose defining property is that it holds nothing but their notes. Both tree screens, `walk()`, `rglob("*.md")` and the user's own `ls` would then have to know to ignore it. The cache's stated property, that deleting it is always safe, only holds because it lives outside the tree. |
| **The synchronisation the sidecar would have given by construction is achieved by giving `compile_file` the job instead**: the one function that produces a PDF is the one function that records the stamp | This is the report's own first suggestion, and it makes the invariant structural rather than a rule each caller must remember. There is no path to a PDF that does not go through `compile_file`. |
| **`compile_file` takes an optional `cache: dict[str, str] | None`.** Given one (by `compile_all`), it updates that dict in place; given none (autocompile, Inspect Tree's fallback), it loads, updates and saves the cache itself | Keeps `compile_all`'s single load/save for a whole-tree run while a one-off compile still records what it did. One code path for "record what you rendered", two callers with different batching. |
| **The render is computed once per file, not twice.** `_render_for(source, grammar) -> (markdown, stamp)` is called by `compile_file`; `compile_all` calls it for the skip decision and passes the result down | Today `compile_all` parses and renders each file to compute the stamp and `compile_file` then parses and renders it again. Folding the recording into `compile_file` without this would make it three times. |
| **A file that fails to compile records no stamp** | Already true via M2's per-file handling, and restated as a test: the next run must retry it. |

### #13 — heading escaping

| Decision | Rationale |
| --- | --- |
| **Answering the roadmap's open question: headings are escaped as *Markdown*, not emitted as raw LaTeX through `_escape`** | Emitting `\section{...}` directly would hardcode the sectioning level that `--shift-heading-level-by=-1` and the template currently decide between them — a category is `##` today and the template is free to change what that maps to. Escaping keeps the level in pandoc's hands, which is where every other structural decision in this pipeline already lives. The tables are raw LaTeX for a reason the headings do not share: their *look* is not reliably expressible through pandoc's own table conversion, whereas a heading is just a heading. |
| **`_escape_markdown(text)` backslash-escapes every ASCII punctuation character** | Pandoc's markdown treats a backslash before any ASCII punctuation character as a literal escape, and before anything else as a literal backslash — so escaping the whole class is provably safe, needs no judgement about which characters are markup this month, and cannot be wrong for a character nobody thought of. A minimal set would need revisiting every time a pandoc extension is enabled. |
| **It applies to category names and subtitle names** — the two places `render_markdown` interpolates user text into markdown | The report's location list, exactly. Entry text already goes through `_escape` into raw LaTeX and is not affected. |
| **This changes the intermediate markdown for any file whose headings contain punctuation, so those files recompile once.** The PDFs they produce are identical except where the bug was showing | Expected and stated up front: the stamp hashes the markdown, so a correct change to the markdown is supposed to invalidate it. Called out in validation so a full rebuild on first run is not mistaken for a regression. |

### #5 — the YAML title

| Decision | Rationale |
| --- | --- |
| **The title is markdown-escaped first, then wrapped as a YAML double-quoted scalar** with `\` → `\\` and `"` → `\"`, and control characters dropped | Order matters and is easy to get backwards. Markdown escaping produces backslashes; those backslashes are then inside a YAML double-quoted scalar, where `\:` is *not* a legal escape — so the YAML step has to run second and must escape the backslashes the first step introduced. Pandoc then unquotes the YAML, gets the markdown-escaped text, and parses it as markdown to literal text. |
| **Double-quoted, not single-quoted or a block scalar** | Single-quoted YAML cannot express a backslash usefully and needs `''` doubling; a block scalar needs indentation the generator would have to manage. The double-quoted form has exactly two escapes to get right. |
| **The same `_escape_markdown` as #13 is used**, so a title and a heading holding the same text render the same way | They are the same class of text — a name the user chose — arriving at the same parser. Two rules would be a bug waiting to happen. |

### #4 and #19 — pinyin

| Decision | Rationale |
| --- | --- |
| **Syllabic consonants are marked with combining diacritics, then NFC-normalised** | `n`, `m`, `ng`, `hm`, `hng` are what pypinyin produces and what the tone renderer rejects. Unicode has precomposed `ń ň ǹ` and `ḿ` but nothing for `m̄`, `m̌`, `m̀` or any of `ng`, so a precomposed table cannot cover the set. Composing with combining marks and running `unicodedata.normalize("NFC", ...)` yields the precomposed character wherever one exists and the combining form where none does — one rule, best available glyph. |
| **`_mark_vowel_index` gains the syllabic-consonant case** rather than a parallel code path | The function's job is "which character carries the mark"; for `ng` that is the `n`, for `m` the `m`. It is the same question with one more answer. |
| **Answering the roadmap's open question — an unsupported syllable renders as its own letters with the tone digit dropped**, and never raises | The alternatives were a placeholder glyph or an error. Neither helps: the user cannot correct the pinyin field, so the only useful behaviour is to print the information that exists (the letters) and lose only the part that could not be expressed (the mark). |
| **…and it is reported.** `CompileReport` (M2) gains `warnings: list[CompileWarning]`, `(source, message)`, and the compile summary screen shows them below the failures | This is the roadmap's "degrades with a diagnostic instead of an exception". M2 already built the structure and the screen; this is one field and one block, not a new reporting channel. It is also the only place in this sprint where a compile-time diagnostic reaches the user — M9 does the same for parse-time warnings, and this is deliberately the same shape. |
| **Answering the roadmap's open question on #19: both what `guess()` stores and what the renderer matches are changed** | Either alone leaves a hole. Fixing only `guess()` leaves every `Txu4` already on disk rendering as `Txù`, and the pinyin field is read-only so the user cannot repair it. Fixing only the renderer leaves the app writing values that are wrong on their face in a file the user can read. Both, and the two agree. |
| **`guess()` emits syllables for hanzi characters only**, dropping non-hanzi segments entirely: `T恤` → `xu4`, `3D打印` → `da3yin4`, `卡拉OK` → `ka3la1` | The report's own suggestion ("keep non-hanzi segments separate… or leave them out"). Leaving them out is what makes the value a clean syllable stream that `_SYLLABLE_RE` and `_pair_hanzi_pinyin` can both consume without a separator convention neither has today. `_pair_hanzi_pinyin` already pairs a non-hanzi character with `""`, so the two halves already agree once the stream is clean. |
| **`_SYLLABLE_RE` matches lowercase pinyin letters only** (`[a-zü:]+`) | The report's second suggestion. It is what makes a value already on disk — `Txu4` — render as `xù` rather than `Txù`, i.e. exactly as a freshly guessed one. |
| **Existing files are not rewritten.** A stored `Txu4` stays on disk and renders correctly; it becomes `xu4` only if that entry is ever re-saved | Per `notes-sprint-6.md`'s third Assumption, nothing in this sprint rewrites the dev's data. The renderer change is what makes that safe. |
| **`from_tone_marks` and `_segment` are untouched** | They consume tone-marked pinyin that a human typed or the renderer produced, neither of which is affected. |

### #10 — single-pass escaping

| Decision | Rationale |
| --- | --- |
| **`_escape` becomes one `re.sub` over a character class, looking each character up in a single table** that includes `\` → `\textbackslash{}` | The bug is entirely that the replacement text is fed back through later replacements. One pass makes that structurally impossible rather than ordering the replacements so it happens not to. |

### #17 — case-only renames

| Decision | Rationale |
| --- | --- |
| **The collision check treats a target that resolves to the source as free**: `target.exists() and not target.samefile(source)` | The report's own fix. `samefile` is the question `exists` was standing in for. |
| **A same-file rename goes through a temporary name in the same directory**, then to the target | On a case-insensitive filesystem a direct rename is not reliably a rename at all. Two steps are correct on every filesystem, and the intermediate name is in the same directory so it is atomic in the same way. |
| **It applies to directories, and to the `.pdf` sibling**, not just the `.md` | The report notes directory renames use the same check; the PDF moves with its source today and must keep doing so. |
| **The temp name is created with `tempfile.mktemp`-style uniqueness in the parent directory** and cleaned up if the second step fails | A fixed suffix could collide with a real file. If the second rename fails, the file is moved back and the failure reported (M2 added the `try/except OSError` this sits inside). |

## Refinements while implementing (2026-09-29)

Each row replaces the decision above that it names. They came up once the
fixes were written and run against real pandoc.

| Refinement | Replaces |
| --- | --- |
| **`_escape_markdown` escapes ASCII punctuation *except* `' " - .`**, the characters pandoc's `smart` extension turns into typography | *"backslash-escapes every ASCII punctuation character"* (#13). Escaping the whole class is markup-safe, but real pandoc then prints `Don't` with a typewriter quote and `--`/`...` as literal hyphens and dots. The four characters are never markup in a heading, and leaving them alone keeps headings typographically consistent with entry cells, where TeX ligatures curl the same characters. |
| **The title is left unquoted when it is plain letters and single spaces and not a YAML keyword** (`true`, `no`, …); anything else is escaped and double-quoted as specified | *"markdown-escaped first, then wrapped as a YAML double-quoted scalar"* (#5), applied unconditionally. Quoting every title would change every file's intermediate markdown and so every stamp: the first Compile after merging would rebuild the whole tree, against validation's "ordinary output is unchanged". |
| **A syllabic consonant carries its tone on its `n` or `m`**: `ńg`, `hḿ`, `hǹg` | Plan group 1's *"mark its **last** letter"*, which contradicted the decision table's own *"for `ng` that is the `n`"*. The table was right. |
| **Warnings are reported for every file on every Compile, not only files it rebuilds**; autocompile does not report them | Implicit in the spec. With #11 fixed, an autocompile records its stamp, so the next Compile skips that file. A warning only reported on rebuild would never be seen. `compile_all` renders every file for the skip decision anyway, so the warning costs nothing. |
| **`_render_for` is `render_source(source, *, grammar) -> Render`** (`markdown`, `stamp`, `unsupported`), and the pandoc subprocess is split out as `_run_pandoc(markdown, notebook_path)` | The spec's tuple-returning `_render_for`. The third field carries #4's syllables, and `_run_pandoc` is the seam the compile tests now fake: faking `compile_file` itself, as M2's tests did, would bypass the stamp recording this milestone moved into it. |
| **`tests/conftest.py` isolates the compile cache for the whole suite** | Nothing. Every compile now records, so the TUI tests' real autocompiles would otherwise write to the dev's `~/.cache/idiomas/`. |
| **Renaming to the unchanged name is a no-op** | Nothing. Before, it was refused as *already exists*; with `samefile`, it would go through the temporary-name dance, then retitle and recompile a file that did not change. |
| **M2's real-xelatex failure fixture is a NUL byte in a row**, not a `C:\new words` heading | M2's `_good_and_bad`, which relied on #13 to fail. A NUL byte cannot come from the form (M1, #15) and xelatex refuses it outright. |

**Found while implementing, not fixed here.** xeCJK treats the closing curly
quote `”` as full-width CJK punctuation and removes the space after it:
`a "b" c` prints as `a “b”c`. This happens before and after this milestone
alike, in titles and headings. It is not one of the report's findings, and
it is recorded in `notes-sprint-6.md`'s Postponed table.

## Context

- **`_stamp_for`** hashes the intermediate markdown, the template's bytes and
  the CJK font name. Any correct change to what `render_markdown` emits
  therefore invalidates every affected file's stamp by design — #13 and #5 will
  cause a one-time rebuild of files whose headings or titles contain the
  characters they now escape. `#10`'s change does the same for any entry
  containing a backslash.
- **`autocompile_one`** (`base.py`) is the one shared worker; Entry, Inspect
  Tree's rename, its new-file and its MD-mode edit all route through it. It calls
  `compile_file` and never touches the cache — that is the whole of #11.
- **`pinyin.guess`** joins `group[0]` for every group pypinyin returns,
  including the groups for non-hanzi characters, which come back as the
  character itself. That is #19's mechanism in one line.
- **`_pair_hanzi_pinyin`** (`compile.py`, Sprint 5 M6) already pairs a non-hanzi
  character with an empty syllable and has its own `_HANZI_RANGES`. `guess()`
  should use the same definition of "hanzi" rather than a second one — the two
  ranges move to one place.
- **`嗯`** is a character the dev could plausibly type; it is not an edge case
  constructed for the report. Its failure today is a `ValueError` escaping
  `autocompile_one`'s handler, which only catches subprocess and OS errors.
- The report's findings were reproduced against commit `aa11572`. Per
  `notes-sprint-6.md`'s first Assumption, each is **re-reproduced before being
  fixed**. #17 is macOS-specific by nature (default APFS is case-insensitive);
  its test asserts the `samefile` logic directly so it is meaningful on Linux
  too, with the end-to-end rename test skipped where the filesystem is
  case-sensitive.

## Out of scope

- **Merging the two Compile options.** M4. This milestone makes the merge
  *correct*; it does not perform it.
- **Making the pinyin field editable** so the user could correct a guess. Not in
  the report; it is a form-model change, and the whole point of #19 is that the
  guess should be right without it. Recorded here because the report names the
  read-only field as part of the impact.
- **Per-language fonts and typography.** M5 and M6.
- **Surfacing *parse* warnings.** M9. The `CompileReport.warnings` added here is
  a compile-time channel for #4's degraded syllables only; M9 is what connects
  `parse()`'s existing warnings to the UI, and it will reuse this shape rather
  than replace it.
- **Escaping entry text differently.** `_escape` is fixed (#10) but its target
  stays raw LaTeX; only the *headings and title* move to markdown escaping.
- **Anything about the tag block's rendering.** Tags are not rendered into the
  PDF today.
