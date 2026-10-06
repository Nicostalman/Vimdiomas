# Roadmap — Sprint 3

Sprint 2 fixed the entry screen. Sprint 3 is about everything around it: the
menus that get you there, and the trees the whole app reads. The source is
[`guidelines/backlog.md`](guidelines/backlog.md), written by the dev; the
decisions taken while turning it into this roadmap live in
[`guidelines/notes-sprint-3.md`](guidelines/notes-sprint-3.md).

Two naming conventions from the backlog hold throughout, and are used below
without further explanation:

- The **notebook menu** is the existing menu — *Enter vocabulary*, *Browse*,
  *Compile*, *Inspect tree*.
- The **landing menu** is new, and comes before it: one entry per language, plus
  *Settings*.

Milestones are ordered on one principle: **the ground before what stands on it.**
M1 changes where every file in the project lives, so nothing that reads a path
can precede it. M3 extracts the tree widget that M4 and M5 build on. The two
milestones that depend on neither — the landing menu and the PDF format — sit
where they are cheapest to run: one early, one last.

Each milestone lists its deliverable and the condition that closes it.

---

## M1 · One tree per language

The backlog's *Trees rework* and *Git treatment*, together — both are the same
file move.

`source/` and `notebook/` were two mirrored trees because the app was meant to be
auxiliary to the filesystem. That premise is gone: this sprint gives the app the
means to edit files without leaving it, so one tree is enough.

**Deliverable.**

- `source/` and `notebook/` merge into a single `tree-Chinese/`, **flat**:
  `tree-Chinese/Vocabulary/Food.md` and `tree-Chinese/Vocabulary/Food.pdf` sit
  side by side. The `md/`/`pdf/` subfolder split the backlog floated is
  deliberately not taken — see the Decisions table.
- `Config`'s `source_root` and `notebook_root` collapse into one `tree_root`,
  named from `Config.language`. The dev's existing `.idiomas.toml` must not be
  left broken; whether M1 migrates it silently or re-prompts is a decision for
  `plan.md`.
- `compile.py`'s source→notebook path mapping becomes suffix substitution within
  one tree. `browse.py`, `entry.py` and `doctor.py` follow.
- **The visual trees do not change.** The entry screen's tree still shows `.md`
  files with their categories as leaves and still reads `Chinese notebook` at the
  root; the user should not be able to tell from the UI that anything moved.
- `tree-Chinese/` is untracked: `git rm --cached` for what is tracked today, plus
  a `.gitignore` entry. Already-pushed history is **not** rewritten — the dev's
  explicit choice, with the consequence recorded in the notes. The tree stays on
  disk locally, for testing.
- The location stays at the project root. Moving the trees out of the source-code
  directory is the installation wizard's job and is out of scope.

**The testing question is already answered.** Sprint 2 blocked this on "what do
the tests read?" — every test in `tests/` builds its trees under pytest's
`tmp_path`, so nothing reads the real trees and untracking breaks no test. This
was verified during the sprint-start conversation.

**Done when.** The dev's real notebook lives in one `tree-Chinese/` with `.md`
and `.pdf` beside each other; `git status` shows nothing from it; entering
vocabulary, browsing and compiling all work against the merged tree; the entry
screen looks exactly as it did before; and the full test suite passes.

---

## M2 · Landing menu

The backlog's *Landing menu*. Independent of the tree work, so it can run early.

**Deliverable.**

- A new screen shown at launch, before the notebook menu: one entry per language
  plus *Settings*. With Chinese and German registered, that reads *Chinese
  notebook*, *German notebook*, *Settings*.
- *Chinese notebook* opens the existing notebook menu, against `tree-Chinese/`.
- *German notebook* is an inert dummy. Multi-language plumbing is not built this
  sprint.
- *Settings* opens a submenu whose items are **all dummies** — add a language,
  remove a notebook, and whatever else fits. The backlog says implementation is
  not expected outright; the wizard owns the data these would write.
- `q` on the landing menu exits the app; `q` on the notebook menu now returns to
  the landing menu rather than exiting. This moves the "root screen" that
  `MainMenuScreen.action_back_or_quit` currently owns, so
  [`../current/design.md`](../current/design.md)'s navigation section is updated
  in place.

**Open for the spec conversation.** The menu is built to hold N languages but fed
a hardcoded two. Whether the list comes from a constant, from `Config`, or from
whatever the wizard will eventually write is a `plan.md` decision — the backlog
only requires that German be inert.

**Done when.** Launching the app lands on the language menu; *Chinese notebook*
reaches the notebook menu and `q` comes back; *German notebook* and every
*Settings* item are visibly present and do nothing; `q` on the landing menu
exits; and `design.md` reflects the new screen order.

---

## M3 · One tree widget

Not a feature — the refactor M4 and M5 stand on. The backlog asks for it
directly: *"I may want to change the layout of every tree in the app at the same
time in the future, so it would be nice if I could manage all of them from the
same place."*

**Deliverable.**

- The tree behaviour and styling currently living in `EntryTree` is extracted
  into a shared base widget with a single home, alongside the existing
  `NavigableScreen`/`VimOptionList`/`PanelAwareInput` family in
  `tui/screens/base.py` (or a module of its own — `plan.md`'s call).
- `EntryScreen` adopts it and is **visually and behaviourally identical**. This
  is the milestone's whole risk: a refactor that changes what the user sees has
  failed.
- The base carries what every tree in the app shares — the aesthetic of the entry
  screen's left panel, the vim keys, no horizontal scrollbar, content-sized
  view — and leaves what differs to subclasses. The difference M4 needs: entry's
  leaves are the *categories inside* a file, while Inspect Tree's leaves are the
  *files themselves*.
- The convention is recorded in [`../current/design.md`](../current/design.md), so
  the "one place to change every tree" promise is documented, not just implied by
  the code.

**Done when.** `EntryScreen`'s tree renders identically to before — verified by
the dev's own eye, not only by the tests; `tests/test_tui_entry_screen.py` passes
unchanged where it can; the base widget is documented in `design.md`; and no tree
styling remains duplicated outside it.

---

## M4 · Inspect Tree, functional

The backlog's *Notebook menu: make Inspect Tree functional*. Both of Sprint 1's
placeholder entries collapse into one working screen.

**Deliverable.**

- The notebook menu's **Notebook** entry is removed. *Inspect tree* absorbs it.
- Inspect Tree opens a real tree — built on M3's base widget, leaves are files —
  with two modes:
  - **PDF mode**, always the default on entry. Opening a file opens its PDF.
  - **MD mode**, reached with `tab`. Opening a file opens the `.md` in vim,
    inside the same terminal.
  - `tab` alternates between them. The mode is **not persistent**: leaving and
    re-entering always starts in PDF mode.
- Saving an `.md` with changes from vim triggers a recompile of that file.
- The screen obeys the navigation conventions in
  [`../current/design.md`](../current/design.md) like every other screen — `tab`
  is the only key this milestone adds.

**Open for the spec conversation.** Three things the backlog leaves open, to
settle in `plan.md`: how vim is hosted inside a running Textual app
(`App.suspend()` is the expected route, unverified on the dev's terminal); what
"open the pdf" means concretely (handing it to the OS viewer, macOS-first, in the
spirit of Sprint 2's M4); and how "saved with changes" is detected — vim's exit
code, an mtime comparison, or a content hash.

**Done when.** *Inspect tree* opens the merged tree in PDF mode; `enter` on a
file opens its PDF; `tab` switches to MD mode and `enter` there opens vim in the
same terminal; quitting vim after a save leaves an up-to-date PDF with no visit
to *Compile*; leaving and re-entering starts in PDF mode again; and *Notebook* is
gone from the notebook menu.

---

## M5 · Editing the tree from inside the app

The backlog's *further functionality for inspect tree*. This is the milestone
that makes M1's premise true — the app can now modify files without the user
touching the filesystem.

**Deliverable.** Five keys on the Inspect Tree screen:

| Key | Action | Notes |
|---|---|---|
| `d` | Delete the file or directory under the cursor | Asks *are you sure*, answered `y`/`n`. Never deletes without it. `enter` does nothing in this dialog — only `y` confirms. The removal is aesthetic while the screen stays open (hidden from the tree, undoable with `u`); the real filesystem removal happens only when the screen is left. |
| `r` | Rename the file or directory under the cursor | Prompts for the new name, pre-filled with the current one. |
| `n` | Create a directory | Always at the top level — directories cannot be nested, so the cursor's position is irrelevant. |
| `m` | Create a file | In the directory under the cursor; if the cursor is on a file, in that file's directory. |
| `u` | Undo the most recent pending delete | Only undoes deletes still pending in this visit to the screen — once the screen is left and the delete is committed to disk, it's final. |

- Deleting or renaming an `.md` must keep its `.pdf` consistent — the two now
  live side by side in one tree, and a stale PDF beside a renamed source is
  exactly the confusion M1's merge was meant to end. Renaming also rewrites the
  `.md`'s own `# Title` header line to match, and recompiles the `.pdf` if one
  existed — a renamed file that still opens to its old title defeats the
  point.
- The `y`/`n` confirmation and the rename/create name prompt are a new
  interaction shape for this app; both are one reusable, centered modal-dialog
  family, recorded in [`../current/design.md`](../current/design.md), not
  invented per keypress.

**Done when.** A directory and a file can be created, renamed and deleted end to
end from Inspect Tree without leaving the app; `d` never destroys anything
without a `y`, and `enter` never accidentally does; a pending delete can be
undone with `u` before the screen is left, and is permanent after; deleting or
renaming an `.md` leaves no orphaned, misnamed, or mistitled `.pdf`; and `n`
refuses to nest.

---

## M6 · PDF format rework

The backlog's *Latex/pdf format rework*. Touches only `compile.py`'s
`render_markdown` and `templates/xecjk.tex`, so it blocks nothing and is parked
last.

**Deliverable.** What the backlog states plainly:

- The list sits on the **left** of the page, not centred.
- The underlying table stays — it gives better alignment than tabs — but becomes
  **invisible**: no rules, no header row on show.
- A **bigger font size**.
- The LaTeX character of the output is kept. It is the part the dev likes.

**This milestone starts with an interview.** The dev asked for one explicitly and
the backlog is a direction, not a specification: "the list on the left side of
the screen" needs pinning down (left-aligned columns? a narrow column against a
wide margin?), as does how the three columns read once their header row is gone.
No `requirements.md` before that conversation.

**Done when.** The dev looks at a recompiled `Food.pdf` and says it is right.
There is no other bar for this one.

---

## Not in this sprint

The dev's standing deferred list lives in their own `postponedfeatures.md` and is
theirs to manage. This roadmap is written from `backlog.md` alone: nothing from
Sprint 2's *Later* list is inherited here by default, and git treatment appears
above only because the dev put it in the Sprint 3 backlog themselves.

Two things the backlog names and explicitly holds back:

- **The installation wizard**, which is where the trees get their real location,
  where languages are registered, and where input methods stop being hardcoded.
  The backlog says the trees "will be created during the installation phase, but
  this will not be touched on this sprint."
- **Real multi-language support.** German is a dummy entry on the landing menu
  and nothing more.
