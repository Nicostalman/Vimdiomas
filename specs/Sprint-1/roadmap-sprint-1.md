# Roadmap

Milestones are ordered by dependency, not by visibility. The data layer comes first because everything else is built on the guarantee that a file survives a read/write cycle unchanged.

Each milestone lists its deliverable and the condition that closes it.

---

## M0 · Documentation and scaffold

**Deliverable.** `readme.md`, `mission.md`, `stack.md`, `roadmap.md`. `pyproject.toml` with a src layout, `.gitignore`, a venv, and the empty `source/` and `notebook/` trees.

**Done when.** `pip install -e ".[dev]"` succeeds and `python -m idiomas` starts and exits cleanly, even doing nothing.

---

## M1 · The data layer

The correctness backbone. `models.py`, `parser.py`, `writer.py`.

**Deliverable.**
- `Entry`, `Category`, `Deck` dataclasses.
- A parser tolerant of hand-editing: filename wins over a mismatched header; `Tags` recognized wherever it sits; any line with ≥2 tabs is an entry; an indented italic line is the note for the entry above; unrecognized lines are preserved verbatim and reported as warnings rather than dropped.
- A deterministic writer that enforces the structural invariants — header first, uncategorized entries before the first `##`, categories in existing order, `## Tags` always last and omitted when empty — and saves atomically via a temp file plus `os.replace`.

**Done when.** `parse(write(deck)) == deck` holds across fixtures covering notes, missing tags, missing categories, uncategorized entries and stray lines; and a file that is parsed and rewritten with no changes is byte-identical.

---

## M2 · Pinyin

**Deliverable.** `pinyin.py` with three pure functions: `to_tone_marks("ni3hao3") → "nǐhǎo"`, its inverse, and `guess("牛肉") → "niu2rou4"` via pypinyin. Accepts `v` and `u:` for `ü`; tone 5 and 0 are neutral and unmarked.

**Done when.** A conversion table of ~40 cases — every tone, `ü`, `ou`, `iu`, `ui`, neutral tones, multi-syllable words — passes in both directions.

---

## M3 · Discovery and search

**Deliverable.** `store.py`: `walk()` builds the tree (directory → file → category); `tag_index()` maps tags to files, cached by mtime; `fuzzy()` scores subsequence matches with bonuses for contiguous runs and word starts.

**Done when.** `fd` ranks `Food` above `Fried noodles`, and `tag_index()` finds a file by a multi-word tag.

---

## M4 · Compile

**Deliverable.** `compile.py` plus the xeCJK LaTeX template. Renders a deck to intermediate markdown with tone-marked pinyin and 3-column tables, runs pandoc through xelatex, and mirrors `source/` into `notebook/`, skipping PDFs newer than their source. A `doctor` command checks pandoc, xelatex, `xeCJK` and the CJK font, printing `sudo tlmgr install xecjk` when it is missing instead of a LaTeX traceback.

**Done when.** `python -m idiomas compile` produces `notebook/Vocabulary/Food.pdf` with hanzi rendered and `niu2rou4` shown as `niúròu`; and `doctor` gives an actionable message on a machine without xeCJK.

---

## M5 · The TUI

The point of the whole thing. `tui/`, styled with `app.tcss`.

**M5.1 — Main menu.** A focusable list: *Enter vocabulary*, *Browse*, *Compile*, *Notebook*, *Inspect tree*, *Quit*. *Notebook* and *Inspect tree* are placeholders that display their resolved path; changing the shell's working directory is out of scope.

**M5.2 — Entry screen.** A horizontal split: tree on the left, form on the right.

- The tree is at most three levels — directory → file → category. A file's children are `(uncategorized)` (present only when the file actually holds loose entries), then the real categories in file order, then `(new category)` always last.
- Directories and files are navigable but are **not** entry targets. The valid targets are a category, `(uncategorized)`, and `(new category)`.
- Selecting `(new category)` reveals a category-name field at the top of the form, hinting *"leave empty for no category"*. On create: a non-empty name creates the category and moves the cursor onto the new node; an empty name files the entry as uncategorized and moves the cursor to `(uncategorized)`. Either way the field disappears, because it is shown if and only if the cursor sits on `(new category)`.
- Fields are fixed-width and scroll internally — borders never move while typing.
- `Tab` cycles the fields and then the create button, wrapping back to the first. Creating clears the fields, shows `牛肉 added successfully!`, and **keeps the selection**, so consecutive words in one category need no re-navigation.
- Typing hanzi prefills pinyin, but only while the pinyin field is still untouched for that entry.

**M5.3 — Browse screen.** Fuzzy filename search plus a tag filter over `tag_index()`.

**Done when.** Twenty words can be entered into one category without touching the tree; a new category can be created and immediately filled; an empty category name produces an uncategorized entry above the first `##`; and the resulting file's formatting and tag placement survive inspection.

---

## M6 · Seed content

**Deliverable.** A starter tree so the app is not empty on first run: `Vocabulary/Food.md` with Meat, Vegetables and Fruits, and `Grammar/Asking for directions.md` carrying `#travel` and `#"C1 exam"`.

**Done when.** A fresh clone runs, shows a populated tree, and compiles.

---

## Later

Deferred deliberately. From the closing section of the original proposal and from decisions made during planning.

- **Creating directories and files from the app.** Currently a new topic file or top-level directory is made in the shell. The tree structure is the user's, and the MVP does not need to own it.
- **Editing and deleting entries from the TUI.** The app only appends. Reordering, moving between categories, correcting a typo and deleting are all done by hand in a text editor — which the format is designed to make easy — until the append path is proven.
- **Renaming and deleting categories from the TUI.** Same reasoning.
- **Editing tags from the TUI.** Tags are read for filtering; they are written by hand.
- **Shell integration for *Notebook* and *Inspect tree*.** Genuinely changing the parent shell's working directory requires a sourced zsh function, which conflicts with staying plug-and-play. Revisit only if the placeholders prove annoying.
- **Other languages.** The format and the tree carry over with no redesign; only pinyin prefill is Chinese-specific and it is already isolated in `pinyin.py`. Nothing needs to happen until a second language actually exists.
- **Watch mode.** Recompile a PDF automatically when its `.md` changes.
- **Search inside entries.** Fuzzy search covers filenames and tags; searching hanzi and glosses across the whole tree is a natural extension of `store.py`.
