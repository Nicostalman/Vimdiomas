# Mission

## The problem

Chinese lessons produce vocabulary and grammar faster than a word processor can absorb it. Kept in `.docx`, notes become:

- **Unsearchable across files.** Finding every word tagged as travel vocabulary means opening documents one by one.
- **Hard to reorganize.** Moving 番茄 from *Vegetables* to *Fruits* is a cut-and-paste ritual through a formatting engine that fights back.
- **Unstructured.** Nothing enforces that every word has a hanzi, a pinyin, and a translation. Entries drift into inconsistency.
- **Slow to fill.** Adding a word mid-lesson costs more attention than the lesson can spare.
- **Opaque.** A `.docx` is a zip of XML. It does not diff, it does not grep, and it is not readable without its application.

## The principle

**Notes are a directory tree of plain text; the polished artifact is generated, never edited.**

Two mirrored trees:

- `source/` — the **editing** tree, holding `.md` files in a rigid, hand-editable format. This is the truth.
- `notebook/` — the **main** tree, holding the `.pdf` files compiled from them. This is the artifact.

Every organizational decision — what the top-level directories are, which topic a file covers, which categories live inside it — is the user's, expressed as directory and file structure rather than as a scheme imposed by the program.

Three properties follow from this and are non-negotiable:

1. **The files stay legible and editable by hand.** A text editor is always a valid tool for this data. The program must read back anything a reasonable hand-edit produces, and must never silently discard a line it did not expect.
2. **The program owns formatting, the user owns order.** Ordering of categories and entries is meaningful and is preserved exactly as found. The program only enforces structural invariants — the tags block last, the header matching the filename.
3. **Entry is fast enough to do during a lesson.** Adding a word is type, Tab, Tab, Enter — no navigation between words that belong together, no mouse.

## Who it is for

One language learner keeping their own notes, working in a terminal on macOS or Arch Linux. Chinese first; the format and the tree carry over to other languages without redesign.

## What "done" looks like

- Vocabulary and grammar live in `source/` as `.md`, organized in a tree the user defined.
- `vimdiomas` opens a terminal app where a new word can be filed into any topic and category in seconds, with pinyin prefilled from the hanzi.
- Files are findable by fuzzy name match and filterable by tag.
- One command compiles the whole tree into `notebook/` as PDFs with properly typeset hanzi and tone-marked pinyin.
- A word processor is never opened again for this purpose.

## Non-goals

These are deliberately out of scope. They are not oversights.

- **Not a flashcard app.** No spaced repetition, no scheduling, no review queue, no quiz mode. Anki exists.
- **Not a dictionary.** Definitions are what the user wrote in class, not what a corpus says. The only automatic lookup is pinyin from hanzi, and it is always overridable.
- **Not multi-user.** No sync, no server, no accounts, no conflict resolution. One person, one machine, one tree.
- **Not a general markdown editor.** The program handles one narrow file format. Freeform prose belongs in a text editor.
- **Not a formal specification.** This document states intent. [`design.md`](design.md) states the file-format standard hand edits are checked against, `roadmap.md` is the schedule.
