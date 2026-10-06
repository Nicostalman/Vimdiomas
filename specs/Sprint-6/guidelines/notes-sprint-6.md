# Sprint 6 — notes

The agent-maintained companion to
[`../roadmap-sprint-6.md`](../roadmap-sprint-6.md): it records what was decided,
assumed, or postponed while the backlog was turned into that roadmap, and it
grows as the sprint runs.

**Where the backlog came from.** [`backlog.md`](backlog.md) is a **copy** of the
dev's root-level `postponedfeatures.md`, taken on 2026-09-29 and kept verbatim,
the same arrangement Sprint 5 used: the root file stays theirs, a living
deferred list they keep managing across sprints, while this copy is Sprint 6's
frozen record of what it said when the sprint opened. Its *Bug fixes* section
reads, in full, "see the file bug-report" — so
`bug-report-2026-09-29.md` was copied alongside it as
[`bug-report.md`](bug-report.md) for the same reason the Sprint 5 backlog's
`image-1.png` was: the reference has to keep resolving after the root file moves
on. Both root files remain the dev's and are never edited here.

**The backlog's *Brainstorming* section was answered, and the answers were not
taken into the sprint.** It asks "What other features do you think are
missing?"; three were proposed at sprint start (below, in Postponed) and the dev
chose to keep Sprint 6 to its nine backlog milestones. This is the first time
the sprint's scope was set by a *ceiling* rather than by what the backlog
contained.

**Sprint 5 closed cleanly.** All seven of its milestones — M1 through M7 — were
specced, implemented and merged (M7 via PR #37), nothing was dropped and nothing
was deferred, so no milestone carries over. The `changelog` skill ran on `main`
before this sprint opened (commit `8ca8ec8`).

**What carries over from Sprint 5's Postponed table.** Two of its items are
picked up by this sprint's backlog rather than by a deliberate carry-over
decision: **a working German notebook** — Sprint 4's standing "still inert"
decision, with the *per-language typography* and *grammar-for-German* items
attached to it — becomes M6, and **the Settings submenu**'s two placeholders,
*Add a language* and *Remove a notebook*, become M7 and M8. The rest of Sprint
5's Postponed table (Windows, WSL, `doctor`'s LaTeX packages, multi-page
preview, the tag cache, brew packaging) is restated in this file's own Postponed
table and stays out.

**The bug report is a sprint input, not a milestone's own finding.** It reviews
commit `aa11572`, Sprint 5's last, and states that no code, tests, config or
specs were changed by it — every fix in it is proposed, none applied. M1–M3 are
where they land, in the report's own recommended order. Its findings are cited
below and in the roadmap by their numbers, which are the report's.

## Decisions

Settled with the dev during this sprint-start conversation, on 2026-09-29.

| Decision | Rationale |
| --- | --- |
| **Every backlog section is in the sprint; the brainstorm answers are not** | Dev's call on both. The five feature sections plus the bug report are all on the roadmap, as in Sprint 5 — but the backlog's open *Brainstorming* question was answered with three proposals and the dev declined all three for this sprint: "backlog only", nine milestones being enough. |
| **`backlog.md` is a copy; `postponedfeatures.md` stays at the root**, and `bug-report-2026-09-29.md` is copied in the same way | Dev's choice, matching Sprint 5's. The root file goes on being their living deferred list; the sprint gets a frozen snapshot. The bug report is copied rather than moved for the same reason and so the backlog's "see the file bug-report" keeps resolving from inside the sprint. |
| **Nine milestones, ordered correctness-first, then shared surface, then the things that extend it** | Three of the report's findings block later milestones (#2 and #16 block M9's whole premise; #11 blocks M4's compile merge), so the bug tiers come first. M4 establishes the legend convention before M7 and M8 add menu options that would otherwise need retrofitting. See the roadmap's preamble. |
| **The bug report becomes three milestones, in its own recommended order** | Dev's choice from four options. The report already groups its 19 findings by what they cost — data loss, crashes, wrong output — and each group is hand-testable on its own, where one 19-bug milestone would run a long way before anything could be confirmed and a per-feature scattering would leave the findings with no feature to attach to homeless. |
| **M1 is data integrity (#1, #2, #3, #6, #8, #15, #18), M2 crash-proofing (#9, #12, #14, #16), M3 output correctness (#4, #5, #10, #11, #13, #17, #19)** | The report's own *Recommended order*, folded from six steps into three milestones. Its two P1s are both in M1; its four P3s are in M3. **Superseded on 2026-09-29 by the row below**: as written, this covers 18 of the report's 19 findings. |
| **Finding #7 joins M1**, whose scope is therefore #1, #2, #3, #6, **#7**, #8, #15, #18 — eight findings, not seven | Found while speccing M1–M3 and settled with the dev. The fold from the report's six recommended steps into three milestones dropped #7 (*relative notebook roots depend on the launch directory*), which the report pairs with #9 at step 5; #9 landed in M2 and #7 landed nowhere. Dev's choice from three (M1 / M2 / postpone): it is a config-serialization bug in the same function as #6, it costs the user access to their own tree exactly as the rest of that tier does, and M1 is already rewriting `config.py`. M1's done-when bar is eight regression tests. The roadmap's M1 section was corrected in place to match. |
| **German splits into three milestones: language kinds (M5), the German notebook (M6), add a language (M7)** | Dev's choice from three options. The alternative — introducing the abstraction inside the German milestone — means writing it once for German and again for the four alphabetical languages behind *Add a language*. M5 is a pure refactor with no user-visible change, which is what makes "Chinese is unchanged" a checkable done-when instead of a hope. |
| **The two compile options merge into one, called *Compile*, which rebuilds what is stale** | Dev's choice from three. Their own suggestion was to merge both under *Force compile*; the agent's counter-proposal was accepted: the reason the cached option feels untrustworthy is finding #11, a bug, and fixing it is cheaper than making every compile a full-tree xelatex run. Force stays available as `idiomas compile --force`, which already exists, and deleting the cache is always safe. This is why M3 precedes M4. |
| **The menu legend is one dim italic line under the list, showing the highlighted option's description** | Dev's choice from three shapes (inline suffix / cursor-following line / static block). The list stays scannable, each option gets a full sentence rather than a telegraphic phrase, and every menu in the app — landing, notebook, Settings — inherits it from the one shared `MenuScreen`. The static block was rejected as duplicating the menu on screen and growing with it. |
| **The legend is a `design.md` convention, not a milestone-local detail** | Per the project's rule that a user-facing convention applying across screens is stated once in `design.md`. It is also what makes M7's and M8's new Settings options cheap: they arrive with descriptions because the convention already requires them. |
| ***Remove a notebook* removes a registered language** | Dev's choice from three readings. It sits in Settings next to *Add a language* and the backlog introduces it as "the opposite operation" — while Inspect Tree's `d` already deletes a file from the tree, so the file-level reading would be a second path to something that exists. Deleting the language's `tree-<Language>` folder is a separate, explicitly confirmed question. |
| **Manual-editing checks surface warnings everywhere and never block** | Dev's choice from three. `mission.md` requires that the program "never silently discard a line it did not expect" — that is a reporting requirement, not a refusal one, so a file with a warning still compiles, opens and can be edited. The rejected option skipped such files at compile time, which would let one stray line withhold the artifact. |
| **M9 is last** | It is the only milestone that validates the others' output: it surfaces warnings for Chinese and German files alike, so it needs M5–M7's field model settled, and it stands on M1's parser fixes and M2's escaping. |

### Settled while speccing M1–M3 (2026-09-29)

The dev delegated the bug milestones' spec conversations — "the feature spec for
the bugs is up to you, unless it's an undefined design decision" — so only the
rows below went back to them. Everything else is recorded as an agent decision
in each milestone's own `requirements.md`.

| Decision | Rationale |
| --- | --- |
| **An entry with an empty translation stays writable** (M1, #2) | Dev's choice from three. Only the parser is fixed; hanzi remains the single required field. `mission.md`'s "must read back anything a reasonable hand-edit produces" means the parser has to accept such a row whatever the form does, so forbidding it at the form would buy nothing and cost a working input. |
| **A duplicate category name selects the existing category; a reserved one (`Tags`) is refused with a message** (M1, #18 and #8) | Dev's choice from three. Selecting is exactly what subtitle creation already does (`entry.py:416`), so the two creation paths stop differing. A reserved name has nothing to select — the heading the writer would emit is unreachable by construction — so it is the one case that refuses. |
| **A partially-failed Compile reports on the screen Compile already pushes**: `PlaceholderScreen` gains a failures block listing each failed file with the tail of pandoc's stderr (M2, #12) | Dev's choice from three. The results screen is already where the user looks after a Compile; a notification cannot hold stderr, expires, and stacks up when several files fail. M3 then adds a warnings block to the same screen for #4's degraded syllables, and M4 inherits it when the two Compile options merge. |

### Settled after M1's implementation (2026-09-29)

M1 is merged (PR #38, squash, all eight findings — #1, #2, #3, #6, #7, #8,
#15, #18). Three refinements came up against the two "Settled while speccing"
rows above once the fixes were actually written; each replaces the row it
touches rather than sitting beside it, and the reasoning is in
[`../features/M1-2026-09-29-data-integrity/requirements.md`](../features/M1-2026-09-29-data-integrity/requirements.md)'s
own *Refinements* table in full.

| Refinement | Replaces |
| --- | --- |
| **#3's third `_render_tag` branch is `shlex.quote`; the second (double-quoted) branch also covers an apostrophe**, not only whitespace | The spec's rule sent an apostrophe straight to `shlex.quote`, which round-trips but is far less readable than `#"tag"` — and the report's own reproduction already has that exact form in the file. |
| **#6's literal-string branch is not just "unchanged output" but the actual byte-identity guarantee**: any value `repr` and TOML's literal-string grammar already agree on (no `'`, no `\`, no control character) is written as a literal string; everything else is a basic string with TOML's own escapes | The spec asked for both "always a basic string" and "byte-identical to today" in the same breath, which only one of them can be once a value contains no special character — `repr` emits single quotes there. |
| **#15's sanitiser runs through `TextField.validate_value`**, the reactive's own pre-`Changed` hook, not an `Input.Changed` handler that reassigns `.value` | Textual runs `validate_value` before posting `Changed`, so no listener — including Entry's hanzi → pinyin auto-fill — ever sees an unsanitised value, and a programmatic assignment is covered along with a keystroke or paste. |

Two behaviour changes came out of #2's fix and are not in the report: an entry
row's inner fields are now stripped of spaces individually (previously only
the row's outer edges were), and a **tab-indented** triad row now reads as an
empty first field rather than raising. Both are asserted directly in
`test_parser.py` rather than left implicit.

Nothing from M1 was newly deferred; its Postponed items (control-character
handling for `PromptDialog`, in-app category rename/delete/reorder) were
already in scope's *Out of scope* section at spec time, not new discoveries,
and are covered by this sprint's existing Postponed table below.

### Settled after M2's implementation (2026-09-29)

M2 is merged (PR #39, squash, all four findings — #9, #12, #14, #16). The
"Settled while speccing" row for #12 stands as written: a partially-failed
Compile reports on the screen Compile already pushes, under a *Failed:* block
with the tail of each file's stderr. Three of M2's own agent decisions were
corrected once the branch was open; each is in
[`../features/M2-2026-09-29-crash-proofing/requirements.md`](../features/M2-2026-09-29-crash-proofing/requirements.md)'s
*Corrections* table in full.

| Correction | Replaces |
| --- | --- |
| **`literal()` returns a Rich `Text`, not an escaped `str`**, and a notification carrying user text passes `markup=False`. The whole message is literal, not just its user-derived fragments | The spec's escaped-string helper. Neither `textual.markup.escape` nor `rich.markup.escape` round-trips a backslash: `a\[b]` and a name ending in `\` both come out doubled. A `Text` never meets a markup parser. |
| **New directory stays at the tree root** | The spec's move to the cursor's directory. The dev's Sprint 3 backlog: "Directories can not be nested, so where the user is standing does not matter." `validate_name` refusing `/` keeps it enforced. |
| **`PromptDialog`'s initial value is not escaped** | The spec's list of call sites. It is an `Input` value, which is never parsed as markup. |

Two consequences for later milestones:

- **M4** inherits `main_menu.compile_summary(report)` as the one place a
  Compile's results are worded; merging the two options leaves it unchanged.
  M3's #4 warnings block belongs there too.
- **M9** stands on `literal()`: a warning quoting a raw line from a file must
  go through it, since that line is exactly the kind of text that holds
  brackets.

M2 also closes the gap M1 left open: `PromptDialog`'s plain `Input` has no
control-character sanitiser, and `validate_name` now refuses control
characters in the one place that prompt's value reaches the disk. Nothing was
newly deferred.

### Settled after M3's implementation (2026-09-29)

M3 is merged (PR #40, squash, all seven findings: #4, #5, #10, #11, #13,
#17, #19). With it, all 19 of the bug report's findings are fixed. None of its
decisions went back to the dev. The five refinements to its agent decisions
are in
[`../features/M3-2026-09-29-output-correctness/requirements.md`](../features/M3-2026-09-29-output-correctness/requirements.md)'s
*Refinements* table in full. The two that reach beyond M3:

| Refinement | Replaces |
| --- | --- |
| **Headings and titles leave `' " - .` unescaped**, pandoc's smart-typography characters, and a title of plain letters and single spaces stays unquoted | The spec's "escape every ASCII punctuation character" and "always double-quote the title". Both were markup-safe, but the first straightened quotes and dashes in real PDFs and the second would have rebuilt every file once. |
| **Compile warnings are reported for every file on every Compile**, not only files it rebuilds | Implicit in the spec. Once autocompile records its stamp (#11), a warning shown only on rebuild would never be seen. |

Consequences for later milestones:

- **M4** can merge the two Compile options: #11 is fixed, and every compile
  path records its stamp. `compile_summary` now has three blocks (compiled,
  *Failed:*, *Warnings:*), and an up-to-date tree can still show warnings.
- **M5** finds the hanzi definition in `pinyin.is_hanzi` and the pandoc call
  in `compile._run_pandoc`, which is also the seam the compile tests fake.
  Moving per-language fonts into the stamp is M5's to decide, and it happens in
  `_stamp_for`.
- **M9** reuses `CompileReport.warnings` / `CompileWarning(source, message)`
  for parse-time warnings rather than a second channel, as M3's spec
  anticipated.

Newly deferred: the xeCJK closing-quote spacing issue, in the Postponed table
below.

### Settled after M4's implementation (2026-10-01)

M4 is merged (PR #41, squash). Decisions made while speccing and implementing it,
in full in
[`../features/M4-2026-10-01-notebook-menu/requirements.md`](../features/M4-2026-10-01-notebook-menu/requirements.md):

| Decision | Detail |
| --- | --- |
| **Every Compile re-parses every file; only xelatex is skipped for an unchanged one** | Confirmed with the dev: the single *Compile* is trustworthy because the stamp is of the regenerated markdown (M3), so an edit from Neovim or the app is always picked up. A forced rebuild stays `idiomas compile --force`; no key on the menu forces one. |
| **The legend covers four menus, not three** | The input-methods language picker is a fourth `MenuScreen`; the dev chose to include it because the convention says *every* menu. |
| **`MenuOption` makes a description a requirement, not a habit** | `MenuScreen` raises `TypeError` for a plain `Option`. **M7 and M8** build their menus' options as `MenuOption`s and replace the "Not available yet." descriptions on *Add a language* and *Remove a notebook* along with the behaviour. |
| **Legend look, from hand-testing** | Two rows always reserved, dim italic, the list's width and padding, plus a one-row margin above it (dev: "a little more space"). Convention stated once in `design.md`'s *Menu legend*. |

Newly deferred: a menu taller than its frame, in the Postponed table below.

### Settled after M5's implementation (2026-10-01)

M5 is merged (PR #42, squash). Decisions made while speccing and implementing it,
in full in
[`../features/M5-2026-10-01-language-kinds/requirements.md`](../features/M5-2026-10-01-language-kinds/requirements.md);
the dev took the recommended option on each of the roadmap's four open
questions.

| Decision | Detail |
| --- | --- |
| **`Entry` is `word`, `reading`, `translation`** | A code-only rename of `hanzi`, `pinyin`, `gloss`: the row on disk is still `word<TAB>reading<TAB>translation`, so the sprint's assumption that no existing Chinese file changes holds. An alphabetical language's `reading` is `""`. What its row looks like on disk is **M6's** question. |
| **A kind is data, not a class** | One frozen `LanguageKind` with two instances, `CHARACTER_PHONETIC` and `ALPHABETICAL`; code branches on `has_reading`. |
| **The kind comes from a built-in table, not the config** | `languages.LANGUAGES`; `config.toml` is unchanged. **M7** extends the same table from two entries to six. |
| **"Functional" survives as a flag on the table entry** | `config.FUNCTIONAL_LANGUAGES` is deleted. German is `functional=False` until **M6** flips it. A name outside the registry is "not functional", never an exception. |
| **The roadmap's "byte-identical PDFs" is replaced** | It can't be met even by a no-op: pandoc's temporary directory ends up in the PDF. Met instead by identical pandoc input (markdown, argv, stamp) and pixel-identical pages, checked with `check_equivalence.py` on a copy of the dev's tree. Recorded in the roadmap. |
| **The compiler's `kind=` is required, with no default** | A silent Chinese default is the hardcoding M5 removes. Inspect Tree, which had no `NotebookConfig`, takes a required `kind=` of its own. |
| **The alphabetical seams are `NotImplementedError`s naming M6** | `render_markdown` (and so autocompile) for a kind with no reading. Unreachable from the app until German is functional. `ALPHABETICAL.cjk_font` is `None`, provisional until M6 picks German's typography. |

### Settled after M6's implementation (2026-10-01)

M6 is merged (PR #43, squash). Decisions made while speccing and implementing it,
in full in
[`../features/M6-2026-10-01-german-notebook/requirements.md`](../features/M6-2026-10-01-german-notebook/requirements.md);
the dev took the recommended option on each of the roadmap's four open
questions, and hand-testing added two requests (§7 and §8 there).

| Decision | Detail |
| --- | --- |
| **A German row is `word<TAB>translation`** | Two columns, extra fields and the indented `*note*` as for Chinese. The parser and writer take the kind (`kind=` required, no default); so do `store.walk`/`tag_index` and Browse. Chinese files are read and written exactly as before. This settles M5's "what a German row looks like on disk". |
| **German's typography is Latin Modern, and no xeCJK** | `ALPHABETICAL.cjk_font` is `None`, now final. The one template loads xeCJK behind `$if(cjkfont)$`; the file keeps the name `xecjk.tex`. This answers the Assumption that German's typography is an open question. |
| **The German tables are Chinese's minus the pinyin** | The vocabulary table drops its middle column; the grammar block's head line is `\GrammarWord` (a `\parbox`, so a wrapped phrase doesn't collide) instead of the `\HanziPinyin` run. Branches only where the kinds differ; no second renderer and no new class. |
| **Every notebook's tree gets `Vocabulary/` and `Grammar/`** | `store.ensure_tree`, called by the wizard and when a notebook menu opens, matching a folder's name in any case. Dev's request after hand-testing. **M7's *Add a language* calls the same helper.** |
| **A vocabulary row too long for the columns is an exception, for every kind** | A word wider than 12em in `\Large`, or the row that makes the table wider than the text, is set across the full width and wraps with a 1.5em hanging indent. Widths are estimated by one shared function; a table that fits is rendered exactly as before. Dev's request, asking for it "at class level". |
| **A long Chinese grammar phrase wraps between units** | `\HanziPinyin` allows a break after each unit; the Chinese markdown is unchanged. The dev confirmed it works, and no deferred note is needed. |
| **The Chinese bar is M5's, with one allowed difference** | The markdown and pandoc argv are identical for every file of the dev's tree and every page is pixel-identical. The stamps differ once, because the template changed, so the first Chinese Compile rebuilds each file once. |

Newly deferred: `doctor` still requires xeCJK and the CJK font whatever languages
are configured, in the Postponed table below. A single word wider than a whole
line (about 70 letters at `\Large`) still overruns; the dev thought it unrealistic.
Nothing else was deferred.

### Settled after M7's implementation (2026-10-01)

M7 is merged (PR #44, squash). Decisions in full in
[`../features/M7-2026-10-01-add-a-language/requirements.md`](../features/M7-2026-10-01-add-a-language/requirements.md);
the dev settled the roadmap's four open questions plus the `doctor` item
inherited from M6, and hand-testing asked for nothing further.

| Decision | Detail |
| --- | --- |
| **The registry is fixed in code, six entries** | Chinese, German, Italian, French, English, Spanish, in that order for both the wizard and Settings. Four of them are a `Language(...)` line with input hints and nothing else: a test checks that no executable string outside `languages.py` and the platform display-name tables names them. A user-extensible registry stays postponed. |
| **Add a language hides registered languages**; with none left it says "Every supported language is already added." | Dev's choice. No disabled-row style was introduced. |
| **An existing `tree-<Language>` folder is adopted untouched**, through `store.ensure_tree` | Dev's choice. This is what makes the Assumption that removing a language is reversible by re-adding it true for M8. |
| **A new language is appended to the landing menu**, and the menu rebuilds when shown again | `MenuScreen.on_screen_resume` re-reads `menu_options()` and keeps the highlight on the same option id, so every menu follows the running config without a relaunch. |
| **Adding saves a copy of the config first**, then appends to the running one | Unlike Input methods, which saves the live config in place: a failed save here cannot leave the running app ahead of the file. |
| **`doctor` knows which languages need what** | xeCJK and the CJK font are `required=False` with `needed_for` derived from the kinds; `doctor.missing_for(checks, languages)` is the one rule used by the CLI, the wizard and Settings. `idiomas doctor` reads the config, so a German-only install passes without xeCJK. This closes the item M6 postponed. |
| **A missing xeCJK or font is offered for installation, on both surfaces** | Through one shared helper: it asks, suspends the TUI, runs the platform's command in the terminal so `sudo` can prompt, and rechecks; the recheck decides, not the exit code. Only a language's own dependencies are ever offered, never `pandoc` or `xelatex`. With no command (an unknown distro, or macOS's font, which ships with the OS) the language is refused with the message. |
| **The wizard checks the CJK pair at step 3, not step 1** | Step 1 still lists them, labelled `[ Chinese]`, and never blocks on them: which languages are wanted isn't known yet. |
| **The wizard's language checkboxes are one row each** | Found in implementation: six default checkboxes pushed *Next* off an 80x24 terminal. |
| **Settings' picker descriptions read "Start a notebook for {language}."** | "Start a Italian notebook" doesn't read. |

Not verified by hand: the install offer against a real `sudo` prompt, for
example on the Linux container from Sprint 5 M7. The tests fake `suspend` and
`subprocess`. Newly deferred: nothing. M4's note about a menu taller than the
frame did not bite: the longest list M7 adds is four options.

### Settled after M8's implementation (2026-10-02)

M8 is merged (PR #45, squash), on the dev's go-ahead. Decisions in full in
[`../features/M8-2026-10-01-remove-a-language/requirements.md`](../features/M8-2026-10-01-remove-a-language/requirements.md).

| Decision | Detail |
| --- | --- |
| **Removing unregisters; deleting the folder is a second, separate `ConfirmDialog`** | Dev's choice. Asked only if the folder exists; `n`/`esc` keep the notes; `enter` confirms neither. Deletion is permanent, like Inspect Tree's `d`. |
| **The last language can be removed** | The landing menu then lists only *Settings* ("Add a language to start a notebook."), and the Input methods and Remove pickers show placeholders. `idiomas compile` and `idiomas doctor` exit 0 on an empty list (tests added, no code change). |
| **The label is *Remove a language*** | The backlog's "Remove a notebook" is replaced in the UI, README and `design.md`. |
| **Removing drops the whole config entry** | A re-added language is asked its keyboards again; the config format didn't change. |
| **The config is saved (as a copy) before the folder is touched**, then the running config is mutated | A failed save leaves the language registered and its folder intact. A failed `rmtree` leaves the language removed and says so. |
| **`compile.forget_tree`** | Purges a deleted folder's cache entries after a successful delete; a kept folder keeps them, so a re-added language doesn't rebuild unchanged files. |

This settles the Assumption that removing a language is reversible by
re-adding it: a test drives remove (keep) → add, and the notes and PDFs are
untouched. M4's note about a menu taller than the frame did not bite either:
the longest picker is six options. Not hand-tested by the agent: the dev's
checklist in `validation.md`. Newly deferred: nothing.

### Settled after M9's implementation (2026-10-02)

M9 is merged (PR #46, squash). Decisions in full in
[`../features/M9-2026-10-02-manual-editing-checks/requirements.md`](../features/M9-2026-10-02-manual-editing-checks/requirements.md).
The dev reframed the milestone mid-spec: it checks a file against the format
the app itself writes, so the spec was rewritten around that format.

| Decision | Detail |
| --- | --- |
| **The format `writer.write` emits is the standard** | Anything outside it is reported when it is *lossy*: the text doesn't reach the PDF as itself, or is read back as something else. Lossless deviations (whitespace, note indentation, tag placement and quoting) stay silent, because the next in-app write tidies them. Six deviations that were silent now report: an extra column, a row with no word, a non-`#tag` token in the tag block, a second `## Tags`, a missing header, a duplicate category or subtitle name. |
| **No live detection** | Dev's call: no watcher, no polling, no re-read on resume. The app re-checks where it reads the file anyway: when a tree screen opens, when MD mode's `nvim` exits having changed the file, before every Entry write, and on every compile. |
| **No differ: the TUI rebuilds from the file unconditionally** | Dev's call. A non-trivial hand change (a category renamed) is always reflected, and a trivial one costs a redraw of the same thing. |
| **A dim `⚠` on the file in both trees; the list in Inspect Tree's preview pane, MD mode only; no count anywhere else** | Dev's call, refined while hand-testing: in PDF mode the block displaced the rendered page. A file edited through the app is treated the same way. |
| **Compile and `idiomas compile` group warnings by file and still exit 0** | A warned file still compiles and counts as compiled. |
| **MD mode opens `nvim` with `noexpandtab`** | Found while hand-testing: with `expandtab`, a hand-typed Tab became spaces, which the parser can't read as columns. Applies only to the buffer the app opens. |
| **`parse()` keeps exactly what it kept before** | The warnings are additive, so no deck, tag list or PDF changes. Making the app a format enforcer would have been a scope jump for the sprint's last milestone. |

Newly deferred: nothing. Fixing a warned line still means `nvim`, the standing
*editing an existing entry* item below.

### Sprint 6 closed (2026-10-03)

**All nine milestones, M1 through M9, were specced, implemented and merged**
(PRs #38–#46). Nothing was dropped and no milestone carries over. All 19 of
the bug report's findings are fixed, and the app now supports six languages
of two kinds.

**Carried into Sprint 7, by the dev's choice at its sprint start:** the
*xeCJK curly-quote space* item from the Postponed table below. Searching inside
entries comes back through Sprint 7's own backlog (*Search for entries*), not as
a carry-over. Every other Postponed item stays out of Sprint 7, including
editing, deleting and moving an entry.

## Assumptions

Taken as given by this sprint; not verified in code or stated in the roadmap.

| Assumption | Origin | Notes |
| --- | --- | --- |
| **The bug report's 19 findings are all still reproducible** | It reviews commit `aa11572`, which is `main`'s tip bar the changelog commit, and states each finding was reproduced rather than read off the code | Two findings are explicitly marked as read-from-code rather than reproduced: the `idiomas compile` CLI traceback within #12, and new-directory's share of #14. Each milestone re-reproduces before fixing. |
| **`models.Entry`'s field names are the sprint's biggest open question** | The backlog: "there's no equivalent to hanzi, so the text field should not appear" | Ambiguous as written — Chinese has two word fields (`hanzi`, `pinyin`) and an alphabetical language has one, but which slot it occupies, and whether the fields are renamed to something kind-neutral, reaches the parser, the writer, every screen and every file already on disk. Assigned to **M5's** spec conversation, deliberately not M6's. |
| **Nothing in the sprint changes the on-disk format for existing Chinese files** | Follows from M5 being a refactor | If M5's field decision turns out to require a format change, that is a sprint-level scope question to raise with the dev, not a milestone's call: the dev's own tree is the data. |
| **The four new languages need no per-language code** | The backlog: "All languages that will be supported fall under the german category (alphabetical only) or chinese category" | This is what M5 and M6 exist to make true, and M7's done-when is where it is actually checked. If Italian or French turns out to need something German does not — an accent-input concern, a typographic one — it surfaces there. |
| **German's typography is an open question, not a reuse of Chinese's** | Sprint 5's Postponed table flagged per-language typography when it settled Songti SC for the whole app | Songti SC is a CJK face and macOS-only; a German notebook wants neither. M6's spec conversation picks the face, and M5's language-kind description is where a per-language font belongs. |
| **Removing a language is reversible by re-adding it** | Follows from M8 leaving notes on disk by default | Only true if M7's *Add a language* tolerates an existing `tree-<Language>` folder — listed as open in M7's spec conversation for exactly this reason. |
| **The dev hand-tests on macOS, as always** | Every sprint so far | Sprint 5 M7 added Linux via an OrbStack container; nothing in this sprint is platform-specific, but M1's #6 (TOML), M2's #9 (missing `nvim`) and M3's #17 (case-insensitive APFS) all have platform-flavoured reproductions. #17 is macOS-specific by nature. |

## Postponed features / pending

Raised during the sprint and deliberately not implemented now. Deferred items
from the dev's own `postponedfeatures.md` are **not** duplicated here — that
file is the dev's and stays the record for them. Sprint 5's own Postponed table
stays where it is; only what this sprint touches or carries is restated below.

| Item | Why postponed | Where it resurfaces |
| --- | --- | --- |
| **Editing and deleting an existing entry in the app** | Proposed at sprint start as an answer to the backlog's *Brainstorming* question, and declined for this sprint — nine milestones was the ceiling. Entry only creates today, so fixing a typo in a saved word means opening nvim; `mission.md`'s own problem statement ("moving 番茄 from *Vegetables* to *Fruits* is a cut-and-paste ritual") is still literally true of this app | The next backlog. First candidate of the three. |
| **Searching inside entries** | Same: proposed and declined for scope. Browse fuzzy-finds filenames and filters by tag but cannot find a word, and "Unsearchable across files" is `mission.md`'s first bullet | The next backlog. It would reuse `store.fuzzy` and the existing tag cache. |
| **Moving an entry between categories or files** | Same, and it is the weakest of the three on its own: it is a natural extension of in-app editing rather than a milestone that stands without it | The next backlog, behind in-app editing. |
| **Windows support** and **WSL** | Carried from Sprint 5 unchanged. The platform layer makes both an addition rather than a rewrite; nobody has a machine to test either on | Whenever someone needs it. |
| **`doctor` checking for the LaTeX packages the template loads** (fontspec, xcolor, caption, lmodern) | Carried from Sprint 5: on Arch a bare `texlive-xetex` passes `doctor` and then fails to compile. M2's #12 makes such a failure survivable and reportable, which lowers the pressure further | Whenever a missing-package compile error shows up in practice. |
| **Multi-page PDF preview** | Carried from Sprint 5: the pane shows a page of a document, and the notebooks are short | If a notebook grows past a page or two often enough to be annoying. |
| **Persisting the tag cache** | Carried from Sprint 5: `store.py`'s `TagCache` is still rebuilt in memory on every Browse open and could share the compile cache's home | If Browse ever feels slow on a large tree. |
| **Brew packaging** | Carried from Sprint 4 and Sprint 5 with the same standing: the documented `git clone` install works | A nice-to-have, unscheduled. |
| **xeCJK eats the space after a closing curly quote** | Found while implementing M3: xeCJK treats `”` as full-width CJK punctuation, so `a "b" c` in a title or heading prints as `a “b”c`. It happened before M3 as well, it is not one of the bug report's findings, and the fix is a template setting (xeCJK's punctuation classes) that would need its own check against the dev's real PDFs | M6, when German gets its own typography and a quote-heavy alphabetical language makes it visible, or the next backlog if the dev hits it first. |
| **A menu taller than the frame can push its legend off-screen** | Found while hand-testing M4: the list clips to the frame and scrolls on its own, and the backpanel scrolls as well, so with a 15-option menu in a 16-row terminal the legend sits below the fold. The dev kept it as is: no menu is near that size (the tallest has four options and fits in about 11 rows). A fix would cap the list's height so the legend stays in view | **M7 and M8**, if *Add a language* or *Remove a notebook* produce a long list, or the input-methods picker once many languages are registered |
| **A user-extensible language registry** | M7 adds six languages from a list the code owns. Letting the user register an arbitrary language would need a kind, a font and an input-method story per entry, with nobody to test them | Settled in M7 as fixed in code for now; it lands here properly. |
| **`doctor` requires xeCJK and the CJK font whatever the configured languages** | Found in M6: a German-only install never uses them, but still must pass them. | **Resolved in M7**: they are needed only by the languages whose kind sets a CJK face. |

