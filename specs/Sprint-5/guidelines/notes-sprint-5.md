# Sprint 5 — notes

Agent-maintained companion to [`backlog.md`](backlog.md), which is written by the
dev and is the authoritative statement of intent. This file does not restate it;
it records what was decided, assumed, or postponed while the backlog was turned
into [`../roadmap-sprint-5.md`](../roadmap-sprint-5.md), and it grows as the
sprint runs.

**Scope discipline for this sprint.** Unlike Sprints 1–4, this backlog is not a
selection from a longer deferred list: the dev asked for **every** item in it to
be in the sprint. All five backlog sections — *Add linux support*, *Fix
compile_all*, *implement pdf preview*, *Screen real estate*, *Grammar folder* —
are on the roadmap, as six milestones (the grammar folder is split in two). There
is no unmarked remainder this time, and no `(5)` marking convention.

**One milestone is not from the backlog.** M3, *Notebook typography*, was added
by the dev later in the same sprint-start conversation: "add a milestone to
change the appearance of the files. i dont like the current font, use the font
of the picture." It is recorded here and in the roadmap, never written into
`backlog.md` — that file is a frozen copy of what the dev's own
`postponedfeatures.md` said when the sprint opened, and adding to it would make
it a record of something that was never in it. Sprint 4 handled its own
mid-sprint M7 the same way.

**Where the backlog came from.** `backlog.md` is a **copy** of the dev's
root-level `postponedfeatures.md`, taken on 2026-09-20 and kept verbatim. The
dev chose to copy rather than move: the root file stays theirs, a living
deferred list they keep managing across sprints, while this copy is Sprint 5's
frozen record of what it said when the sprint opened. `image-1.png`, which the
backlog's last section links relatively, was copied alongside it for the same
reason — the reference has to keep resolving after the root file moves on. Both
root files remain the dev's and are never edited here.

**Sprint 4 closed cleanly.** All seven milestones — M1 through M7 — were specced,
implemented and merged (M7 via PR #30), nothing was dropped, and the `changelog`
skill ran before this sprint opened (commit `bccca03`). No milestone carries
over. Sprint 4's own Postponed table lists seven open items; none of them was
brought into this sprint, and the two this sprint touches anyway are noted below.

**M1, Screen real estate, merged 2026-09-21** (PR #31), dev-confirmed by hand at
a short terminal across all five named screens with no changes requested. Its
spec-conversation decisions are folded into the Decisions table below.

**M2, compile_all and renderer staleness, merged 2026-09-22.** The dev asked
for this one without a spec conversation ("do m2. i wont test so do it
yourself") — the mechanism and every other open question from the roadmap
were decided by the agent alone, from the roadmap's own leading candidates,
and verified mechanically (unit tests plus a real pandoc/xelatex run) rather
than by the dev's hand. Its decisions are folded into the Decisions table
below.

**M3, Notebook typography, merged 2026-09-22** (PR #33). The dev picked
**Songti SC** from a rendered comparison against the four installed
candidates (`comparison.pdf`, in the milestone's own spec folder), despite it
being the one serif face where `image-1.png` is visibly sans — their own
eyeball call, not a mismatch corrected afterward. The dev then opted out of a
second comparison round for title/heading style ("Just make the call"), so
the agent designed the rest of the pass — title block, category headings,
explicit Latin font — and handed over a real recompiled notebook instead. One
round of feedback followed: the dev asked for the hanzi sized up relative to
pinyin/gloss ("increase the size of the hanzi"), applied as `{\Large ...}`
around the hanzi cell in `_render_table`, approved after that ("nice"). Its
decisions are folded into the Decisions table below.

**M4, PDF preview pane, merged 2026-09-22** (PR #34). Spec conversation
settled the scope decisions listed in the Decisions table below (kitty-only,
env-var detection, per-mode content, the `pdftotext` fallback). Two things
surfaced only once the dev hand-tested in Ghostty, both folded into the spec
as they came up rather than left as silent code-only fixes: `pdftoppm` turned
out to have no stdout mode at all, and — found only on manual retest —
doesn't compute an omitted `-scale-to-x`/`-scale-to-y` proportionally either,
so the original implementation both piped incorrectly and stretched the page
to fill the pane on a non-matching aspect ratio; both are fixed in
`idiomas.pdf_preview.rasterise_page`. Three more rounds of hands-on feedback
followed: a kitty image left lingering after leaving the screen or moving to
a directory (a kitty image sits in its own compositor layer that redrawing
text never clears, so it needs an explicit delete — added to
`action_back_or_quit` and to every message-state transition); a
directory-to-PDF cursor move not previewing while PDF-to-PDF did (traced to
sizing/positioning off the image widget's own stale pre-layout region rather
than the always-live preview panel's); and a proposed "too small" cutoff on
resize that the dev asked to drop after a first attempt didn't trigger
reliably — the aspect-ratio fix alone was kept, the cutoff was reverted
entirely (code, tests and spec) rather than iterated further. Its decisions
are folded into the Decisions table below.

**M5, The grammar folder — format and entry, merged 2026-09-28** (PR #35).
Spec conversation settled the folder-based grammar marker, the Subtitle
field living in the form rather than the tree, the Note field staying, and
the *Minimal* scope (subtitles optional and one level deep, Inspect
Tree/Browse/the tag index untouched) — all folded into the Decisions table
below. Confirmed against the dev's real tree: the existing
`Grammar/Clasificadores.md` and `Grammar/Asking for directions.md` parsed
identically with the grammar flag on and off, so the milestone changed
nothing about them. The dev then moved both to `Vocabulary/` and asked for a
fresh dummy grammar file to test against, after not seeing the Subtitle
field on `Asking for directions.md` — which has no `##` categories at all,
so there was never a category target for the field to appear on; expected
behaviour, not a bug, confirmed by reproducing the exact tree headlessly.
One round of hands-on feedback on the new `Grammar/Conjunctions.md`
followed: picking a Subtitle option left focus on the collapsed field
instead of moving the form forward, fixed by advancing to Hanzi
(`(none)`/an existing subtitle) or the name field (`(new subtitle)`) on
`SelectField.Changed`. A second observation — a newly-added entry not yet
showing in the compiled PDF — turned out to be a timing read rather than a
bug: exiting *Enter vocabulary* triggers the screen's existing
autocompile-on-unmount, and the PDF was confirmed correct once rechecked
after exit. Its decisions are folded into the Decisions table below.

**M6, The grammar renderer, merged 2026-09-29** (PR #36). The alignment
mechanism was left to the agent's judgment (a self-contained `\HanziPinyin`
macro, a `[t]`-aligned two-row `tabular` per hanzi character, rather than
falling back to an external LaTeX package), and a note renders as an italic
parenthetical, matching vocabulary's own convention. Mid-implementation,
checking pandoc's own raw output (rather than assuming, as the M3-era
`\subsection` redefinition had) showed a category heading (`##`) actually
shifts to `\section`, not `\subsection` — the existing redefinition had been
inert the whole time, restyling a command pandoc never emitted for a
category. It's repurposed for the subtitle heading (`###`) instead, and
`design.md`'s M3 entry corrected to match. Three rounds of the dev's manual
review against the real `Grammar/Conjunctions.md` followed, each folded
back into `compile.py`'s constants and the template: the first found pinyin
too far from its hanzi (inheriting the vocabulary table's global
`\arraystretch{1.6}`) and a note sitting inline beside the translation
instead of below it; the second found a spacing bug — a standalone
`\vspace` line leaves a non-discardable item that turns the source newline
after it into a visible space, indenting every line but the first, fixed by
moving the gaps into `\\[...]` line-break arguments instead — and shrank the
subtitle heading from `\large` to body size with an en-dash prefix; the
third found the gap before a subtitle larger than the gap between two
ordinary entries (the subtitle's own beforeskip stacking on top of the
entry gap), fixed by reducing the beforeskip to `-1sp` — still negative, so
`\@startsection`'s indent suppression still fires — and ending each block's
last entry with `\par\vspace{GRAMMAR_ENTRY_GAP}` rather than a trailing
`\\[...]`, which had been adding an extra blank line. Its decisions are
folded into the Decisions table below.

**M7, Linux support, merged 2026-09-29** (PR #37). The spec conversation
settled D1–D7 (OrbStack, an Arch image, fcitx5 and ibus both, Noto Serif
CJK SC, install commands by distro family, `.bashrc` as the Linux fallback,
WSL out). No container runtime existed when the milestone opened. The dev
installed OrbStack and then handed the whole container pass to the agent
("i can install orbstack and then you test"). That pass found six things,
each folded into the spec as it came up:
- pacman's download sandbox fails under emulation;
- Arch's `texlive-xetex` can't compile the template on its own;
- `tui/app.tcss` was never package data, so the README's non-editable
  install crashed on launch on **every** platform. The dev had never seen
  it, because they run an editable checkout;
- the input-source advisories told Linux users to open System Settings;
- the wizard's dependency column misaligned on Linux's longer names;
- `test_main` read the machine's real config.

Mid-hand-off, the dev asked why a Docker image existed at all, having read
it as a change of distribution. Clarified: it's a test machine only, per
the sprint-start decision, and the install stays `git clone` + venv
everywhere. The dev confirmed the goal ("someone in linux [can] use the
program the same way a user in mac does") and approved the merge without a
separate macOS hand-check pass. Their own `idiomas` runs this checkout
editable, so their use that day ran the branch. Its decisions are folded
into the Decisions table below.

**One correction to a standing doc, made at sprint start.**
[`../current/stack.md`](../current/stack.md)'s *Distribution* section still
described `pipx install git+https://...` as the install path. Sprint 4's M7
reversed that mid-milestone — the dev dropped `pipx` for a documented `git
clone` + venv, and the wizard gained a step that symlinks `idiomas` into
`~/.local/bin` itself. `readme.md` and `install.py` both match the reversal;
only `stack.md` was left behind. It spans sprints, so it is edited in place
rather than corrected inside frozen Sprint 4.

**Sprint 5 is complete as of M7** (PR #37, 2026-09-29). All seven milestones
— M1 through M7 — were specced, implemented and merged; nothing was dropped and
nothing was deferred, so no milestone carries over into Sprint 6. The
`changelog` skill ran on `main` before Sprint 6 opened (commit `8ca8ec8`). What
does carry forward is this file's Postponed table: Sprint 6's backlog picks up
**a working German notebook** (with the per-language typography and the
grammar-for-German questions attached to it) and **the Settings submenu**'s two
placeholders, *Add a language* and *Remove a notebook*. Those are restated in
Sprint 6's own notes, not tracked here.

## Decisions

Settled with the dev during this sprint-start conversation, on 2026-09-20.

| Decision | Rationale |
| --- | --- |
| **Every backlog item is in the sprint.** Nothing deferred, nothing dropped | Dev's opening instruction: "it should incorporate every feature in the postponedfeatures list." The first sprint whose backlog is taken whole. |
| **`backlog.md` is a copy; `postponedfeatures.md` stays at the root** | Dev's choice against `git mv`. The root file goes on being their living deferred list; the sprint gets a frozen snapshot so its record can't change under it later. `image-1.png` copied alongside so the backlog's relative link still resolves. |
| **Seven milestones, ordered shared-code-first, platform-last** | The two backlog items that change shared code (*Screen real estate* on `panels.py`, *Fix compile_all* on `compile.py`) come before everything that consumes them, both PDF-appearance milestones (M3, M6) come after the staleness fix that makes them visible, and Linux comes last so it ports one finished codebase rather than a moving one. Six from the backlog plus M3. See the roadmap's preamble. |
| **The grammar folder is two milestones:** file format + Entry's panel (M5), then the PDF renderer (M6) | Dev's choice from three options. Each half is hand-testable on its own — M5 in the app, M6 by eye against `image-1.png` — where a single milestone would show nothing until the end. Same approach as Sprint 3's M3→M4 and Sprint 4's M1→M2. |
| **`compile_all`'s fix lands before anything that changes a PDF** | Not a preference, a dependency: M3 (a template change) and M6 (a renderer change) both are exactly the case the bug describes — a change that leaves PDFs falsely up to date. Without M2 first, the dev's existing PDFs would silently keep the old look, and neither milestone's done-when could be checked by eye. |
| **The PDF preview draws real images via a terminal image protocol**, not text and not Unicode blocks | Dev's choice. A text-only pane would lose fonts, layout and the hanzi/pinyin alignment that M6 exists to produce, and the typeface M3 settles — the preview would show least of what it's most needed for. Unicode half-block rendering was rejected on the same grounds: a page of hanzi at that resolution is unreadable. |
| **poppler is the rasteriser, and an *optional* dependency** | Dev's choice. `pdftoppm` is the standard tool and `pdftotext` ships with it, which gives the no-protocol fallback for free from the same install. Optional in `doctor` because a missing rasteriser degrades the preview only — it must never block compiling, which is what `doctor`'s required tier is for. PyMuPDF was rejected as a large AGPL wheel; mupdf-tools as having no equally clean text-extraction path for the fallback. |
| **Linux is verified in a Docker container** | Dev's choice. The done-when rule is that the dev confirms by hand, and they are on macOS with no Linux machine; a container is the only way this milestone gets checked at all rather than shipped on faith. Input-method switching is the one part a container cannot verify — see Assumptions. |
| **`stack.md`'s stale *Distribution* section is corrected at sprint start**, not inside a milestone | It contradicts the shipped code and README, and every milestone this sprint reads `stack.md` for architecture. Fixing it once now beats six milestones reading a wrong page. |
| **A seventh milestone, M3 *Notebook typography*, added at sprint start** — not from the backlog | Dev's request, mid-conversation: "add a milestone to change the appearance of the files. i dont like the current font, use the font of the picture." The compiled PDF is a user-facing surface this project has never deliberately designed — it still wears LaTeX's `article` defaults for everything except the CJK font. |
| **The milestone is a wider typography pass, not font-only** | Dev's choice from three options. Font, headings, the title block, margins, body size and row spacing are decided together as one look; font-only would have left `\maketitle`, `12pt` and `margin=1in` untouched and needed a second appearance milestone later. |
| **It is the *Chinese* font the dev dislikes, not the Latin one** | Dev's explicit correction. The agent's first reading was the opposite — the template sets `\setCJKmainfont{Heiti SC}` but no `\setmainfont` at all, so Latin text silently falls back to Latin Modern Roman, TeX's default serif, which looked like the obvious culprit next to the picture's sans. Wrong: the dev is unhappy with the hanzi. The Latin face therefore stays as it is, and M3 only makes it explicit in the template so it stops being a fallback nobody chose. |
| **The face is chosen from rendered samples, not identified from the picture** | After getting the identification wrong once, guessing a second time off a small PNG is not worth it. M3's first step renders the same content in every CJK face installed and the dev names one. The roadmap states the deliverable and the done-when; the face itself is the milestone's own decision, per the project's "interview before speccing" rule. |
| **M3 sits after M2 and before M6** | Two dependencies, not a preference. It is a template change, so M2's staleness fix has to exist first or nothing rebuilds. And M6's done-when is an eyeball check against `image-1.png` — judging its layout while the typeface is still known to be wrong would muddy exactly the comparison that closes it. Being the smallest consumer of M2, it also doubles as the proof M2 works. |
| **The font name gets one source of truth** | It currently appears independently in `templates/xecjk.tex`, `stack.md` (twice) and `doctor.py`'s `CJK_FONT_PATH`. Sprint 4 M4 already had to fix this exact drift once — `doctor.py` was checking Songti SC long after the template had moved to Heiti SC. Changing the font is the moment to stop it recurring. |
| **The dev's terminal is Ghostty**, so M4 targets the **kitty graphics protocol** | Settled 2026-09-20, hours after the sprint opened: the dev installed Ghostty 1.3.1 (`/Applications/Ghostty.app`) in response to the assumption below. Ghostty speaks the kitty graphics protocol, not iTerm2's inline-image escape, which decides M4's primary target. Whether iTerm2's escape is *also* implemented for portability stays M4's own call. |
| **M4 stays kitty-only, no iTerm2 escape** | Dev, M4's spec conversation: "im using ghostty. the program should be usable in non kitty terminals, but without preview." Portability is handled by degrading cleanly, not by a second protocol implementation. |
| **M4 detects protocol support via `TERM_PROGRAM`/`TERM`**, not a terminal capability query | Simple, no I/O, no risk of hanging on a non-responding terminal. Matches how Ghostty and kitty already advertise themselves. |
| **M4's preview pane shows different content per mode** — the rasterised page in PDF mode, the `.md` source's raw text in MD mode | Dev: "md mode should preview text" / "Raw .md source" — the pane always shows *something* relevant to the mode you're in. MD mode shows the source file itself (matching what `Enter` opens in nvim there), not `pdftotext` output. |
| **M4's tree and preview panels split the screen evenly** (50/50), and a directory shows "no file selected" text rather than a blank pane | Dev's choice on both — a rendered page needs real pane width, and every other degradation case is a stated message rather than silence. |
| **M4's rasterised pages are cached** (in-memory, keyed on the PDF's path, size and mtime), separate from M2's compile-staleness cache, and fall back to `pdftotext` output — not just a message — when poppler is present but the terminal lacks kitty support | The cache avoids re-rasterising a page the cursor revisits; the `pdftotext` fallback was already decided when poppler was chosen (above), since it ships free with the same install. |
| **M4's rasterised page always keeps the PDF's own aspect ratio**, fit inside the pane rather than stretched to fill it | Surfaced only in the dev's manual Ghostty testing (2026-09-22), after the milestone was believed done: the original `-scale-to-x`/`-scale-to-y` pair stretches independently to fill the box exactly, skewing the page on a non-matching ratio. Fixed in `idiomas.pdf_preview.rasterise_page` by computing both target dimensions from `page_aspect_ratio` before ever calling `pdftoppm`. |
| **A proposed minimum-pane-size cutoff for M4 was tried and then dropped** — the aspect-ratio fix above was kept | The dev's first retest found the cutoff never actually triggered (checked against the pane's raw cell count, which a badly skewed pane can pass while the aspect-fit render is still tiny); after a second pass judged it against the *fitted* pixel size instead, the dev asked to remove the cutoff outright rather than keep tuning it — "lets just push the changes previous to this (the aspect ratio preservation thing is fine)." Reverted in full: code, tests, and every spec file it had touched. |
| **`design.md` gains the compiled notebook's look** | It currently documents the TUI only. The PDF is just as much a user-facing surface, and by the project's own rule a cross-cutting user-facing convention is stated once in `design.md` rather than per milestone — M6's grammar layout then builds on a documented baseline instead of inventing one. |
| **M1 "move the focus" means scroll-into-view only** — the focused widget's identity never changes because it scrolled off-screen | Dev's choice in M1's spec conversation. Matches `design.md`'s existing focus model: nothing about *which* widget has focus changes, only what's visible. |
| **M1's `.select-list` `max-height: 8` cap is removed**, not kept on top of the general overflow rule | Dev's choice. The deployed list now grows with its content like every other panel and gets a scrollbar only when the terminal itself is too short, no more special-cased shorter cap. |
| **M1's mechanism is Textual's own `overflow-y: auto` plus a `DescendantFocus` handler**, not hand-rolled scroll code | Both are stock Textual 8.2.8 APIs (`stack.md` requires ≥ 0.80). `overflow-y: auto` gives "scrollbar only on overflow, no reserved gutter otherwise" as a CSS rule on `Panel`/`Backpanel`; `DescendantFocus` bubbles to every ancestor of a newly focused widget, so handling it once via a shared `_ScrollsFocusIntoView` mixin covers every way focus can land in a panel without a hook at each call site. `Tree`/`OptionList` already scroll their own cursor/highlighted row internally and needed no new code. |
| **A panel too short for one row of content just clips**, no crash, no enforced minimum height | Dev's choice in M1. Standard scrollable-container behaviour; no special-casing for the degenerate case. |
| **M2's staleness mechanism is a content hash**: `sha256(render_markdown(deck) + templates/xecjk.tex's bytes)`, compared per file against a stored stamp | Agent's choice, the roadmap's own leading candidate — automatic (nothing to remember to bump, unlike a hand-rolled `RENDERER_VERSION`), and catches a template edit for free since the hash covers it. `render_markdown` is already what `compile_file` computes on the way to pandoc, so nothing extra is parsed just to get the stamp. |
| **M2's cache lives at `~/.cache/idiomas/compile_cache.json`**, one JSON file mapping each source path to its stamp | Agent's choice, the roadmap's own suggested home — a sidecar file per PDF was rejected because it would show up inside Inspect Tree's own file browser. Missing or corrupt cache is treated as empty, never an error, which is what makes deleting it always safe. |
| **A stale-cache false positive (an unnecessary recompile) is accepted**; a false negative (silently keeping a wrong PDF) is the bug M2 exists to close and is never accepted | Agent's choice, following directly from the roadmap's own framing of the bug. |
| **M2's manual override is both `idiomas compile --force` and a second menu option, *Compile (force)*** | Agent's choice — the roadmap left "flag, menu key, or both" open. Both callers already share `compile_all`, so wiring both costs little, and a menu option (not a hidden key binding) matches `MainMenuScreen` being a plain option-list menu with no other keybinding surface. `force=True` still updates the cache afterward, so the next ordinary run stays fast. |
| **M2 shipped with no dev spec conversation and no dev hand-test** | Dev's explicit instruction: "do m2. i wont test so do it yourself." Acceptance is the mechanical checklist in `validation.md` (unit tests plus one real pandoc/xelatex run) rather than the dev's own tree. |
| **M3's chosen CJK face is Songti SC** | From `comparison.pdf` (STHeiti Light, STHeiti Medium, Hiragino Sans GB, Songti SC), the dev named Songti SC — the one serif candidate, despite `image-1.png` itself being visibly sans. Their own eyeball call; the whole point of rendering samples instead of guessing from the picture a second time was to let it win regardless of what the reference suggests. |
| **M3's comparison content is the picture's own example**, not a real notebook file or generic placeholder | Dev's answer when asked which content to render: "just copy the picture i dont understand" — read as "reproduce the picture's own text," which is simpler than pulling a real tree file and literally what was being compared against. |
| **No second comparison round for title/heading style** | Dev's choice ("Just make the call") once the font was settled — the agent designed the title block, category headings and explicit Latin font by ordinary judgment and handed over a real recompiled notebook rather than another synthetic sample. |
| **The Latin font is named via `\usepackage{lmodern}`, not `\setmainfont{Latin Modern Roman}`** | Agent's implementation-time correction to the plan. `\setmainfont` couldn't find "Latin Modern Roman" through fontspec's system-font search on this machine — it ships inside TeX Live's own font tree, not as an OS-level font — even though it's exactly what already renders by default. `lmodern` names the same choice through classical NFSS instead: same look, no dependency on system font discovery, which also matters for M7's later Linux port. |
| **Category headings are redefined with `\@startsection` directly, not `titlesec`** | Agent's implementation-time correction. `titlesec.sty` isn't in this machine's TeX Live "basic" scheme, and `\@startsection` is the same primitive `titlesec` would generate here anyway — no new required dependency for one heading rule. |
| **Hanzi are set larger than pinyin/gloss** (`{\Large ...}` in `_render_table`) | Dev's feedback after the first hand-off ("increase the size of the hanzi") — the first pass looked too even across all three columns. Pinyin and gloss stay at body size. Approved after this change ("nice"). |
| **A grammar file is one that lives under the tree's top-level `Grammar/` folder** (`store.is_grammar`, case-insensitive, top level only) | Dev's choice, settling the sprint-start Assumption below. A `Grammar/` folder nested deeper than the top level doesn't count; a file moved out of `Grammar/` becomes vocabulary again, and its `###` subtitles flatten into their category on its next save — the same fallback a vocabulary file has always given an unrecognised line. |
| **`###` is the subtitle heading** — a third level, below `##` category and above the tab-separated triads | Agent's choice, the roadmap's own obvious candidate: `##` was already the category heading. |
| **The Subtitle field lives in Entry's form, not the tree** — a `SelectField` on a grammar category: `(none)`, each existing subtitle, `(new subtitle)` with its own name field | Dev's choice, matching the backlog's own words ("the right panel changes from the rest of the folders") literally. `(uncategorized)` and `(new category)` show no Subtitle field on a grammar file, the same as on any other. |
| **Grammar entries keep the Note field** — hanzi, pinyin, translation, note, same as vocabulary | Dev's choice. How a note renders in a grammar PDF is M6's question. |
| **Subtitles are optional and exactly one level deep**; a category may mix loose entries with subtitled ones; Inspect Tree, Browse and the tag index are untouched | Dev's choice (*Minimal* scope) over a wider option that would have also shown grammar-ness or subtitles in Inspect Tree. |
| ~~**The PDF shows subtitles as plain headings under their category until M6**~~ — **settled in M6** | Already the roadmap's own framing — M5 ships the format and Entry's panel; M6 is where the layout (stacked triads, per-character pinyin, the subtitle heading's own size/weight) is designed. See the M6 rows below for the finished layout. |
| **`parser.parse` takes a `grammar: bool = False` keyword**; only `grammar=True` recognises `###`, and the writer needs no equivalent flag (it just writes whatever subtitles a deck has) | Keeps a vocabulary file's parse byte-for-byte what it always was — the whole "nothing about vocabulary changes" guarantee rests on this one flag defaulting off. Every caller that knows a file's path decides it via `store.is_grammar`, threaded through `compile_file`/`compile_all`/`autocompile_one` so a grammar PDF (and M2's staleness stamp) never silently drop a subtitle. |
| **Create with `(new subtitle)`** reuses an existing subtitle of the same name instead of duplicating it, and creates an empty subtitle when Hanzi is left blank; an empty name is a no-op. The Subtitle field then stays on whatever subtitle was just used, resetting to `(none)` only when the tree target itself changes | Lets several entries go under one subtitle in a row without re-selecting it, and lets the first entry ride along with the subtitle's own creation. |
| **`SelectField` gains `set_choices()` and a `Changed` message**, posted only from a real user pick (never from a value set in code) | Its choices were fixed at construction before this milestone (Settings' input-method lists never change); Entry's subtitle list changes per category and after a create. |
| **Picking a Subtitle option advances focus** — to Hanzi for `(none)`/an existing subtitle, to the name field for `(new subtitle)` — rather than leaving it on the collapsed select | Dev's feedback after hand-testing on `Grammar/Conjunctions.md`: picking an option is a step forward in the form, the same as `Tab`. |
| **The per-character alignment mechanism is a self-contained `\HanziPinyin` LaTeX macro**, not an external package | Dev: "whatever works best i trust you… if its too complicated just import." A `[t]`-aligned two-row `tabular` per character needs only `array`/`xcolor`, both already present in this machine's TeX Live "basic" scheme, so nothing new was required. |
| **`pinyin.py` gains `to_tone_mark_syllables(numbered) -> list[str]`**, the per-syllable half of `to_tone_marks` | Pure refactor — the existing regex already segments a numbered string into one match per syllable; `to_tone_marks` was just joining them early. |
| **`compile.py` gains `_is_hanzi` and `_pair_hanzi_pinyin(hanzi, pinyin)`**, pairing each hanzi character with its next pinyin syllable in order and a non-hanzi character (or one past the end of the syllable list) with `""` | The actual rule behind "a non-hanzi character contributes no syllable" — `...` has three non-hanzi characters and an empty pinyin field, so all three pair with nothing. |
| **A category heading (`##`) actually shifts to `\section`, not `\subsection`** — checked against pandoc's own raw output rather than assumed. The M3-era `\subsection` redefinition had been inert the whole time; it's repurposed for the subtitle heading (`###`) instead, one size down from a category | Found while implementing M6, after the dev's manual pass showed subtitle and category headings at the same size. `design.md`'s M3 entry corrected to match. |
| **`_render_grammar_table` prefixes its output with an explicit `\noindent`**, not left to the preceding heading | A grammar entries block is raw LaTeX text — one paragraph, subject to `\parindent` on its own first line regardless of what precedes it (a heading, or nothing at all for `deck.uncategorized`). |
| **An entry is up to four stacked lines — hanzi, pinyin, translation, note — with three distinct gaps**: pinyin hugs its hanzi, a small gap separates pinyin from translation, and a considerable one separates one entry from the next | Settled over three rounds of the dev's manual review against the real `Grammar/Conjunctions.md`; see the merge note above. Supersedes the original plan of a translation-line-only note — it's on its own line below, not beside the translation. |
| **The gaps are `\\[...]` line-break arguments, not standalone `\vspace` lines**, except a block's last entry, which ends its paragraph with `\par\vspace{GRAMMAR_ENTRY_GAP}` | A standalone `\vspace` line leaves a non-discardable item that turns the source newline after it into a visible space, indenting every following line; a trailing `\\[...]` right before a paragraph's end adds an extra blank line instead, which had made the gap before a subtitle bigger than between two entries. |
| **A subtitle's `\@startsection` beforeskip is `-1sp`, not `-1.2em`** — effectively zero, still negative | Zero would drop the indent-suppression `\@startsection` gets from a negative sign; `-1sp` keeps it while letting `GRAMMAR_ENTRY_GAP` alone set the gap before a subtitle, same as between two entries. |
| **The subtitle heading is body size (`\normalsize\bfseries`), prefixed with an en dash**, not `\large` | Dev's review after the first recompile: `\large` still competed with the category heading. The dash lives in the template's style argument, not in the markdown `render_markdown` emits, so the source stays the dev's own. |
| **M7's verification container runs under OrbStack, on Arch (`archlinux:latest`, amd64, emulated on Apple Silicon)** | Dev, M7 D1/D2. Plain Docker, so any runtime works. `docker/Dockerfile` is a test machine, not a distribution method. The install stays `git clone` + venv on both platforms, which the dev reconfirmed at hand-off. |
| **Linux input switching targets both fcitx5 and ibus**, whichever is running, probed once per process; neither running means a silent no-op | Dev, M7 D3. fcitx5's sources are read from its INI profile and ibus' from `gsettings`, so there's no D-Bus dependency. Unit-tested only. |
| **Linux's CJK face is Noto Serif CJK SC**; macOS keeps Songti SC | Dev, M7 D4. The Ming/serif counterpart. PDFs from the two platforms are close but not identical. Verified to use the SC glyphs, not JP ones, in the container. |
| **Install commands are picked by distro family** (`arch`/`debian`/`fedora` from `/etc/os-release`); an unknown family gets no command | Dev, M7 D5. Only Arch was run; the apt and dnf lines are correct by reading. `install_hint` returns a command or `None`, which is what keeps macOS's `doctor` messages byte-identical. |
| **The shell-config fallback is per-platform**: `.zshrc` on macOS, `.bashrc` on Linux | Dev, M7 D6. |
| **The platform layer owns every OS-specific string**: the font and how to check for it, install commands, the switcher, where input sources are enabled, what counts as a keyboard layout, and the default shell config | M7. `tests/test_no_platform_leaks.py` enforces it for code outside the layer. |
| **Arch needs `texlive-latexrecommended` and `texlive-fontsrecommended` alongside `texlive-xetex`** | Found building M7's image. The template's fontspec, xcolor, caption and lmodern come from them. `doctor` doesn't detect their absence (see Postponed). |
| **Every non-Python file under `src/idiomas/` must be declared package data** | Found in M7's container pass: `tui/app.tcss` wasn't, which crashed a non-editable install on every platform. `tests/test_packaging.py` enforces it. |

## Assumptions

Taken as given by this sprint; not verified in code or stated in the roadmap.

| Assumption | Origin | Notes |
| --- | --- | --- |
| ~~**The dev's terminal will support an inline image protocol by the time M4 is hand-tested**~~ — **settled the same day** | Dev, asked directly which terminal they run `idiomas` in: "i will install them later, assume it is installed" | Nothing image-capable was installed at sprint start — no iTerm2, kitty, WezTerm or Ghostty in `/Applications`, and Terminal.app supports no protocol at all. The dev then installed **Ghostty 1.3.1**, verified on disk. M4's done-when now names it. M4 is still specced to detect and degrade rather than assume — the app must not require Ghostty. |
| ~~**Which protocol** is M4's own call, not settled here~~ — **narrowed the same day** | Followed from the above, while the terminal was still unchosen | Ghostty settles the *primary* target: the **kitty graphics protocol**, which is also what kitty and WezTerm speak. iTerm2's simpler escape (iTerm2, VS Code's integrated terminal) is now a portability question rather than an either/or — M4's `plan.md` decides whether to carry both. |
| ~~**A grammar file is identified by living under the tree's top-level `Grammar/` folder**, by name~~ — **settled in M5's spec conversation** | The backlog: "there are two folders: grammar and vocabulary… The grammar folder will be special" | Confirmed as the folder name, top level only, case-insensitive (`store.is_grammar`). See the Decisions table. |
| ~~**The existing grammar files stay valid.**~~ — **confirmed** | Read from the dev's tree at sprint start | `Grammar/Clasificadores.md` and `Grammar/Asking for directions.md` parsed to identical decks with the grammar flag on and off, no new warnings — verified directly against the dev's real files (copied into `tests/fixtures/`), not just a synthetic one. |
| **Docker on the dev's machine can run the full toolchain** — pandoc, a TeX Live with xeCJK, and a CJK font | Follows from the Linux decision | **Didn't hold when M7 opened (2026-09-29): no container runtime was installed at all** — no Docker, OrbStack, Podman or Colima. M7's D1: the dev installs OrbStack before the hand-test. The image is Arch (`archlinux:latest`, amd64-only, so emulated on Apple Silicon — M7's D2). Whether the toolchain actually runs there is checked in M7's container pass. **Settled 2026-09-29: it runs.** The build took about 4½ minutes under emulation, and the full suite about 3 minutes. It needed pacman's sandbox disabled (it fails under emulation), plus Arch's LaTeX- and fonts-recommended TeX packages. |
| ~~**PingFang SC is not installed on the dev's machine**~~ — **moot** | Checked at sprint start: `/System/Library/Fonts` has `STHeiti Light`, `STHeiti Medium`, `Hiragino Sans GB` and `Songti.ttc`, and no PingFang | The four installed candidates produced a winner (Songti SC) on the first comparison — installing PingFang SC was never needed. |
| **M3's chosen face, Songti SC, is macOS-only** | Ships with macOS (`/System/Library/Fonts/Supplemental/Songti.ttc`), not redistributable | Confirmed, not just predicted, now that the face is settled. Drives M7's per-platform font bullet as planned — Linux needs its own counterpart (Noto Serif CJK, matching Songti's Ming/serif style, not Noto Sans). |
| **Linux input-method switching cannot be verified this sprint** | A container has no ibus/fcitx daemon and no desktop session | Whatever M7 writes for it ships best-effort, exactly as macOS's `macism` path degrades to a no-op when the tool is absent. Which framework to target — ibus, fcitx5, or both — is M7's question. **M7's D3: both.** Whichever is running is detected once per process, and with neither, switching and listing are silent no-ops. It's unit-tested only (no daemon in the container). |

## Postponed features / pending

Raised during the sprint and deliberately not implemented now. Deferred items
from the dev's own `postponedfeatures.md` are **not** duplicated here — that
file is the dev's and stays the record for them. Sprint 4's own Postponed table
stays where it is; only what this sprint actually touches is restated below.

| Item | Why postponed | Where it resurfaces |
| --- | --- | --- |
| **Windows support** | The backlog asks for Linux only. M7 adds a third platform module, which is the proof the layer works — Windows would be a fourth with no one to test it and no CJK/TeX story worked out | Whenever someone needs it; the platform layer is what makes it an addition rather than a rewrite |
| **`doctor` checking for the LaTeX packages the template loads** (fontspec, xcolor, caption, lmodern), not just `xelatex` and `xeCJK` | Found in M7: on Arch, a bare `texlive-xetex` passes `doctor` yet fails to compile. The install hint and README now name the needed packages, but `doctor` still can't tell they're missing | Whenever a missing-package compile error shows up in practice |
| **WSL** | M7's D7: out of scope. Most of the app likely works there as plain Linux, but nothing WSL-specific (opening files through Windows, a Windows-side font) is built or tested | Alongside Windows support, if ever |
| **A grammar-specific compiler for German**, or for any language but Chinese | M5/M6 describe hanzi, pinyin and a translation — a Chinese-shaped triad. German is still inert (Sprint 4's standing decision) | Whenever German stops being inert — it carries Sprint 4's own "a working German notebook" item, unscheduled |
| **Multi-page PDF preview** | M3's pane shows a page of a document; paging through it is a second question, and the notebooks are short | If a notebook grows past a page or two often enough to be annoying |
| **Persisting the tag cache** | M2 introduces the project's first on-disk cache, for compile staleness. `store.py`'s `TagCache` is still rebuilt in memory on every Browse open and could share the same home | If Browse ever feels slow on a large tree — not a problem today |
| **Per-language typography** | M3 settles one CJK face for the whole app. A German notebook would want its own type, and the template is a single fixed file until M7 makes it per-platform | Whenever German stops being inert, alongside the grammar-for-German item above |
| **The Settings submenu** (*Add a language*, *Remove a notebook*) | Still placeholders, and still not in a backlog. Sprint 4 M6 made *Input methods* real; the rest were left | Carried from Sprint 4's Postponed table; unscheduled |
