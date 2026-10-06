# Roadmap — Sprint 6

Sprint 5 cleared its backlog whole and left the app Chinese-only, on macOS and
Linux, with a grammar folder that renders. Sprint 6 is the sprint that **makes
the app a language app rather than a Chinese app**, and it starts by paying off
a debt: a 19-bug review of the closing commit
([`guidelines/bug-report.md`](guidelines/bug-report.md), referenced by the
backlog's own *Bug fixes* section) found two ways to lose or corrupt a user's
notes and several ways an ordinary keystroke ends the session. Nothing new is
built on top of that.

Every section of [`guidelines/backlog.md`](guidelines/backlog.md) is on this
roadmap and nothing is deferred, as in Sprint 5 — but this time the backlog's
*Brainstorming* section was answered and its answers were **not** taken into the
sprint: the dev's call, nine milestones being enough. They are recorded in
[`guidelines/notes-sprint-6.md`](guidelines/notes-sprint-6.md)'s Postponed
table, which is also where the decisions behind this roadmap live.

The backlog's five feature sections become six milestones (the bug report
becomes three, and *Implement german* splits into three with *Add a language*),
for **nine** in total.

The ordering principle is **correctness before capability, then the shared
surface before the things that extend it**:

- **The bug report comes first, in its own recommended order** (M1–M3). Three of
  its findings are not merely bugs but blockers for what follows: an entry saved
  with no translation cannot be reparsed at all (#2) and bracket text in a
  file crashes the tree (#16), which is precisely the input M9 has to survive;
  and autocompile's stamp desync (#11) is the reason the notebook menu currently
  needs two compile options, which M4 removes.
- **The notebook menu (M4) comes before the two milestones that add menu
  options.** It establishes the per-option legend as a convention in
  [`../current/design.md`](../current/design.md), so M7's and M8's new Settings
  entries are written with descriptions rather than retrofitted with them. Its
  compile merge is the first consumer of M3's #11 fix.
- **The language work goes abstraction → first consumer → the rest** (M5–M7):
  the language-kind split is introduced with Chinese refactored onto it and no
  behaviour change, German is then the first language that exercises it, and
  only then do the four alphabetical languages arrive behind *Add a language*.
  Doing German first and generalizing after would mean writing the abstraction
  twice.
- **Removing a language (M8) follows adding one (M7)**, sharing its
  config-mutation path, and is meaningless before it.
- **Manual-editing checks (M9) come last**, because they are the one milestone
  that validates *everything else*: they surface warnings for Chinese and
  German files alike, so they need M5–M7's field model settled, and they stand
  on M1's parser fixes and M2's markup escaping.

Sprint 4's and Sprint 5's vocabulary is used below without re-explaining it: a
**menu** is a screen whose content is a list; a **screen** is what opens from a
menu; a screen is a **backpanel** holding **panels** holding **content**; a
**grammar file** is one under the tree's top-level `Grammar/`. See
[`../current/design.md`](../current/design.md).

Each milestone lists its deliverable, what its spec conversation still has to
settle, and the condition that closes it.

---

## M1 · Data integrity

The first tier of [`guidelines/bug-report.md`](guidelines/bug-report.md)'s
recommended order: every finding where the app writes something it cannot read
back, or acts on the wrong file. These are the ones that cost the user data or
lock them out of their own tree, and they are first for that reason alone.

**Findings in scope:** #1, #2, #3, #6, #7, #8, #15, #18.

> **Corrected 2026-09-29, while speccing M1–M3.** This section first listed
> seven findings, and M1–M3 between them covered 18 of the report's 19: #7 was
> in none of them, the report pairing it with #9 at its own step 5 and the fold
> into three milestones dropping it when #9 went to M2. Settled with the dev and
> added to M1 — see
> [`guidelines/notes-sprint-6.md`](guidelines/notes-sprint-6.md)'s Decisions.

**Deliverable.**

- **A pending delete stops surviving a rename of its parent** (#1, P1). Today
  deleting `Old/DeleteMe.md` and then renaming `Old/` to `New/` un-deletes the
  file in the tree and leaves the pending path pointing at something that may
  by then be a different file — on leaving Inspect Tree, the wrong file is the
  one that goes. Either the pending paths are remapped with the rename or the
  rename is refused while descendant deletions are pending; either way a
  destructive commit verifies the target is still what was marked.
- **An entry with an empty field round-trips** (#2, P1). `你\tni3\t` is
  writable through the form today and unparseable afterwards — and because both
  tree screens parse every file to build themselves, one such row locks the
  user out of the whole tree. The split stops discarding empty boundary fields,
  and a malformed row becomes a diagnostic rather than an exception escaping
  discovery.
- **Tags survive a write** (#3). The parser reads tags with `shlex`; the writer
  quotes only whitespace. `#"don't"` parses and then rewrites to `#don't`,
  which no longer parses — so adding an unrelated entry corrupts the file's tag
  block. Writing becomes `shlex`-compatible, and unparseable tag syntax is a
  warning rather than a crash.
- **The config survives an apostrophe** (#6). `config.py` serializes with
  Python's `!r`, which is not TOML. A user named `O'Brien` finishes the wizard
  and cannot launch the app again. A real TOML encoder replaces it, and the
  document is validated before it replaces the existing file.
- **Reserved and duplicate category names are refused** (#8, #18). `Tags` as a
  category name produces a heading the parser reads as metadata, and a second
  `Food` produces a heading nothing can ever reach. Both are rejected at the
  form with a visible message and no file written — or, for the duplicate, the
  existing category is selected, as subtitle creation already does.
- **A tab pasted into a field cannot shift the columns** (#15). Control
  characters are stripped or rejected at the form, and the writer refuses to
  emit a field containing a tab.
- **A tree root is stored absolute** (#7). The wizard validates a resolved path
  but stores the raw one, so a relative answer is re-interpreted against every
  future process's working directory: the same command finds a different tree,
  or none, depending on where it was launched. The wizard resolves before
  storing, and a config that already holds a relative root gets an explicit,
  stable recovery.

**Open for the spec conversation.** Whether #1 is solved by remapping or by
refusing the rename. What a row the parser cannot unpack becomes — a `Warning`
and a skipped line, or a best-effort entry — given that M9 will be the thing
that shows it. Whether an empty translation stays *writable* at all, or joins
hanzi as a required field. Which TOML writer is used (a dependency, or a small
correct encoder in `config.py`). Whether a duplicate category name is refused or
silently resolves to the existing one.

**Done when.** Each of the eight findings has a regression test matching the
report's *Regression coverage* line; the two P1 reproductions no longer
reproduce; a config containing both quote characters and a backslash saves and
reloads; the same command finds the same tree from any working directory; the
dev confirms by hand in their own tree; and the full test suite passes.

---

## M2 · Crash-proofing

The second tier: every finding where ordinary input or an ordinary keystroke
takes the whole TUI down. None of these corrupt data; all of them end the
session, and two of them make a screen unopenable while the offending file
exists.

**Findings in scope:** #9, #12, #14, #16.

**Deliverable.**

- **Bracket text in a notebook is text, not markup** (#16). `[/]` in a
  translation crashes Inspect Tree's MD mode; a category named `Verbs [/x]`
  makes Entry unopenable; `[b]x[/b]` in a filename is silently shown as `x`.
  Every place user text reaches a widget — previews, tree labels, select
  labels, notifications — passes it as literal content rather than markup.
- **A compile failure is reported, not fatal** (#12). The notebook menu's
  Compile and Inspect Tree's PDF-mode `Enter` call into the compiler outside any
  handler, so one file that xelatex rejects ends the session and discards the
  cache entries for every file that had already rebuilt in that run. Failures
  become per-file: the rest keep compiling, the successes are saved, and the
  user is told which files failed and why. The `idiomas compile` CLI stops
  printing a raw traceback for the same reason.
- **A name prompt cannot write outside the tree** (#14). Rename, new file and
  new directory join their input straight onto a parent path, so `../outside`
  moves a file out of the tree and `sub/food2` crashes the app after having
  already rewritten the file's header. Path separators, `.`/`..` and edge
  whitespace are refused before anything touches the filesystem, and a header is
  only rewritten once the rename has succeeded.
- **A missing optional editor is a message** (#9). `doctor` calls Neovim
  optional; Inspect Tree's MD-mode `Enter` invokes `nvim` with no handler for
  its absence. The action reports that the editor is unavailable and leaves the
  screen usable and the file untouched.

**Open for the spec conversation.** Whether escaping happens at each call site
or behind a single helper every screen routes user text through. What a
partially-failed Compile shows — a summary screen, a notification, the existing
`PlaceholderScreen` — and how much of pandoc's stderr is worth showing. Whether
the name validation is shared with M1's category-name rules as one rule set.

**Done when.** Each of the four findings has a regression test; none of the
report's reproductions ends the session; a tree containing a file named
`[b]x.md` with `[/]` in a translation opens in both tree screens; a deliberately
broken file next to a good one leaves the good one compiled and the app running;
the dev confirms by hand; and the full test suite passes.

---

## M3 · Output correctness

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

**Open for the spec conversation.** Whether the stamp moves next to the PDF
instead of staying in a central cache, which would make any writer keep them in
sync by construction. Whether headings are escaped as Markdown or emitted as raw
LaTeX through the existing `_escape`. What an unsupported pinyin syllable
renders as. Whether #19's fix changes what is *stored* by `guess()` or only what
is rendered — the pinyin field is read-only, so the user cannot correct either.

**Done when.** Each of the seven findings has a regression test, with the
report's real-Pandoc cases run against real Pandoc; the compile → autocompile →
revert → compile sequence rebuilds; `嗯` and `T恤` compile and print correctly;
the dev confirms the PDFs by eye; and the full test suite passes.

---

## M4 · The notebook menu

The backlog's *Main menu modifications*, in full — the reorder, the merge, and
the legend the dev asked for proposals on. Before M7 and M8 so that the two new
Settings options they add are written into a menu that already explains itself.

**Deliverable.**

- **Inspect tree moves above Browse** in the notebook menu.
- **One Compile, not two.** *Compile* and *Compile (force)* become a single
  **Compile** that rebuilds what is stale and reports what it did. This is
  correct only because M3 fixed #11; before it, the cached path could skip a
  stale file, which is what made a second option feel necessary. Force stays
  available as `idiomas compile --force`, which already exists, and deleting
  the cache is always safe.
- **A legend line under every menu.** A dim italic line below the option list
  showing the **highlighted** option's description, changing as the cursor
  moves — not a static block, and not a suffix on the rows. Every menu in the
  app gets it from the one shared `MenuScreen`: the landing menu, the notebook
  menu, and Settings. *Browse* reads as "fuzzy-find a file by name, or filter
  by tag"; the rest are written in the same voice.
- [`../current/design.md`](../current/design.md)'s *Flat menus* section gains
  the legend as a standing convention, stated once — every menu added after
  this one is expected to carry descriptions, which is what makes M7 and M8
  cheap.

**Open for the spec conversation.** The exact wording of every option's
description, on all three menus. Whether the legend line lives inside the
backpanel with the list or below it, and how it coexists with the screens that
already carry a `FooterHint`. Whether the notebook menu also binds a key for a
forced rebuild, or force stays CLI-only. Whether a reserved line for the legend
is always present (so the layout never shifts) or only appears when a
description exists.

**Done when.** The notebook menu reads Enter vocabulary / Inspect tree / Browse
/ Compile; every option on all three menus shows a description as it is
highlighted; a rebuild after an in-app edit is picked up by the single Compile
option; `design.md` states the convention; the dev confirms by hand; and the
full test suite passes.

---

## M5 · Language kinds

The abstraction under the backlog's *Implement german* and *Implement add a
language*: the app currently hardcodes Chinese everywhere — `FUNCTIONAL_LANGUAGES
= {"Chinese"}`, a `hanzi`/`pinyin`/`gloss` triad in `models.py`, pinyin guessed
on every keystroke in Entry, one CJK font in the template. The backlog names the
split itself: **character-and-phonetic** (Chinese) and **alphabetical only**
(German, Italian, French, English, Spanish).

Its own milestone, and first of the three, because the alternative is writing
the abstraction once for German and again for the other four. **Nothing the user
sees changes in this milestone**: Chinese is refactored onto the new shape and
behaves identically.

**Deliverable.**

- **A language kind is a first-class thing** — a small module describing, per
  kind: how many word fields an entry has and what they are called, whether a
  phonetic field exists and whether it is auto-filled, and which font the
  renderer uses.
- **Chinese is expressed in it and nothing else changes.** The existing
  behaviour — hanzi with pinyin guessed from it, the three-column vocabulary
  table, the stacked grammar triads, Songti SC — is reproduced exactly, verified
  against the dev's real tree by compiling it before and after and diffing.
- **Every hardcoded Chinese assumption is routed through it**, including
  `config.FUNCTIONAL_LANGUAGES`, the wizard's `LANGUAGE_CHOICES`, Entry's
  pinyin auto-fill, and `compile.py`'s per-language font, so that M6 adds a
  language rather than editing ten call sites.
- **The parser and writer stay compatible with every existing file.** The
  storage format does not change in this milestone; the dev's tree parses to
  identical decks before and after, as Sprint 5 M5 verified for the grammar
  flag.

**Open for the spec conversation.** The big one: `models.Entry`'s field names.
The backlog says German has "no equivalent to hanzi, so the text field should
not appear" — which of the two Chinese word fields an alphabetical language's
single word occupies, and whether `hanzi`/`pinyin` are renamed to something
kind-neutral or kept and reinterpreted. That decision reaches the parser, the
writer, every screen and every existing file on disk, so it is settled here and
not in M6. Also: whether a kind is data or a class; whether a language's kind is
stored in the config or derived from a built-in table; and whether "functional"
survives as a concept at all once German works.

**Done when.** Chinese behaves exactly as before by hand and by test; the dev's
real tree compiles to byte-identical PDFs across the refactor; adding a language
of an existing kind is demonstrably a table entry rather than a code change; and
the full test suite passes.

> **Corrected 2026-10-01, while speccing M5.** "Byte-identical PDFs" can't be met
> even by a change that does nothing: pandoc runs xelatex in a fresh temporary
> directory each time, and that path ends up in the output, so two compiles of
> the same markdown differ in about 14,000 bytes. The bar is met instead by
> identical input to pandoc (markdown, command line and stamp, for every file in
> the dev's tree) and pixel-identical rasterised pages. See
> [`features/M5-2026-10-01-language-kinds/requirements.md`](features/M5-2026-10-01-language-kinds/requirements.md),
> *A correction to the roadmap's done-when*.

---

## M6 · The German notebook

The backlog's *Implement german*: "keeping the same ideas from chinese", with no
hanzi equivalent and its own rendering, recycling from Chinese rather than
duplicating it — "if necessary you can create new classes only if they add more
functionality than complexity". German has been registered-but-inert since
Sprint 4 and explicitly out of scope in Sprint 5; this is where it stops being a
placeholder.

**Deliverable.**

- **German is functional.** Choosing it on the landing menu opens the notebook
  menu, not `PlaceholderScreen`. `FUNCTIONAL_LANGUAGES` — or whatever M5 leaves
  in its place — includes it.
- **Entry shows the right fields.** The character field does not appear, nothing
  is auto-guessed, and there is no read-only phonetic field to tab past. Field
  order, tab behaviour, the create-and-clear loop, the tree of
  categories/uncategorized/new-category, and the grammar panel's subtitle field
  all behave exactly as Chinese's do.
- **The renderer renders German.** A vocabulary deck and a grammar deck both
  compile, with a layout derived from Chinese's but without the pinyin row: the
  grammar renderer's stacked hanzi-over-pinyin unit has nothing to stack, so the
  block is redesigned rather than left with an empty row. Typography is
  German's own — Sprint 5's Postponed table flagged per-language typography as
  the open question, and one CJK face for the whole app is not the answer here.
- **Input-method switching keeps working.** German's config already stores both
  sources and has since Sprint 4 M6; they stop being stored-and-unused.
- **No Chinese regression.** Every Chinese behaviour and PDF is unchanged, on
  the dev's real tree.

**Open for the spec conversation.** What a German entry's row looks like on
disk, which follows from M5's field decision. What the German vocabulary table
and grammar block actually look like — two columns, or two with the note
convention retained. Which typeface. Whether a German file's storage format is
distinguishable from a Chinese one by a reader, or only by which tree it lives
in. Whether the grammar folder convention applies to German at all.

**Done when.** The dev creates German vocabulary and grammar entries by hand in
the real app, compiles both, and approves the PDFs by eye; no Chinese PDF
changes; and the full test suite passes.

---

## M7 · Add a language

The backlog's *Implement add a language*: a list of possible languages, all
falling into one of M5's two kinds, with **Italian, French, English and Spanish**
added for now — all alphabetical, i.e. all German-shaped. "I suppose this means
the wizard will also change."

**Deliverable.**

- **A registry of supported languages**, each with its kind: Chinese
  (character-and-phonetic); German, Italian, French, English, Spanish
  (alphabetical). One list, read by both surfaces below.
- **The wizard offers all six**, replacing today's hardcoded
  `LANGUAGE_CHOICES = ["Chinese", "German"]`, still requiring at least one, and
  still asking the per-language input-method questions for each chosen.
- **Settings › Add a language is real.** It registers a language that was not
  chosen at install time: writes it to the config, creates its `tree-<Language>`
  folder, asks the same input-method questions with the same widgets and the
  same wording the wizard uses — `design.md`'s standing rule that a setting the
  wizard asks for is a setting Settings can change — and the language appears on
  the landing menu without relaunching, as Sprint 4 M6's input-method change
  already does.
- **Every alphabetical language works on arrival**, because M5 and M6 did the
  work: adding Italian is a registry entry, and its Entry screen and PDFs come
  out right with no per-language code.
- The new Settings option carries a legend description, per M4.

**Open for the spec conversation.** Whether a language already registered is
hidden from the list or shown disabled. What happens when its tree folder
already exists on disk. Whether the registry is extensible by the user (a config
list) or fixed in code for now. Whether adding a language can be undone from the
same screen or only through M8.

**Done when.** The dev adds a language from Settings in the running app, sees it
on the landing menu without relaunching, enters a word into it and compiles it;
a fresh wizard run offers all six; and the full test suite passes.

---

## M8 · Remove a language

The backlog's *Implement remove a notebook* — "the opposite operation, not much
to add" — and the second of Settings' two long-standing placeholders. Settled at
sprint start as removing a **registered language**, the true opposite of M7, not
a second path for deleting a single file (Inspect Tree's `d` already does that).

**Deliverable.**

- **Settings › Remove a notebook removes a language**: drops it from the config
  so it stops appearing on the landing menu and in Settings' input-method list.
- **Notes are never deleted without a separate, explicit confirmation.** The
  language's `tree-<Language>` folder is a directory of the user's own files;
  unregistering it and deleting it are two different intentions, and the second
  is asked for separately through the app's existing `ConfirmDialog`, whose
  `enter` is deliberately unbound.
- **Removing the last language is handled**, not crashed into: the landing menu
  with nothing on it has never existed.
- **It takes effect in the running app**, same as M7's addition.
- The option carries a legend description, per M4.

**Open for the spec conversation.** Whether the folder-deletion question is
offered at all or the folder is always left on disk. What happens to the
language's compiled PDFs and its entries in the compile cache. Whether the last
language can be removed at all, or the screen refuses. Whether the option's
label stays "Remove a notebook" now that it removes a language — the backlog and
the existing UI both call it that.

**Done when.** The dev removes a language in the running app and sees it leave
the landing menu without relaunching; their notes are still on disk unless they
explicitly asked otherwise; re-adding it through M7 restores it; and the full
test suite passes.

---

## M9 · Manual editing checks

The backlog's *Manual editing*: "Modifying manually an md file should be always
checked. It is only checked when it is modified through the app." Last, because
it validates everything the rest of the sprint built — Chinese and German files
alike — and stands on M1's parser fixes and M2's escaping.

The starting position, established at sprint start: `parse()` **already**
produces a `Warning` for every line it cannot read, and **every caller discards
it** — `store.py`, `compile.py`, Entry, Inspect Tree all write
`deck, _ = parse(...)`. Nothing is checked anywhere today, in-app edits
included. The machinery exists; this milestone connects it.

Also settled at sprint start: warnings are **surfaced, never blocking**.
`mission.md` requires that the program "never silently discard a line it did not
expect" — it requires reporting, not refusal, and a file with a warning still
compiles.

**Deliverable.**

- **Good-faith edits are picked up.** A category added by hand, an entry moved
  between categories, entries or categories reordered, a tag added — all of
  these already parse and round-trip correctly. What is missing is the app
  noticing: a file changed on disk is re-read, and the trees and the Entry
  form's category list reflect it without relaunching.
- **Bad-faith edits are visible.** A markdown table, a line of prose, a row with
  fewer than two tabs, a header that does not match the filename — each already
  becomes a `Warning`. The offending file is marked in the tree, and its
  warnings are readable from the app, with line numbers and the raw line.
- **`idiomas compile` reports warnings** rather than silently rendering a file
  with lines missing from it.
- **Nothing is blocked.** A file with warnings compiles, opens, and can be
  edited; the warning is information, not a gate.

**Open for the spec conversation.** How a changed file is detected — mtime on
tree rebuild, a watcher, or a re-read on focus. What "marked in the tree" looks
like and where the warning list is read (the preview pane, a modal, a footer
count). Whether the same treatment applies to files edited through the app,
which can now only produce warnings via M1's leftovers. Whether a warning count
appears anywhere at a glance. Which of the report's parser findings are already
warnings by then and which still need one.

**Done when.** A category added to a file in an external editor appears in the
app without relaunching; a hand-added markdown table shows as a warning naming
its line, and the file still compiles; `idiomas compile` prints warnings; the
dev confirms by hand-editing files in their own tree; and the full test suite
passes.

---

## Not in this sprint

For the second sprint running, **nothing from the backlog is deferred** — all
five of its feature sections, plus its *Bug fixes* pointer at the review, are on
the roadmap above.

What is out, and recorded in
[`guidelines/notes-sprint-6.md`](guidelines/notes-sprint-6.md)'s Postponed
table:

- **The three answers to the backlog's own *Brainstorming* question** — editing
  and deleting an existing entry, searching inside entries, and moving an entry
  between categories or files. Proposed at sprint start, and the dev chose to
  keep the sprint to its nine backlog milestones. They are the sprint's first
  candidates for the next backlog.
- **Windows support and WSL**, carried from Sprint 5 unchanged.
- **`doctor` checking the LaTeX packages the template loads**, carried from
  Sprint 5: on Arch a bare `texlive-xetex` passes `doctor` and then fails to
  compile.
- **Multi-page PDF preview** and **persisting the tag cache**, both carried from
  Sprint 5.
- **Brew packaging**, carried from Sprint 4 and Sprint 5 with the same standing:
  the documented `git clone` install works.
