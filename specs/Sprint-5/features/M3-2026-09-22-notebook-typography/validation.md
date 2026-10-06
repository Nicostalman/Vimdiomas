# M3 · Notebook typography — validation

Ground truth is the roadmap's done-when, read together with the interview's
two-step process (comparison, then implementation).

- [x] **A comparison PDF exists and the dev has named a face.**
      `comparison.pdf` renders all four candidates (STHeiti Light, STHeiti
      Medium, Hiragino Sans GB, Songti SC) against the picture's own example;
      the dev named **Songti SC**, recorded in `requirements.md`'s Decisions
      section.
- [x] **Every compiled notebook uses the chosen face.** `CJK_FONT_NAME =
      "Songti SC"` in `compile.py`; `templates/xecjk.tex`'s
      `\setCJKmainfont{$cjkfont$}` receives it via the pandoc `-V` variable
      (not hardcoded in the template) — verified both by
      `test_compile_file_passes_cjk_font_to_pandoc` and by a real recompile
      of the dev's tree.
- [x] **The Latin face is explicit.** `templates/xecjk.tex` loads
      `\usepackage{lmodern}` rather than `\setmainfont{Latin Modern Roman}`
      as planned — fontspec's system-font search can't find "Latin Modern
      Roman" by name on this machine (it ships inside TeX Live, not as a
      system font), so `lmodern`'s classic NFSS route is the mechanism that
      actually names the choice without depending on font discovery. Visual
      output is unchanged (confirmed against the pre-M3 PDFs).
- [x] **Landing the milestone rebuilds the dev's existing PDFs with no
      manual step.** `idiomas compile` (no `--force`) against the dev's real
      tree (`~/Documents/Idiomas`) reported all 5 existing PDFs rebuilt, none
      skipped — M2's staleness mechanism caught the template/font change via
      `_stamp_for`'s new `CJK_FONT_NAME` input, nothing deleted by hand.
- [x] **`idiomas doctor` checks the chosen font, named once.** The CJK-font
      `Check`'s name and message reference `CJK_FONT_NAME`, imported from
      `compile.py`; the string `"Songti SC"` appears in exactly one place in
      the code (`compile.py`'s constant definition) plus `stack.md`'s and
      `readme.md`'s prose (docs, not code — see `requirements.md`'s
      Decisions). `test_reports_missing_font_by_its_name` and related
      `test_doctor.py`/`test_tui_wizard.py` tests updated accordingly.
- [x] **`design.md` documents the notebook's typography** — CJK face, Latin
      face, title-block treatment, margins, body size, row spacing — as a
      standing convention, in a new *The compiled notebook* section.
- [x] **`stack.md`'s CJK-font row and *PDF* section prose match what
      shipped** — updated to Songti SC, no leftover mention of Heiti SC as
      the current choice (the one remaining mention is explicitly historical,
      describing the Sprint 4 M4 drift this milestone's one-source-of-truth
      change now prevents from recurring). `readme.md`'s dependency table
      updated too.
- [x] **The dev approves the final result by eye against `image-1.png`**,
      using a real recompiled notebook from their tree, not a synthetic
      sample — this milestone's step-9 hand-off. One round of feedback (hanzi
      too small relative to pinyin/gloss) was applied — `_render_table` now
      wraps the hanzi cell in `{\Large ...}` — and the dev approved the
      result ("nice").
- [x] **Vocabulary rendering is otherwise unchanged**: the three-column
      `longtable` shape, tone-marked pinyin, LaTeX escaping, and the note
      parenthetical are untouched (confirmed against `Clasificadores.pdf`
      and `skel.pdf` from the dev's real tree) — only the surrounding
      typography (fonts, title, headings, margins, spacing) changed. `M6`
      (not this milestone) is where the grammar layout itself changes.
- [x] **The full test suite passes**: `python -m pytest` — 485 passed, run
      in this environment with pandoc/xelatex available (integration tests
      included).
