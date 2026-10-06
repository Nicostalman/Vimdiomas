# Roadmap — Sprint 7

Sprint 6 made the app a language app: six languages of two kinds, all 19
findings of the bug report fixed, and hand edits checked against the format the
app writes. Sprint 7 is the sprint that **makes the project public**. It ends
with one public GitHub repo, a README written for someone installing the app,
and the feature a public user will expect most: finding a word. A second
feature, taking words into Anki, was planned as M4 and dropped on 2026-10-04
(see M4).

The backlog is [`guidelines/backlog.md`](guidelines/backlog.md). It is a copy
of the dev's `postponedfeatures.md` and, by a decision taken at sprint start,
**it is never committed**, so the link resolves only on the dev's machine.
Every one of its five sections is on this roadmap. One item joins from Sprint
6's Postponed table, by the dev's choice: the curly-quote spacing bug. That
made **six** milestones. M4 was then dropped, which leaves **five**. M4 keeps
its number so M5 and M6 keep theirs. The decisions behind them are in
[`guidelines/notes-sprint-7.md`](guidelines/notes-sprint-7.md).

The backlog opens with an instruction that applies to every milestone below:
"It is important the specs are as thorough as possible as to minimze
interaction with the dev during the implementation step." Each milestone's
*Open for the spec conversation* list below is the minimum its interview has to
close, not the whole of it.

The ordering principle is **process, then the app, then the docs, then
publishing**:

- **The skills come first** (M1). Two of the three fixes change how a sprint
  *ends* (the changelog is written at close, no branch is left behind), and
  Sprint 7 should end under the fixed rules rather than the old ones. The
  third, backlogs never committed, is what M6 relies on to publish safely.
- **The app changes go in the middle** (M2–M4), smallest first. The curly-quote
  fix is a template setting with nothing depending on it. Search and Anki
  export are independent of each other. Search goes first because it is a
  change to an existing screen with a known shape, while Anki export starts
  from "I'm not sure on the specifics of this". (M4 was later dropped.)
- **The README follows the code it describes** (M5), so its *Installing* and
  *Dependencies* sections describe the app as published.
- **Publishing comes last** (M6), because it publishes whatever is current. It
  follows the finished README and every code change.

Earlier sprints' vocabulary is used below without re-explaining it: a **menu**
is a screen whose content is a list; a **screen** opens from a menu; a screen is
a **backpanel** holding **panels** holding **content**; **MD mode** and **PDF
mode** are Inspect Tree's two preview modes, toggled with `tab`; a language's
**kind** is either Chinese (word, reading, translation) or alphabetical (word,
translation). See [`../current/design.md`](../current/design.md).

Each milestone lists its deliverable, what its spec conversation still has to
settle, and the condition that closes it.

---

## M1 · Fix the skills

The backlog's *Fix skills*, its three numbered items in one milestone. All
three edit the same four files under `.claude/skills/`, and none is big enough
to hand-test alone.

**Deliverable.**

- **Backlogs are never committed** (item 1). Settled at sprint start, with a
  single public repo: a backlog lives on disk in its `Sprint-N/guidelines/`
  folder and is gitignored. The ignore rule
  `specs/Sprint-*/guidelines/backlog.md` already landed with the sprint opening.
  This milestone does the rest:
  - It untracks Sprint 3–6's committed backlogs with `git rm --cached`. The
    files stay on disk.
  - `sprint-start` places the backlog without `git mv` and without staging it.
  - Every place that describes the backlog says it is local-only and needs a
    backup of its own: the skills, `specs/current/README.md` and `CLAUDE.md`.
- **Closing a sprint writes the changelog** (item 2). Today a sprint is folded
  into `changelog.md` only when the next sprint opens. Now the changelog is
  written when the sprint closes, and `sprint-start`'s gate checks that it was.
- **No loose local branches** (item 3). `feature-spec` step 9 already says to
  delete the branch locally and on the remote after the squash-merge, but
  branches have been left behind anyway. A squash-merged branch is not "merged"
  as far as `git branch -d` is concerned, so the delete can fail quietly. The
  fix makes the cleanup something that can be checked, not just an instruction.

**Open for the spec conversation.** What event closes a sprint, and so triggers
the changelog: the last milestone's merge in `feature-spec`, an explicit "close
the sprint" request, or a new skill. Whether `changelog` is still invoked by
`sprint-start` as a fallback. Where the loose-branch check lives: the end of
`feature-spec`, its start, `sprint-start`'s gate, or all three. Also whether it
prunes remote-tracking refs, and how it tells a squash-merged branch from
unmerged work, which must never be deleted. Whether Sprint 2's `motivation.md`,
Sprint 5's `image-1.png` and Sprint 6's `bug-report.md` count as backlogs and
are untracked with them. Whether the root `postponedfeatures.md` convention
(copied in, kept at root) is written into `sprint-start` as the standard
arrangement. How `kickoff`, which runs once and has already run, is touched, if
at all.

**Done when.** `git ls-files` lists no `backlog.md` (and none of the companions,
if those are in) and the files are still on disk. The four skills,
`specs/current/README.md` and `CLAUDE.md` agree with each other. A dry read of
`feature-spec` and `sprint-start` against this sprint's own close shows the
changelog written at close and no branch left behind. The dev reviews the skill
diffs.

---

## M2 · Curly-quote spacing

Carried from Sprint 6's Postponed table, where M3 found it: xeCJK treats `”` as
full-width CJK punctuation, so `a "b" c` in a title or heading prints as
`a “b”c`. It predates Sprint 6, and it is not one of the bug report's findings.

The template loads xeCJK only when the language's kind has a CJK face (Sprint 6
M6), so **only Chinese notebooks are affected**. German and the other
alphabetical languages never load it.

**Deliverable.** A closing curly quote followed by a space keeps the space in a
Chinese PDF, in a title, a heading, a category and an entry. The fix is a
setting in `src/idiomas/templates/xecjk.tex` (xeCJK's punctuation classes, or
equivalent), with no change to the markdown or the parser. Alphabetical PDFs
come out byte-for-byte as before. Sprint 5 M2's staleness rules make every
Chinese file rebuild on the next Compile, because the template changed.

**Open for the spec conversation.** Which other characters behave the same way
and are fixed in the same change: `’` as an apostrophe (`don’t`), the opening
quotes, `—`, `…`. The fix must not change how a genuine full-width `“”` around
hanzi is spaced, and the spec needs a test that pins that down. How the fix is
verified, given that the bug is in xelatex's typesetting rather than in
anything the Python produces. Text extraction from the compiled PDF is the
likely check, if it preserves the space reliably.

**Done when.** A Chinese file with `a "b" c` in a heading and in an entry
compiles with the space intact, checked by an automated test. The dev's real
Chinese notebooks recompile with no visible change except the restored spaces,
and the dev confirms by eye. The full test suite passes.

---

## M3 · Search by content

The backlog's *Search for entries*. Browse gets two modes, "analogous to md
and pdf modes" in Inspect Tree:

- **Search by filename**, the default, is today's Browse: fuzzy match on PDF
  names, filtered by tag, and Enter opens the PDF.
- **Search by content** finds category names and entries "in any format
  (hanzi, pinyin, translation, or equivalent)". For an alphabetical language
  that means the word and the translation.

`mission.md`'s first problem bullet is "Unsearchable across files", and this
milestone is where that is finally answered.

**Deliverable.** A mode switch on Browse. In content mode, a query matches
across every field of every entry and every category name in the notebook's
tree, grammar files included. Each result says where it was found, and
selecting it takes the user there. The mode convention is written into
`design.md` once, since Browse is now the second screen with modes.

**Open for the spec conversation.**

- **The key.** Inspect Tree toggles modes with `tab`, but in Browse `tab`
  cycles the filename field, the tag field and the results. One of them has to
  move, and whichever moves becomes the design convention.
- **What a result looks like.** An entry row with its file and category, a
  category with its file, or grouped by file. Whether its note shows. How many
  results show before the list scrolls.
- **What selecting a result does.** Open the PDF, as filename mode does. Open
  the source in MD mode at the line, through Inspect Tree's `nvim` path. Or
  jump to the file in Inspect Tree.
- **Matching.** Fuzzy (`store.fuzzy`, as filenames) or substring. Case and
  accents (`über` from `uber`). Pinyin: whether `ni`, `ni3` and `nǐ` all find
  你, and whether a tone-less query matches toned readings. Partial hanzi
  (`番` finds `番茄`).
- **Whether the tag filter applies in content mode**, and whether notes and
  tags are searchable content.
- **Speed.** Content mode parses every file. Whether that needs a cache, and
  whether Sprint 5's postponed *persisting the tag cache* item becomes part of
  this milestone.

**Done when.** In a Chinese notebook, searching by a hanzi, by its pinyin and
by its translation each find the same entry. In the German notebook, the word
and its translation each find theirs. A category name finds the category.
Selecting a result does what the spec settled on. Filename mode behaves exactly
as Browse does today. The dev confirms on their own trees, and the full test
suite passes.

---

## M4 · Anki export — dropped

**Dropped on 2026-10-04, before its spec.** The dev: the item was on the
backlog because the agent suggested it, not because they needed it. Most of
what was still open was a matter of taste in flashcards (card faces, tone marks,
deck layout), and only someone who studies with Anki can settle that. M4 would
also have added the sprint's only new dependency just before the project goes
public. Nothing was branched or specced. The text below is kept as it was
planned, in case the feature comes back. See
[`guidelines/notes-sprint-7.md`](guidelines/notes-sprint-7.md), *Settled in M4*
and Postponed.

The backlog's *Anki export*: "I'm not sure on the specifics of this." So the
spec conversation starts from the shape of the feature, not from its details.
The roadmap fixes only the deliverable: a notebook's entries become Anki cards
the dev can import and study.

**Deliverable.** An export that turns a notebook's tree, or part of it, into
something Anki imports. Running it again after adding words updates the
imported deck rather than duplicating it.

**Open for the spec conversation.**

- **Format.** A `.apkg` package (a new dependency such as `genanki`, which
  carries note models, deck structure and stable IDs) or a tab-separated text
  file for Anki's own importer (no dependency, but less control over decks and
  note types and weaker re-import behaviour).
- **Card shape per kind.** Chinese: which of hanzi, pinyin and translation go
  on the front and back, whether there is a reverse card, and whether pinyin is
  shown with tone marks. Alphabetical: word and translation, one card or two.
  Whether notes and tags carry over (tags map naturally to Anki tags).
- **Deck structure.** One deck per notebook, per file, or per category, or
  Anki's `::` subdecks mirroring the tree. Whether grammar files are exported
  at all, given that their rows are phrases under subtitles.
- **Scope and trigger.** The whole notebook, a file, or a category. A menu
  option on the notebook menu (with its legend line, per `design.md`), an
  `idiomas export` CLI command, or both. Where the output file goes.
- **Re-export.** Stable note IDs derived from the entry (its word? its
  file and category?), and what happens when an entry is edited or moved
  by hand.

**Done when.** The dev exports a Chinese notebook and the German notebook,
imports both into Anki, and studies a card from each. A second export after
adding a word adds one card on re-import and duplicates none. The full test
suite passes.

---

## M5 · README rewrite

The backlog's *Redo readme.md*: "It should only have the following sections:
Installing, Dependencies and Tutorial. The tutorial will be full of screenshots
so I'll do it manually."

Today's README has ten sections, from *What you need first* to *Developing*.
Settled at sprint start: **the Tutorial is an empty `## Tutorial` heading**,
left for the dev.

**Deliverable.** `readme.md` with a title and exactly three sections.
*Installing* covers `git clone`, the install, the first-run wizard, updating
and uninstalling. *Dependencies* covers what has to be on the machine and per
platform (pandoc, xelatex, the CJK packages and font only for Chinese, `nvim`),
and what `idiomas doctor` checks. *Tutorial* is an empty heading.

**Open for the spec conversation.** Where today's other content goes, if
anywhere: the file format (Sprint 6 M9 wrote it into the README as the standard
hand edits are checked against), the screen-by-screen *Using it*, *When
something stops working*, and *Developing*. The candidates are the Tutorial
(the dev's), `design.md` or `stack.md` (but `specs/` may not be published, see
M6), a second doc file, or nowhere. Whether the clone URL in *Installing* is
the public repo's, which does not exist until M6. Whether Sprint 6's
postponed note about `doctor` missing LaTeX packages is answered here by naming
them under *Dependencies*.

**Done when.** The README has exactly the three sections, *Tutorial* is empty,
and following *Installing* on a clean machine (or the Sprint 5 M7 Linux
container) installs a working app. The dev reads it and approves.

---

## M6 · Publishing

The backlog's *Publishing*: "Create a new repo with what's current, preventing
leaks. The only exception of what's current is the individual sprints
backlogs, these should not be published."

Settled at sprint start:

- **One repo, public.** The dev removes the current private origin afterwards.
- **No history.** The public repo's first commit is the current tree.
- **Backlogs are excluded by M1.** They are untracked and gitignored, so they
  are not in the tree that gets published.

**Deliverable.** A public GitHub repo whose single commit is the current tracked
tree, minus whatever else the spec rules out, and that passes a leak check. The
local clone is then working against it as `origin`, and feature work after
this point opens its PRs there.

**Open for the spec conversation.**

- **What else the tree drops.** The dev said there are more things they want
  removed. Candidates: the SDD tooling (`.claude/skills/`, `CLAUDE.md`), all of
  `specs/` or only its sprint folders, the sample notes under `source/`, and
  Sprint-local artifacts such as M5's `check_equivalence.py` and the Sprint 5
  typography comparison PDF.
- **The leak check.** What it scans for: the dev's email, absolute paths under
  `/Users/`, tokens, personal notes, `postponedfeatures.md`. Whether it is a
  one-off or a script kept for later.
- **Identity.** The author email on the root commit (a GitHub noreply address?)
  and on every commit after it. Whether the `Co-Authored-By` trailers stay.
- **The repo.** Its name, description and license. A license is the main thing
  that makes a public repo usable by others.
- **The local history.** After the switch, the local `main` holds 46 PRs of
  history the public repo does not. Whether it is rebased onto the new root,
  kept in a local archive branch or a bundle file, or dropped. If it is pushed
  anywhere, the leak comes back.
- **The order of the switch**, so there is never a moment when the only copy of
  the history is gone: publish, verify, re-point `origin`, and only then does
  the dev delete the private repo.

**Done when.** The public repo exists with one commit, the leak check over it
is clean, no backlog is in it, a fresh clone of it installs by M5's README,
and the local clone pushes to it. The dev then deletes the private repo
themselves.

---

## Not in this sprint

Every backlog section was put on the roadmap above, and one of them, *Anki
export*, was later dropped. What is out, and recorded in
[`guidelines/notes-sprint-7.md`](guidelines/notes-sprint-7.md)'s Postponed
table:

- **Anki export** (M4), dropped mid-sprint before its spec.
- **Editing, deleting and moving an existing entry in the app.** Offered as
  carry-overs from Sprint 6 and declined.
- **Windows support and WSL**, **`doctor` checking the LaTeX packages**,
  **multi-page PDF preview**, **persisting the tag cache** (unless M3 takes it)
  and **brew packaging**, all carried from earlier sprints unchanged.
- **A user-extensible language registry**, carried from Sprint 6 M7.
