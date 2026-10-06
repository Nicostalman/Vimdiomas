# Sprint 7 — notes

The agent-maintained companion to
[`../roadmap-sprint-7.md`](../roadmap-sprint-7.md): it records what was decided,
assumed, or postponed while the backlog was turned into that roadmap, and it
grows as the sprint runs.

**Where the backlog came from.** [`backlog.md`](backlog.md) is a **copy** of the
dev's root-level `postponedfeatures.md`, taken on 2026-10-03 and kept verbatim,
the same arrangement as Sprints 5 and 6: the root file stays theirs and goes on
being their living deferred list. Unlike those sprints' copies, **this one is
never committed.** It is gitignored from the day the sprint opened (see
Decisions), so the link above resolves only on the dev's machine.

**Sprint 6 closed cleanly.** All nine of its milestones, M1 through M9, were
specced, implemented and merged (PRs #38–#46). Nothing was dropped and no
milestone carries over. Its closing note and M9's settled decisions were written
into `notes-sprint-6.md` just before this sprint opened. The `changelog` skill
added Sprint 6 to `specs/current/changelog.md` in the same sitting, on `main`.

**What carries over from Sprint 6's Postponed table.** One item, by the dev's
choice: **the xeCJK curly-quote space**, which becomes M2. Searching inside
entries comes back through this backlog's own *Search for entries* section
rather than as a carry-over. The rest of that table stays out, and is restated
in this file's own Postponed table.

**The backlog's standing instruction.** It opens: "It is important the specs are
as thorough as possible as to minimze interaction with the dev during the
implementation step." This applies to every milestone this sprint. See the first
Decisions row.

## Decisions

Settled with the dev during this sprint-start conversation, on 2026-10-03.

| Decision | Rationale |
| --- | --- |
| **Every open question is settled in the spec conversation, not during implementation** | The backlog's opening line. Each milestone's `feature-spec` interview has to close everything the roadmap lists as open, plus anything found while reading the code, so implementation runs without stopping for decisions. A question that still comes up mid-implementation is a gap in the spec. Record it in the spec as it happens, and treat it as worth avoiding in the next milestone. |
| **Six milestones: the backlog's five sections, plus one carry-over** | *Fix skills*, *Search for entries*, *Anki export*, *Redo readme.md* and *Publishing* are each one milestone. The carry-over is Sprint 6's curly-quote item. Fix skills keeps its three numbered items in one milestone: they all edit the same four skill files, and none is big enough to hand-test alone. |
| **Order: process, then the app, then docs, then publishing** | Dev accepted the proposed order. M1 comes first so Sprint 7 itself closes under the fixed skills (changelog at close, no loose branches), and because M1 defines what "not published" means for M6. M6 comes last because it publishes whatever is current, so it should follow the finished README and code. See the roadmap's preamble. |
| **Anki export is in the sprint; its specifics are settled at spec time** | Dev's choice. The backlog says "I'm not sure on the specifics of this", so M4's spec conversation starts from format and card shape, not from a design. **Superseded:** M4 was dropped on 2026-10-04, see *Settled in M4* below. |
| **One repo, and it is public. The current private origin will be deleted** | Dev's statement: "i will remove the private repo, i dont want two separate repos." The project ends the sprint with a single public repo on GitHub. |
| **The public repo starts with no history** | Dev's choice, revised during the conversation: first filtered history, then "just publish without history". Every past commit carries a backlog, and stripping them commit by commit would mean auditing every past commit. A fresh root commit has nothing to audit but the current tree. *What* the current tree drops besides backlogs stays open for M6 (the dev said there are more things they want removed). |
| **Backlogs live on disk, gitignored, and are never committed** | Dev's choice from three, after it was explained that git cannot push a branch while holding back committed files. This is how backlog item *Fix skills* 1 ("kept in the local git but not be published") is met with a single public repo: the backlog stays in its `Sprint-N/guidelines/` folder on the dev's machine, the way `postponedfeatures.md` already does. Trade-off accepted: backlogs get no git history and need a backup of their own. |
| **The ignore rule `specs/Sprint-*/guidelines/backlog.md` was added to `.gitignore` at sprint start**, not in M1 | Otherwise this sprint's own backlog would have gone into the commit that opens the sprint, contradicting the row above on day one. M1 does the rest: it untracks Sprint 3–6's backlogs and changes the skills that place them. |
| **The README's Tutorial section is left as an empty heading** | Dev's choice. They write it themselves, with screenshots. M5 writes *Installing* and *Dependencies* only. **Superseded:** the dev filled it in during M5's review, see *Settled in M5* below. |
| **Sprint 6's curly-quote item is the only carry-over** | Dev's choice from three Postponed items offered. Editing, deleting and moving an entry stay postponed. |

### Settled in M1 · Fix the skills (PR #47, 2026-10-03)

| Decision | Rationale |
| --- | --- |
| **`changelog` is the skill that closes a sprint**: gate, closing note, `## Sprint N` section, one `Close Sprint N` commit on `main` | Backlog *Fix skills* 2. The close procedure is written in one place. `feature-spec` offers it after the roadmap's last milestone merges, the dev can ask for it at any time, and `sprint-start` runs it as a fallback. |
| **A sprint is closed when its `## Sprint N` changelog section exists** | That section is what `sprint-start`'s gate checks for. Closed is not frozen: a sprint freezes only when the next one opens. |
| **Branch cleanup is an exact sequence in `feature-spec` step 9, using `git branch -D`**, with no check anywhere else | Backlog *Fix skills* 3. The dev's diagnosis was that the cleanup was misspecified, not that it needed checking afterwards. `-d` refuses a squash-merged branch, and that refusal is how branches were left behind. |
| **`postponedfeatures.md` is the standard backlog source.** It is copied with `cp`, never staged, and confirmed with `git check-ignore` | Backlog *Fix skills* 1. Only `backlog.md` is local-only. Companions such as `bug-report.md` and `image-1.png` stay committed. Sprint 2's `motivation.md` counts as a backlog. |

### Settled in M2 · Curly-quote spacing (PR #48, 2026-10-03)

| Decision | Rationale |
| --- | --- |
| **The fix removes `\ignorespaces` from xeCJK's `\xeCJK_FullRight_and_Boundary:`**, guarded so a TeX Live without the macro compiles as before | Chosen over `LatinPunct`, `CheckFullRight` and a `Default` class, all measured and rejected (see M2's `requirements.md`). Genuine hanzi quotes keep identical layout. |
| **A typed space after any full-width punctuation is kept before a Latin character.** Before a hanzi it is unspecified | The macro does not look at which character it follows. CJK-to-CJK spacing varies by context and font (Songti SC vs Noto Serif CJK SC), and Chinese is not typed with spaces there. |
| **`…` is `Default` class**, so `...` prints as `…` and not `⋯` | Dev: "yes, fix it too". A real `……` now also prints the Latin glyph. |
| **A straight `"` in an entry is curled when the PDF is rendered, for every language**: word, translation and note, not the reading | Dev: "yes, add it to M2". The source `.md` is untouched. This is the one change to alphabetical PDFs. |
| **`--wrap=none` was not added to pandoc** | Measured: pandoc wraps only at the author's spaces, so it changed nothing. |
| **`–` (from `--`) was never affected** | Found at implementation, and pinned by a test. |

M2's `validation.md` §4 (the dev's check of real notebooks) was not reported to the agent before the merge. The dev asked for the merge directly.

### Settled in M3 · Search by content (PR #49, 2026-10-04)

| Decision | Rationale |
| --- | --- |
| **The tag field sits below the results panel**: query, results, tag | Dev, on the M3 branch before merging: "id like the field filter by tag be moved below the results panel". Changes §1's panel order, the `enter` chain (query → results when any, else tag; tag does nothing) and the J/K order. |
| **Category and subtitle rows show the bare name, in bold, with no `¶`** | Dev, from a screenshot: the `¶` read as a stray special character. Bold is what tells these rows from entries. `format_row` takes a `style`, applied to the fields only, so the location stays dim. |

### Settled in M4 · Anki export (dropped, 2026-10-04)

| Decision | Rationale |
| --- | --- |
| **M4 is dropped before its spec. No branch, no spec folder** | The dev: "honestly this is here because you suggested it". The agent offered three options: drop it, a minimal TSV `idiomas export` with no dependency, or the full `.apkg` export as planned. The dev chose to drop it. Most of what was open was a matter of flashcard taste that only a regular Anki user can settle. It would also have been the sprint's only new dependency (`genanki`), added just before M5 documents dependencies and M6 publishes. |
| **M5 and M6 keep their numbers** | Renumbering would break every M5/M6 reference already in this sprint's specs. The roadmap's M4 heading stays, marked dropped, with its plan text kept for if the feature returns. |

### Settled in M5 · README rewrite (PR #50, 2026-10-05)

| Decision | Rationale |
| --- | --- |
| **The README is a tagline plus *Tutorial and overview*, *Installing*, *Dependencies*, in that order** | The dev hand-edited the README after the agent's version: the Tutorial moved first, titled *Tutorial and overview*, with two screenshots and a line on Vim keybindings, all theirs. This supersedes the roadmap's "Tutorial is an empty heading". |
| **The dev cut *Updating* and the wizard's six-step list from *Installing*, and condensed it to one commented code block** | The dev's edit. The README no longer says how to update. If that is wanted back, it is a README change in a later sprint. |
| **The screenshots live in `docs/images/overview-{1,2}.png`** | They were untracked files at the repo root with macOS's default names. The agent moved and renamed them when taking in the edits. |
| **Docker instructions moved to `docker/README.md`; `mission.md` points at `design.md` instead of calling the README the contract** | Agent's proposals, taken in with the merge. The dev did not object in review. |
| **The clone URL stays `https://github.com/Nicostalman/Idiomas.git`** | Dev's choice at spec time. If M6 picks another repo name, M6 updates the README. |
| **Validation §3's interactive steps (wizard, new shell, add and compile) were not run** | The agent ran the three install commands and `doctor` in the Linux container. The dev merged on the strength of Sprint 5 M7, which exercised the same steps. |

### Settled in M6 · Publishing (PR #51, 2026-10-06)

| Decision | Rationale |
| --- | --- |
| **The app is renamed Vimdiomas**: package, command, config and cache folders, app strings, repo | The dev, when M6 started. A full rename, with `migrate_legacy_paths()` moving an older install's folders on first start. Closed sprints, this sprint's roadmap and M1–M5 specs, and past changelog sections keep the old name as records. |
| **The public repo is `Nicostalman/Vimdiomas`, GPL-3.0**, with the code as one commit on top of GitHub's *Initial commit* | The dev had already created it with the `LICENSE`. Two commits and no force-push, instead of the roadmap's "single commit". |
| **Everything tracked is published except the backlogs**: `specs/`, `.claude/skills/`, `CLAUDE.md` and the sprint artifacts included | The dev's choice. Sprint 2's `motivation.md` and Sprint 3–6's backlogs were untracked here (moved from M1), and `motivation.md` is ignored. |
| **Exception to the frozen-sprint rule: one line of Sprint 4 M4's `plan.md` is redacted** | The dev's choice. It held the dev's home path, the only leak the scan found. It now reads `/Users/you/...`. |
| **`scripts/leak_check.sh [ref [base]]` is kept and run before every public push** | The dev's choice. It reads its patterns from the machine at run time, so it holds nothing personal. `base` exists because at publish time the commit sits on the public repo's `main`, not the private one's. |
| **The old history is kept only in `~/Ego/Computing/idiomas-history.bundle`** | The dev's choice. Local `main` follows the public repo only. The public commits use the GitHub noreply email (local `user.email`). |
| **The migration ran on the dev's machine during implementation** | The agent's `uv run vimdiomas --help` went through `main()`. The config, its backups and the cache moved intact, and the agent made the `~/.local/bin/vimdiomas` link. Validation §4's app checks are still the dev's. |
| **Untracking deleted the backlogs from disk at the pull, and they were restored** | `git pull` applies a commit that untracks a file as a deletion in the working folder. Sprint 2–6's backlogs were restored from `e4df466`. One-off: since M1 no backlog is ever staged, so none is ever untracked again. |

### Sprint 7 closed (2026-10-06)

**Five of the six planned milestones landed**: M1, M2, M3, M5 and M6 (PRs
#47–#51). M4, *Anki export*, was dropped before its spec. The project is now
public as **Vimdiomas** at <https://github.com/Nicostalman/Vimdiomas>
(GPL-3.0). It has a rewritten README (the dev removed its *Dependencies* section in `becefef`, on the public repo), content search in Browse, and fixed
skills. The private `Nicostalman/Idiomas` repo is left for the dev to delete.
Its history survives in `~/Ego/Computing/idiomas-history.bundle`.

**Carried forward:** nothing as a milestone. The Postponed table below is what
the next sprint start should offer: Anki export, editing and moving entries,
Windows/WSL, `doctor` checking the LaTeX packages, multi-page preview,
persisting the tag and content caches, opening a result at its entry, wider
content search, brew packaging, a user-extensible language registry, the
legend overflow and the straight `'`. From now on, PRs go to the public repo,
and `scripts/leak_check.sh` runs before each push.

## Assumptions

Taken as given by this sprint; not verified in code or stated in the roadmap.

| Assumption | Origin | Notes |
| --- | --- | --- |
| **The private origin is not deleted until M6's public repo is verified** | Follows from it being the only off-machine copy of the history today | Deleting it also deletes PRs #1–#46 and their discussions on GitHub. The squash commits' messages survive in the local clone. Deleting it is the dev's action, not the agent's. M6's spec settles what happens to the local history. |
| **Until M6, milestones run as they always have**: a branch, a PR and a squash-merge on the private origin | No reason given to change it mid-sprint | M6's spec decides where PRs go afterwards. |
| **Backlogs need a backup of their own once untracked** | Follows from the backlog decision | Time Machine, iCloud or similar. The dev's responsibility, but M1 should state it wherever the skills describe the backlog. |
| **"Or equivalent" in *Search for entries* means an alphabetical language's word and translation fields** | The backlog: "in any format (hanzi, pinyin, translation, or equivalent)" | Since Sprint 6 M5, Chinese has three columns and every alphabetical language has two. M3 confirms. |
| **The dev has Anki installed to verify M4** | M4's done-when needs an import into a real Anki | Ask at M4's spec if not. **Moot:** M4 was dropped. |
| **Sprint 3–6's backlog companions are backlogs for this purpose** | Each exists only because a backlog references it: Sprint 2's `motivation.md` (the old name for the backlog), Sprint 5's `image-1.png`, Sprint 6's `bug-report.md` | **Settled in M1:** only `motivation.md` is a backlog. `image-1.png` and `bug-report.md` stay published. |
| **The dev hand-tests on macOS, as always** | Every sprint so far | Nothing here is platform-specific, except that M2's PDF check runs against the dev's real notebooks. |

## Postponed features / pending

Raised during the sprint and deliberately not implemented now. Deferred items
from the dev's own `postponedfeatures.md` are **not** duplicated here — that
file is the dev's and stays the record for them. Sprint 6's own Postponed table
stays where it is; only what this sprint carries is restated below.

| Item | Why postponed | Where it resurfaces |
| --- | --- | --- |
| **Anki export** (M4) | Dropped mid-sprint, before its spec: suggested by the agent, not needed by the dev (see *Settled in M4*). The roadmap's M4 section keeps the open questions. The cheapest version if it returns is a TSV `idiomas export` with no dependency, which Anki's importer can update by first field | If the dev or a user asks for it. |
| **Editing and deleting an existing entry in the app** | Offered as a carry-over from Sprint 6 and declined. Fixing a typo or a warned line still means `nvim` | The next backlog. |
| **Moving an entry between categories or files** | Same, and it builds on in-app editing | The next backlog, behind editing. |
| **Windows support** and **WSL** | Carried from Sprints 5 and 6 unchanged | Whenever someone needs it. |
| **`doctor` checking for the LaTeX packages the template loads** | Carried from Sprints 5 and 6: on Arch a bare `texlive-xetex` passes `doctor` and then fails to compile | Whenever a missing-package compile error shows up in practice. M5's *Dependencies* section now names them, but `doctor` still does not check for them. |
| **Multi-page PDF preview** | Carried from Sprints 5 and 6 | If a notebook grows past a page or two often enough to be annoying. |
| **Persisting the tag cache** and **the content index** (M3's in-memory `ContentIndex`) | Carried from Sprints 5 and 6. M3 added the content index, kept in memory only | If Browse feels slow on a large tree. M3's content search may make it more pressing, since it reads every file's entries. |
| **Opening the PDF at the entry's page, or the source at its line** | M3's content results open the file's PDF, not the position (requirements.md, Out of scope) | If the dev wants to land on the entry itself. |
| **Searching notes, tags or extra columns; fuzzy or ranked content matching; traditional ↔ simplified hanzi matching** | Out of M3's scope, by the dev's choice (requirements.md, Decisions) | If the dev asks for one. |
| **Brew packaging** | Carried from Sprints 4–6 with the same standing | A nice-to-have, unscheduled. It becomes possible once M6 makes the repo public. |
| **A user-extensible language registry** | Carried from Sprint 6 M7 | Unscheduled. |
| **Untracking Sprint 2–6's committed backlogs** (`git rm --cached`) **and the `motivation.md` ignore line** | Moved from M1 by the dev at merge | M6, before anything is published. Run M1's `validation.md` §1 checks. |
| **A menu taller than the frame can push its legend off-screen** | Carried from Sprint 6 M4. It never came up: the longest list is six options | M3 or M4 if either adds a long list. |
| **A straight `'` in an entry** (TeX prints it as `’`, wrong for an opening `'x'`) | A rule cannot tell `'x'` from `'tis` or `'90s`. Raised in M2, not asked for | If it shows up in a real notebook. |
