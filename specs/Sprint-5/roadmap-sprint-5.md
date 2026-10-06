# Roadmap — Sprint 5

Sprint 4 rebuilt how screens are put together and how the app gets installed.
Sprint 5 is the sprint that clears the backlog: for the first time, **every**
item in [`guidelines/backlog.md`](guidelines/backlog.md) is on the roadmap,
nothing deferred. The decisions taken while turning it into this roadmap live in
[`guidelines/notes-sprint-5.md`](guidelines/notes-sprint-5.md).

The backlog's five sections become six milestones — the grammar folder is split,
being much the largest of them — plus **M3, added at sprint start** and not from
the backlog: the dev asked for the compiled PDFs' appearance, and their CJK font
in particular, to change. Seven in total.

The ordering principle is **shared code before its consumers, and the platform
last**:

- The two items that change code every screen or every compile runs through
  come first: *Screen real estate* on `panels.py` (M1) and *Fix compile_all* on
  `compile.py` (M2).
- Everything that changes what a PDF looks like comes after M2, because M2 is
  what makes such a change visible at all: typography (M3) and the grammar
  renderer (M6).
- Typography is settled **before** the grammar renderer, so M6's eyeball check
  against the dev's reference picture is about layout rather than being muddied
  by a typeface still known to be wrong. It is also the smallest possible
  consumer of M2, which makes it the proof M2 works.
- The PDF preview (M4) follows typography, so the first thing it previews
  already looks right, and it sits on M1, being a new panel whose content never
  fits.
- Linux (M7) comes last so it ports one finished codebase rather than a moving
  one. M4 adds a rasteriser dependency and M3 settles a font that is very
  likely macOS-only; porting after both means porting once.

Sprint 4's vocabulary is used below without re-explaining it: a **menu** is a
screen whose content is a list; a **screen** is what opens from a menu; a screen
is a **backpanel** holding **panels** holding **content**. See
[`../current/design.md`](../current/design.md).

Each milestone lists its deliverable, what its spec conversation still has to
settle, and the condition that closes it.

---

## M1 · Screen real estate

The backlog's *Screen real estate*, in full: "Every screen should
automatically move the focus and add a scrollbar only when the content does not
fit the screen."

First because it changes `panels.py`, which every screen in the app is built
on — including the screen a later milestone adds a panel to. Doing it after M4
would mean fixing the same overflow twice.

**Deliverable.**

- **Scrollbars appear only when content overflows**, on every panel and every
  flat menu, and take no space when it doesn't. Today's behaviour is ad-hoc:
  `app.tcss` gives a few widgets `height: auto` with a hand-picked
  `max-height: 8`, one rule per place someone noticed a problem, and nothing
  general. This becomes a property of `Panel` and `Backpanel` rather than a
  per-screen CSS rule.
- **Focus follows the cursor into view.** When a focused widget — or the
  selected row inside it — is scrolled out of the visible region, the screen
  scrolls it back into view rather than leaving the user typing somewhere
  they can't see. This must hold for a tree's cursor line, a menu's
  highlighted option, and a form's focused field.
- **Every screen is checked at a small terminal.** The regression this
  milestone is really about is a screen that silently clips: Entry's form
  panel with every field shown, Browse's results on a long match list,
  Inspect Tree on a deep tree, the wizard's dependency checklist, Settings'
  input-method form. Each is confirmed by hand at a deliberately short
  terminal.
- [`../current/design.md`](../current/design.md) gains the convention as a
  standing rule, stated once, in the same place the focus and `esc` rules
  live — not restated per screen.
- The navigation model is **unchanged**. `esc`/`enter`/shift+hjkl, backpanel
  reachability and the focus look all behave exactly as Sprint 4 M1–M2 left
  them; a scrollbar is not a panel and is never a focus stop.

**Open for the spec conversation.** Whether "move the focus" in the backlog
means only scroll-into-view, or also changing *which* widget is focused when
one scrolls away. Whether the hand-tuned `max-height` rules in `app.tcss`
(the 8-line select list, the form panel) are replaced by the general rule or
kept as deliberate caps on top of it. What happens to a panel too short to
show even one row. And whether Textual's own `scrollbar-gutter` /
`overflow: auto` get us most of this for free, or the scroll-into-view half
needs real code.

**Done when.** No screen shows a scrollbar it doesn't need; every screen that
overflows gets one; moving the cursor to a row outside the visible region
brings it into view on every tree, list and form in the app; the dev confirms
each screen by hand at a short terminal; `design.md` states the rule; and the
full test suite passes.

---

## M2 · compile_all and renderer staleness

The backlog's *Fix compile_all*: "compile_all does not detect changes to the
renderer, so a renderer change leaves already compiled pdfs falsely looking up
to date."

Second because M3 and M6 are both renderer changes, and this is the milestone
that makes their results visible at all.

**Deliverable.**

- **A renderer change makes every affected PDF recompile**, with nothing for
  the dev to remember to do. Today
  [`compile.py`](../../src/idiomas/compile.py)'s `compile_all` skips a file
  whenever `notebook_path.stat().st_mtime > source_path.stat().st_mtime` — a
  comparison that knows only about the source `.md`, so a change to
  `render_markdown`, to `_render_table`, or to `templates/xecjk.tex` leaves
  every existing PDF untouched and wrong.
- **The staleness check accounts for the template too**, not just Python
  code. `templates/xecjk.tex` decides the font and the page; editing it is as
  much a renderer change as editing `_render_table`. M3 is exactly that edit,
  one milestone later.
- **A manual override.** Whatever the automatic check, there is a way to force
  a full recompile — the escape hatch for the case where the check is wrong.
  Whether that's a flag on `idiomas compile`, a key in the notebook menu, or
  both is the spec conversation's call.
- The fast path stays fast: a run with nothing changed must still skip
  everything without invoking pandoc, and both callers — `__main__.py`'s
  `compile` subcommand and the notebook menu's *Compile all* — keep their
  current "here's what was rebuilt" reporting.
- A test covers the actual bug: compile a file, change what the renderer
  produces, run `compile_all`, and assert the PDF was rebuilt.

**Open for the spec conversation.** The mechanism, which is the whole
milestone. The leading candidate is to compare **what the renderer would
produce** — a hash of the intermediate markdown plus the template's contents —
against a stamp recorded for that PDF, which is automatic, precise, and
catches the template for free; parsing and rendering to text is cheap next to
pandoc + xelatex. The alternatives are a hand-bumped `RENDERER_VERSION`
constant (simple, but "with nothing for the dev to remember" is exactly what
it fails at) and comparing the PDF's mtime against the renderer module's
(fragile once the package is installed). Then: **where the stamp lives.** A
sidecar file per PDF would show up in Inspect Tree's own tree, so a cache
under `~/.cache/idiomas/` is the likelier home — this would be the project's
first persisted cache (`store.py`'s `TagCache` is in-memory only), so its
format, its corruption behaviour, and what happens when it's missing all need
deciding. Also: whether a stale-cache false *positive* (recompiling
unnecessarily) is always acceptable, which would let the cache be safely
deleted at any time.

**Done when.** With every PDF up to date, changing `_render_table` and running
*Compile all* rebuilds all of them; changing `templates/xecjk.tex` does the
same; running it twice in a row with no change rebuilds nothing and takes no
noticeable time; deleting the cache is safe; a forced recompile is available;
the dev confirms against their real tree; and the full test suite passes.

---

## M3 · Notebook typography

**Not from the backlog.** Added at sprint start on 2026-09-20, when the dev
asked for "a milestone to change the appearance of the files" — the compiled
PDFs — giving the font as the reason: *"i dont like the current font, use the
font of the picture."* Asked which font, they were specific: **"i dislike the
chinese font not the translation font."** The picture is the same
[`guidelines/image-1.png`](guidelines/image-1.png) the backlog's grammar
section links.

Placed after M2 because it is a template change and M2 is what makes a
template change rebuild anything; placed before M6 so the grammar renderer is
judged on its layout rather than on a typeface already known to be wrong.

**Deliverable.**

- **A new CJK face, chosen by the dev by eye.** The milestone's *first* step
  is a comparison PDF: the same content set in each CJK face actually
  installed on the machine — **STHeiti Light** and **STHeiti Medium** (what
  today's `\setCJKmainfont{Heiti SC}` resolves to), **Hiragino Sans GB**, and
  **Songti SC** — shown next to the picture. Nothing is written into the
  template until the dev names one. (PingFang SC, macOS's usual modern
  default, is **not** installed here; if the dev wants it, installing it is
  part of the milestone.)
- **The Latin face is left as it is** — the dev said plainly they don't
  dislike it — but it **stops being an accident**. Today the template sets no
  `\setmainfont` at all, so every Latin glyph falls back to LaTeX's default
  Latin Modern Roman. The template will state the choice explicitly, so it
  can't drift and so the next person to read it knows it was decided.
- **A wider typography pass**, the dev's own scope choice over font-only: the
  heading style and sizes, the title block (currently pandoc's bare
  `\maketitle`), the margins (`margin=1in`), the body size (`12pt`) and the
  row spacing (`\arraystretch{1.6}`) are all reviewed together as one
  coherent look rather than left as the defaults they currently are.
- **`design.md` gains the compiled notebook.** Today it covers the TUI only —
  navigation, panels, the focus look — and the PDF, which is just as much a
  user-facing surface, has no home there at all. The notebook's typography
  becomes a standing convention stated once, the same way the navigation keys
  are.
- **Every place the font name appears follows the choice, and cannot drift.**
  `templates/xecjk.tex`'s `\setCJKmainfont`, `stack.md`'s summary-table row
  and its *PDF* section prose, and `doctor.py`'s
  `CJK_FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"` all name the
  font independently today. Sprint 4 M4 fixed exactly this class of drift
  once already — `doctor.py` was still checking Songti SC long after the
  template had moved to Heiti SC — so the milestone leaves one source of
  truth rather than three copies.
- **Both renderers are covered**: vocabulary files and grammar files get the
  new type. M6 then builds its layout on top of settled typography.
- **M2 is what makes this checkable**: landing this milestone must rebuild
  every existing PDF automatically, with no manual deletion.

**Open for the spec conversation.** Which face, from the samples — the whole
point of the first step, and not decided here. Whether **Songti SC** is even
in the running, being a Ming/serif face where the picture is clearly a sans.
Whether the chosen face's weight matters (STHeiti ships Light and Medium as
separate files, and the picture's strokes are noticeably light). Whether the
Latin face is made explicitly Latin Modern Roman or quietly reconsidered
after all once the two sit side by side. What the title block should look
like, given `\maketitle` on an article class is the most obviously
"untouched LaTeX" thing in the output. Whether category headings take a
different face or weight from the body. And **whether the chosen face exists
off macOS at all** — Hiragino Sans GB and Songti SC are both macOS-only,
which lands squarely on M7 (see its font bullet).

**Done when.** A comparison PDF has been rendered and the dev has named the
face; every compiled notebook uses it; landing the milestone rebuilds the
dev's existing PDFs with no manual step; `idiomas doctor` checks for the
chosen font rather than Heiti SC, and the font is named in exactly one place
in the code; `design.md` documents the notebook's typography; `stack.md`'s
CJK-font row and prose match what ships; the dev approves the result by eye
against `image-1.png`; and the full test suite passes.

---

## M4 · PDF preview pane

The backlog's *implement pdf preview*: "in the right pane of the inspect tree
screen."

**Deliverable.**

- **Inspect Tree gains a second panel**, to the right of the tree, showing
  the PDF of whatever the cursor is on. It follows the cursor — moving to
  another file previews that file.
- **A real rendered page**, not text: `pdftoppm` rasterises the first page and
  it is drawn with the **kitty graphics protocol**, which the dev's terminal
  (Ghostty 1.3.1, installed 2026-09-20) speaks. This is the point of
  the feature — a text preview would lose the fonts M3 has just settled, the
  layout, and the hanzi/pinyin alignment M6 exists to produce.
- **poppler is an optional dependency.** `doctor` gains a check for
  `pdftoppm` in its *optional* tier, alongside `macism` and `nvim`: missing it
  degrades the preview and nothing else, and must never block compiling.
  Install line shown, not run — the wizard's standing block-on-required,
  warn-on-optional rule (Sprint 4 M4/M5) applies unchanged.
- **Graceful degradation, stated as behaviour rather than assumed away.** The
  pane says what it can't do and why, for each case: no poppler, a terminal
  with no image protocol, a directory or a `.md` with no compiled PDF beside
  it, a PDF that fails to rasterise. None of these is a crash and none blocks
  using the rest of the screen.
- **Rasterising happens off the UI thread**, in a worker, like the autocompile
  workers already do — moving the cursor fast down a tree must not stall the
  tree.
- Everything Inspect Tree already does still works: PDF/MD mode on `tab`,
  `enter` to open, `d`/`r`/`n`/`m`/`u`, and its autocompile-on-return
  behaviour. Note that Inspect Tree goes from **one panel to two**, which by
  `design.md`'s own rule means its backpanel becomes reachable with `esc` and
  shift+hjkl start doing something there — that is the intended consequence,
  not a regression.

**Open for the spec conversation.** **Whether iTerm2's inline-image escape is
carried as well.** The primary target is settled — Ghostty speaks the kitty
graphics protocol — but iTerm2 and VS Code's integrated terminal speak only
the older escape, so supporting both is a portability call rather than a
choice between them. And **how support is detected at runtime**, which is
needed either way for the degradation path above. How a rasterised page is
sized to the pane and what happens on resize.
Whether renders are cached and keyed on what — M2 has just built a staleness
mechanism that may be reusable here. Whether the preview shows the PDF in MD
mode too, or the pane changes with the mode. And whether the tree panel and
the preview split the width evenly.

**Done when.** Moving the cursor onto a file in Inspect Tree shows its
compiled PDF in the right-hand pane; moving to another file changes it;
moving fast down the tree doesn't stall; a directory, a PDF-less file, a
missing `pdftoppm` and an image-incapable terminal each show a clear message
instead of failing; `idiomas doctor` reports `pdftoppm` as optional; `esc`
and shift+hjkl behave per `design.md` now that the screen has two panels; the
dev confirms by eye **in Ghostty**; the same screen in a terminal with no
image support degrades to the message rather than breaking; and the full test
suite passes.

---

## M5 · The grammar folder — format and entry

The first half of the backlog's *Grammar folder*: everything except the PDF.
"The grammar folder will be special and managed differently. Though it will
still be managed through the enter vocabulary menu. The visual difference is
the right panel changes from the rest of the folders."

**Deliverable.**

- **Grammar files are recognised as grammar**, by living under the tree's
  top-level `Grammar/` folder — the backlog states it as a folder, and the
  dev's real tree already has `tree-Chinese/Grammar` alongside `Vocabulary`
  and `Testeo`.
- **Subtitles: a third level in the file format**, below the category and
  above the triads. The backlog's example: inside the category
  *Conjunctions*, subtitles like *copulative conjunction* and *disjunctive
  conjunction*. `##` is already the category heading in
  [`parser.py`](../../src/idiomas/parser.py), so `###` is the obvious
  subtitle, but it's `plan.md`'s call. `models.py` gains whatever holds it.
- **The round trip still holds.** `parse(write(deck)) == deck` is the
  project's correctness backbone (`stack.md`) and must cover subtitles,
  including a grammar file with none, a subtitle with no entries, and a
  category mixing loose entries with subtitled ones. Existing grammar files —
  today byte-identical in format to vocabulary files — must keep parsing
  unchanged.
- **Entry's right panel changes for a grammar file.** The tree, the category
  structure and the hanzi/pinyin/translation/note fields are unchanged; what
  changes is that a grammar target also has a subtitle, and that a subtitle
  can be created the way Sprint 4 M3 made `(new category)` creatable. It is
  reached through the same *Enter vocabulary* menu as everything else.
- **Nothing about vocabulary changes.** A file outside `Grammar/` parses,
  renders and edits exactly as it does today; M5 adds a branch, it doesn't
  move everyone onto a new format.

**Open for the spec conversation.** Whether the grammar marker is really the
folder name, or a header in the file, or config — and what happens to a
grammar file moved out of `Grammar/`, or a nested `Grammar/` deeper in the
tree. Whether subtitles are optional inside a grammar category (the existing
files have none, which suggests yes). What Entry's grammar panel actually
looks like — where the subtitle field sits, whether `(new subtitle)` mirrors
`(new category)`, and whether a grammar entry keeps the note field. Whether
Inspect Tree, Browse and the tag index need to know about grammar at all.
And whether a subtitle can nest further.

**Done when.** A grammar file with categories and subtitles round-trips
through `parser.py`/`writer.py` with no loss; the dev's existing
`Grammar/*.md` files still parse unchanged; opening a grammar file in Entry
shows the grammar panel and a vocabulary file shows the normal one; a
subtitle can be created and entries added under it from the app; compiling a
grammar file still produces a PDF (the old layout is fine — M6 is the new
one); the dev confirms by hand; and the full test suite passes.

---

## M6 · The grammar renderer

The second half of *Grammar folder*: the PDF. The reference is the dev's own
[`guidelines/image-1.png`](guidelines/image-1.png), copied in alongside the
backlog that links it. By this point M3 has settled the typeface, so what is
judged here is **layout**.

**Deliverable.** A second rendering path in `compile.py` for grammar files,
leaving the vocabulary path untouched:

- **The triad is three lines, not three columns.** Hanzi, then pinyin, then
  the translation, stacked — where vocabulary renders a three-column
  `longtable`.
- **Tighter inside a triad than between triads.** The vertical gap separating
  hanzi/pinyin/translation is visibly smaller than the gap between one triad
  and the next, so a triad reads as one block.
- **Pinyin is smaller and lighter** — a smaller size in a paler shade, as in
  the image, expressed against M3's settled type rather than as an
  independent font decision.
- **Each pinyin syllable is aligned under its own hanzi character.** This is
  the hard part and the reason the milestone is separate: hanzi are
  double-width glyphs and pinyin syllables are variable-width Latin, so
  alignment is per-character positioning, not a space-separated line.
- **Characters with no reading get no pinyin under them.** The backlog's
  example is `...`; the general rule is that a non-hanzi character in the
  hanzi field contributes no syllable. `pinyin.py` produces the readings; the
  renderer decides the pairing.
- **Subtitles render as a heading** below the category heading, as in the
  image.
- Pinyin is still stored numbered and tone-marked at compile time
  (`to_tone_marks`), unchanged. LaTeX escaping (`_escape`) applies to grammar
  output exactly as it does to vocabulary.
- **M2 is what makes this checkable**: landing this milestone must rebuild the
  dev's existing grammar PDFs automatically, with no manual deletion.

**Open for the spec conversation.** The LaTeX mechanism for per-character
alignment — `ruby`/`xpinyin`, a per-character `\begin{tabular}` column, or
stacked boxes — and whether it needs a package `doctor` should check for, the
way `xeCJK` already is. How a triad that runs past the line width wraps, or
whether it's kept from wrapping. What happens to a grammar entry with a note
(vocabulary renders it as a parenthetical italic on the gloss). Whether the
translation line is styled at all or stays plain. Exact spacing and shades,
which are eyeball decisions against the image. And whether an empty subtitle
renders as a bare heading, the way Sprint 4 M3 settled for an empty category.

**Done when.** Compiling a grammar file produces the layout in
`image-1.png` — three stacked lines per triad, tight within and loose
between, pinyin smaller and paler and aligned character by character, `...`
and friends bare, subtitles as headings; vocabulary PDFs are unchanged by
this milestone; landing it rebuilds the dev's grammar PDFs with no manual
step; the dev approves the result by eye against the image; and the full test
suite passes.

---

## M7 · Linux support

The backlog's *Add linux support*: "Add whatever is necessary for linux
support."

Last, deliberately: it ports what M1–M6 leave behind rather than a codebase
still moving under it. Sprint 4 M4 built `idiomas.platform` for exactly this
milestone — the test of that design is whether Linux is an addition here or a
rewrite.

**Deliverable.**

- **A Linux module in the platform layer**, `platform/linux.py`, dispatched
  the same way `macos.py` is. It implements the four things the layer
  covers — opening a file, the CJK-font check, input-source switching, and
  listing input sources — plus `user_bin_dir`, which today returns `None` off
  macOS and makes the wizard skip its `PATH` step entirely.
- **Everything OS-specific that leaked out of the layer is moved in.** Known
  at sprint start: `doctor.py` hardcodes a macOS font path outside the
  platform layer (M3 will have changed *which* font, not the fact that it's
  hardcoded there), and every install command it prints is a `brew` line. A
  sweep for the rest is part of the milestone.
- **The CJK font is per-platform.** Whichever face M3 settles on is very
  likely macOS-only — Hiragino Sans GB and Songti SC both are, and so is
  STHeiti — so Linux needs its own counterpart (Noto Sans CJK or Noto Serif
  CJK, matching whichever style M3 chose) and `templates/xecjk.tex`'s
  `\setCJKmainfont` has to follow. That means the template stops being a
  fixed file for the first time. How is `plan.md`'s call.
- **`doctor` reports Linux dependencies with Linux install commands** —
  pandoc, TeX Live with xeCJK, the font, and M4's `pdftoppm`
  (`poppler-utils` on Debian/Ubuntu, `poppler` elsewhere) — rather than
  telling a Linux user to run `brew`.
- **The installation wizard runs on Linux end to end**, including its final
  step: `~/.local/bin` and the shell-config line are if anything more
  standard on Linux than on macOS, and `~/.zshrc` is the wrong default for a
  bash user.
- **The README documents the Linux install**, alongside the macOS one Sprint 4
  M7 wrote.
- **A Docker image for verification**, checked into the repo: pandoc, TeX Live
  with xeCJK, a CJK font, Python, and whatever it takes to run the app and
  the suite. This is how the milestone gets confirmed by hand at all, the dev
  being on macOS.
- **macOS must not regress.** Every macOS behaviour is unchanged; this
  milestone adds a branch and moves code into the layer, it doesn't alter
  what the layer does on a Mac.

**Open for the spec conversation.** **Which input-method framework** — ibus,
fcitx5, both, or none, given a container cannot verify any of them (see the
notes' Assumptions). Which distro the Docker image targets and how big is too
big. How the shell-config line picks a file when the user isn't on zsh. How
the Linux CJK font is chosen when several are installed, or none is — and
whether a visible difference between the macOS and Linux faces is acceptable
or needs a font both platforms can install. Whether "Linux support" includes
WSL. And whether M4's image protocol behaves the same under a Linux
terminal — Ghostty itself runs on Linux, so the container can plausibly be
driven from the same terminal the dev uses on macOS.

**Done when.** The app installs and runs inside the Docker image from the
README's Linux instructions; the wizard completes there, writes a config,
links `idiomas` and adds the `PATH` line to the right shell config;
`idiomas doctor` lists Linux install commands and no `brew`; a notebook
compiles to a correct PDF with a Linux CJK font, grammar files included; the
full test suite passes inside the container; nothing outside
`idiomas.platform` names a macOS-only tool or path; the dev confirms macOS is
unchanged by hand; and the full test suite passes on macOS.

---

## Not in this sprint

For the first time, **nothing from the backlog is deferred** — all five of its
sections are on the roadmap above, and M3 was added on top of it.

Out by decision during this sprint's planning, and recorded in
[`guidelines/notes-sprint-5.md`](guidelines/notes-sprint-5.md)'s Postponed
table:

- **Windows support.** The backlog asks for Linux; M7 keeps the platform layer
  honest enough that Windows stays an addition.
- **A working German notebook**, still inert — Sprint 4's standing decision.
  M5/M6's grammar format is Chinese-shaped (hanzi, pinyin, translation) and
  doesn't pretend otherwise. M3's typography likewise settles one CJK face,
  not a per-language type system.
- **Multi-page PDF preview.** M4 previews a page, not a document.
- **The Settings submenu.** *Add a language* and *Remove a notebook* are still
  placeholders, and still in no backlog.
- **Brew packaging**, carried from Sprint 4 with the same standing: the
  documented `git clone` install works, so this stays a nice-to-have.
