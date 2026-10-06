# M3 · Notebook typography — requirements

## Anchor (from the roadmap)

Not from the backlog. Added at sprint start on 2026-09-20: "add a milestone to
change the appearance of the files. i dont like the current font, use the
font of the picture." Asked which font, the dev corrected the agent's first
reading: "i dislike the chinese font not the translation font."

**Deliverable**, per `roadmap-sprint-5.md`: a new CJK face chosen by the dev
from rendered samples; the Latin face left visually as-is but stated
explicitly in the template; a wider typography pass (headings, title block,
margins, body size, row spacing) reviewed together as one look;
`design.md` gains the compiled notebook as a documented user-facing surface;
the font name appears in exactly one place in the code; both renderers
(vocabulary and, once M6 lands, grammar) share the same template; M2's
staleness fix makes the change checkable without a manual PDF deletion.

**Done when**, per the roadmap: a comparison PDF has been rendered and the
dev has named the face; every compiled notebook uses it; landing the
milestone rebuilds the dev's existing PDFs with no manual step; `idiomas
doctor` checks for the chosen font rather than Heiti SC, named once in the
code; `design.md` documents the notebook's typography; `stack.md`'s CJK-font
row and prose match what ships; the dev approves the result by eye against
`image-1.png`; the full test suite passes.

## Interview — settled 2026-09-22

- **Comparison content: the picture's own example, not a real notebook file
  or generic placeholder.** The dev, asked which content to render for the
  font comparison, answered "just copy the picture i dont understand" —
  meaning reproduce `image-1.png`'s own text (bold "Clima" heading, "天气"
  hanzi, "tiān qì" pinyin in a lighter/smaller weight, "clima" translation)
  once per candidate font, laid out next to the picture itself. This is
  simpler than pulling a real tree file and is literally what the dev asked
  to compare against.
- **No second round for title/heading style.** Asked whether to show
  title-block/heading options as a separate comparison after the font is
  picked, the dev chose to skip it: "Just make the call" — the agent designs
  the wider typography pass (title block, headings, margins, body size, row
  spacing) using ordinary judgment once the font is settled, and shows the
  dev the final compiled result (a real notebook, not a synthetic sample) to
  approve or send back for changes. This is a single hand-off (this
  milestone's step 9), not two.
- Everything else about scope was already settled at sprint start and is
  recorded in `notes-sprint-5.md`'s Decisions table — quoted here rather than
  re-litigated: it's the Chinese font the dev dislikes, not the Latin one;
  the Latin face stays as it looks but is made explicit
  (`\setmainfont{Latin Modern Roman}`, its current fallback, named instead of
  implied); the milestone is a full typography pass, not font-only; the face
  is chosen from rendered samples, not guessed from the picture a second
  time; the font name gets one source of truth in the code; `design.md`
  gains the compiled notebook.

## Two-step process

1. **Comparison PDF.** Render the picture's example once in each of the four
   installed CJK candidates — STHeiti Light, STHeiti Medium, Hiragino Sans
   GB, Songti SC — on today's otherwise-unchanged template, output one PDF,
   and stop. Nothing is written into `templates/xecjk.tex` yet. The dev opens
   it next to `image-1.png` and names a face (or asks for another candidate,
   e.g. installing PingFang SC, if none fits).
2. **Implementation**, once the font is named: wire the chosen font as the
   template's single source of truth, make the Latin face explicit, do the
   wider typography pass by agent judgment, update `doctor.py`, `design.md`
   and `stack.md`, and hand the dev a real compiled notebook (via `compile_all`,
   proving M2's staleness fix rebuilds it with no manual step) to approve by
   eye against `image-1.png`.

Step 2 does not start until the dev has answered step 1 — this file, `plan.md`
and `validation.md` are updated with the chosen font name as soon as the dev
names it.

## Decisions

- **The chosen face is Songti SC.** From `comparison.pdf` (STHeiti Light,
  STHeiti Medium, Hiragino Sans GB, Songti SC, each rendering the picture's
  own "Clima / 天气 / tiān qì / clima" example), the dev named Songti SC —
  the one serif candidate, despite `image-1.png` itself being visibly sans.
  This is the dev's own eyeball call, not a mismatch to correct: the
  roadmap's whole point in requiring rendered samples over guessing from the
  picture was to let the dev's actual preference win regardless of what the
  reference image suggests.
  - Family name for `\setCJKmainfont`/`\CJKfontspec`: `Songti SC`.
  - File for `doctor.py`'s installed-check:
    `/System/Library/Fonts/Supplemental/Songti.ttc` (contains Songti SC in
    Light/Regular/Black weights; fontspec's plain `Songti SC` family lookup
    resolves to Regular, matching the comparison PDF's rendering, which used
    no weight override).
- **Songti SC stays in the comparison** despite being a Ming/serif face where
  the picture is clearly sans — cheap to render, and it's the dev's call to
  eliminate it, not the agent's to leave out pre-emptively.
- **Both STHeiti weights (Light and Medium) are separate candidates** in the
  comparison, not just Light — the picture's strokes look light, but "looks
  light in a phone photo" isn't the same as "is Light in the two rendered
  side by side," so the dev judges both.
- **PingFang SC is not installed** (checked at sprint start) and is not in
  this round's comparison. If the dev's answer to step 1 is "none of these,"
  installing it is the next move, per the roadmap's own framing — not
  pre-installed speculatively now.
- **One source of truth for the font name**: a single constant in
  `compile.py` (`CJK_FONT_NAME`, plus `CJK_FONT_PATH` for `doctor.py`'s
  installed-check), passed into the template as a pandoc `-V` variable
  (`\setCJKmainfont{$cjkfont$}` replacing the hardcoded `Heiti SC`) rather
  than hardcoded in the `.tex` file itself. `doctor.py` imports both
  constants instead of keeping its own independent `CJK_FONT_PATH` and
  hardcoded check name — this is what closes the drift the roadmap calls out
  (Sprint 4 M4 already had to fix `doctor.py` lagging the template once).
- **`stack.md` is prose, not code** — its CJK-font row and *PDF* section text
  are updated by hand to match what ships, same as any other doc, not
  derived from the constant.

## Out of scope

- **M6's grammar layout** (three stacked lines, per-character pinyin
  alignment) — this milestone only settles the shared typographic look
  (font, headings, title block, spacing) that M6 then builds its layout on
  top of. The vocabulary table's three-column `longtable` shape is
  unchanged.
- **Linux's CJK font** — M7's job; whichever face is chosen here is very
  likely macOS-only per `notes-sprint-5.md`'s Assumptions, and porting it is
  explicitly deferred there.
- **Installing PingFang SC**, unless the dev's step-1 answer calls for it.
