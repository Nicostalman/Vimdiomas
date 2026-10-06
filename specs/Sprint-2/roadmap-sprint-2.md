# Roadmap — Sprint 2

Sprint 1 built the thing. Sprint 2 comes out of using it: every milestone below
traces to something that went wrong, or grated, during hand-testing with a real
notebook. The source is [`guidelines/motivation.md`](guidelines/motivation.md),
written by the programmer; the numbered proposals it was decomposed into live in
[`guidelines/agent-notes.md`](guidelines/agent-notes.md) and are cited here as
`#n`.

Milestones are ordered on one principle: **conventions before the screens that
obey them.** M1 changes key handling on every screen, so any screen work done
before it would have to be revisited.

Each milestone lists its deliverable and the condition that closes it.

---

## M1 · Navigation conventions

`#7`, `#8`, `#19`, `#20`, `#21`. One key map, applied everywhere, written down
once.

**Deliverable.**

- `h` `j` `k` `l` work wherever the arrow keys already do — in `OptionList` (main
  menu, browse results) and `Tree` (entry screen).
- `enter` chooses.
- `q` returns to the previous menu; on the main menu it exits the app. It must
  **not** fire while an `Input` has focus, or the letter cannot be typed.
- `shift`+`h`/`l` — and `shift`+`←`/`→` — moves between panels: tree ↔ form on
  the entry screen, and between browse's three stacked fields.
- Every `escape` binding is removed: `PlaceholderScreen.BINDINGS` and
  `EntryScreen`'s `focus_tree`.
- Leaving a screen with `q` must not lose work — saving and compiling happen on
  the way out. Edge cases are the implementer's call, but silent loss is not one
  of them.
- The conventions are recorded as a section of [`../stack.md`](../stack.md), so
  they are stated once and cited from then on rather than restated per feature.

**Open for the spec conversation.** Textual has no screen-level "an Input has
focus" guard inside `BINDINGS`. The likely shape is a shared base `Screen` (or a
mixin) holding the common bindings plus the focus check, rather than four copies
of the same list. Settle it in `plan.md`.

**Done when.** Every screen can be driven end to end with `hjkl`, `enter` and `q`
alone; `q` on the main menu exits; `q` inside a text field types a `q`; no
`escape` binding remains in the codebase; and `stack.md` carries the key map.

---

## M2 · Entry screen corrections

`#9`–`#16`. The screen works; the details are wrong. Almost entirely
`tui/screens/entry.py` and `tui/app.tcss`.

**Deliverable.**

- The form is inert unless the tree cursor sits on a valid target. Switching to
  the right panel off a leaf shows *choose a category* instead of editable
  fields. `_active_target` and `VALID_TARGET_KINDS` already draw the
  distinction — what is missing is gating focus on it.
- `(uncategorized)` appears under **every** file, not only files that already
  hold loose entries. This reverses an M5.2 decision from Sprint 1, deliberately.
- The tree root reads `[language] notebook`, not `source`. This needs a language
  to read: `Config` gains `language: str = "Chinese"`, which the future
  installation wizard will write and which defaults cleanly for the existing
  `.idiomas.toml`.
- No horizontal scrollbar under the tree; the view sizes to its content.
- The footer hint is rewritten for the M1 key map.
- A thinner input cursor than Textual's default block beam — a `.tcss` change,
  applied to every `Input` in the app, not only this screen.
- The pinyin field is read-only and skipped by `tab`, which runs hanzi →
  translation. The `_pinyin_touched` / `_last_prefilled_value` race guard becomes
  dead weight once the field cannot be typed into; remove it rather than leave
  it.
- `gloss` becomes `translation` in the UI: the widget id, the field order, the
  placeholder, and the tests that query `#gloss`. The `Entry.gloss` dataclass
  field and the on-disk format keep the old name — renaming those reaches the
  parser, the writer and every fixture, and buys nothing the user can see.

**Done when.** Twenty words still enter into one category without touching the
tree — Sprint 1's bar, unbroken; the right panel refuses focus off a leaf and
says why; every file offers `(uncategorized)`; `tab` never lands on pinyin; the
root reads `Chinese notebook`; and `tests/test_tui_entry_screen.py` passes as
amended.

---

## M3 · Autocompile

`#18`. The user should never have to remember to compile.

**Deliverable.** A file is compiled automatically when

1. at least one entry has been added to it and the cursor then moves to a
   different file — or to a category inside a different file; and
2. the entry screen is left altogether.

This needs per-file tracking of "has entries added since its last compile".
`_on_node_highlighted` already fires on every cursor move and is the natural
hook. Compilation is slow — pandoc through xelatex — and must not block typing;
whether it runs off the UI thread or is deferred is a decision for `plan.md`.

**Done when.** Entering a word in `Food.md`, moving the cursor to a category in
another file, and then leaving the screen produces an up-to-date `Food.pdf` with
no visit to *Compile*; a cursor move with no new entries compiles nothing; and
the UI stays responsive while a compile runs.

**Scope note (post-implementation).** Condition 1 (compile on cursor move to a
different file/category) was dropped during this milestone's spec discussion —
only condition 2 (compile on leaving the entry screen) was implemented. The
*Done when* bar above still holds as written, since the example scenario ends
with an up-to-date PDF regardless of what triggers the compile. See
[`guidelines/agent-notes.md`](guidelines/agent-notes.md) (#18 and the Decisions
table) and
[`features/2026-09-07-m3-autocompile/requirements.md`](features/2026-09-07-m3-autocompile/requirements.md)
for the rationale.

---

## M4 · macOS input-method switching

`#17`. Isolated on purpose: a new module, called from the entry screen, so the
platform-specific part has one home.

**Deliverable.** On macOS, focusing the hanzi field switches the system input
source to Pinyin Simplified; leaving it switches back to English
International. A no-op on every other platform, and a no-op — not a crash —
when an expected input source is not installed.

The MVP supports exactly these two keyboards, and only for the Chinese
notebook. The intended architecture is:

1. A future installation wizard asks the user to pick their **local**
   keyboard and their **international** keyboard.
2. That wizard is not built this milestone. Its two answers are hardcoded
   instead — `Pinyin Simplified` and `English International` — and only for
   Chinese, since Chinese is the only functional language. A different
   language would need a different hardcoded pair; nothing here generalizes
   across languages yet.

**Assumption on record.** The programmer states both sources are installed on
their machine. What happens when one is missing is undefined today; this
milestone is where it gets defined.

**Done when.** Typing hanzi on the programmer's machine needs no manual keyboard
switch; the app runs unchanged on a machine with neither input source installed;
and the switching module imports and tests without a Mac.

---

## Later

Considered for this sprint and deliberately left out, with the reason.

- **Entry screen real estate** (`#22`). The form panel's 5 fields + Create
  button don't all fit in a default-size terminal window — Create clips off
  the bottom until the window is enlarged. Raised by the programmer during
  M2 hand-testing, not from `motivation.md`. Needs a layout discussion
  (scrolling the form, shrinking field heights, a minimum-size guard, etc.)
  before it's scoped into a milestone.
- **Git treatment** (`#6`). Untrack `notebook/` and `source/` and purge what is
  already pushed — it is private content. Destructive, entangled with what the
  tests read, and explicitly postponed by the programmer while hand-testing is in
  progress. Needs the testing question settled and an explicit go-ahead.
- **Installation wizard** (`#1`–`#4`). PATH install, tree location, name,
  language selection, and the `[name]'s chinese notebook` greeting. The
  motivation document says to leave it last, and it is the least settled of the
  proposals. Now also covers local/international keyboard selection (`#23`),
  hardcoded for M4 ahead of the wizard's arrival.
- **Keyboard selection as a main-menu config option** (`#23`). Once the
  wizard (or M4's hardcoded pair) exists, let the user change their local and
  international keyboards later without re-running the wizard — e.g. a
  *Settings* entry on the main menu. Raised by the programmer during M4's
  spec conversation; not scoped, not started.
- **Multi-language support**. German as an inert menu entry, with no plumbing
  behind it. Waits for the wizard.
- **Seed content**. Sprint 1's M6, now dropped — hand-testing with a real
  notebook took its place. It interacts with `#6`: if the trees stop being
  tracked and nothing ships starter content, a fresh clone is empty by design.
- **Sprint 1's own deferred list** — entry editing and deleting, category
  renaming and deleting, tag editing, shell integration for *Notebook* and
  *Inspect tree*, watch mode, and search inside entries. Untouched, still
  deferred.
