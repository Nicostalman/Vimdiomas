# M3 · Notebook typography — plan

## 0. Font decided: Songti SC

Comparison PDF reviewed by the dev on 2026-09-22; answer: Songti SC. Group 2
below uses `CJK_FONT_NAME = "Songti SC"` and
`CJK_FONT_PATH = Path("/System/Library/Fonts/Supplemental/Songti.ttc")`.

## 1. Comparison PDF (blocks everything below) — done

- New standalone LaTeX file, kept in this spec folder (not in `src/`, since
  it's a one-off decision aid, not shipped code):
  `specs/Sprint-5/features/M3-2026-09-22-notebook-typography/comparison.tex`.
- Content: one block per candidate — **STHeiti Light**, **STHeiti Medium**,
  **Hiragino Sans GB**, **Songti SC** — each reproducing `image-1.png`'s own
  example under a label naming the face:
  - Bold "Clima" heading.
  - "天气" in that block's CJK face (`\newfontfamily` per block, via
    `xeCJK`'s `\CJKfontspec`/`\setCJKmainfont` switched per block — no need
    to touch `templates/xecjk.tex` for this).
  - "tiān qì" underneath, smaller and in a lighter gray, matching the
    picture's own pinyin treatment as closely as a first pass allows (this
    detail isn't the point of the comparison — the CJK face is).
  - "clima" translation line.
- Compile directly with `xelatex comparison.tex` (no pandoc, no
  `compile.py`) — output `comparison.pdf` alongside it in the same folder.
- Hand off to the dev: open `comparison.pdf` next to `image-1.png` and name a
  face. If the dev asks for a candidate not on the list (e.g. PingFang SC),
  install it and re-render before proceeding.
- **Stop here until the dev answers.** Nothing below starts until a face is
  named. `requirements.md`'s Decisions section is updated with the chosen
  face as soon as it's picked.

## 2. One source of truth for the font name (`compile.py`) — done

- Add two module-level constants next to `CACHE_PATH`:
  - `CJK_FONT_NAME = "Songti SC"` — what goes into `\setCJKmainfont`.
  - `CJK_FONT_PATH = Path("/System/Library/Fonts/Supplemental/Songti.ttc")` —
    what `doctor.py`'s installed-check needs.
- `compile_file`'s pandoc invocation gains `-V`, `f"cjkfont={CJK_FONT_NAME}"`
  in its argument list.
- `_stamp_for`'s inputs are unchanged — the constant lives in Python, not the
  template, so a font change alone (no template edit) would need its own
  cache-busting path. Since `CJK_FONT_NAME` is only ever changed by editing
  `compile.py`, and `compile.py` isn't part of `_template_bytes()`'s hash,
  add `CJK_FONT_NAME.encode()` into `_stamp_for`'s hashed input (alongside
  `markdown` and `template_bytes`) so a future font change is caught by M2's
  mechanism the same way a template edit is — otherwise this milestone would
  ship a font change that M2 itself can't detect next time.

## 3. Template changes (`templates/xecjk.tex`) — done

- `\setCJKmainfont{Heiti SC}` → `\setCJKmainfont{$cjkfont$}`, a pandoc
  template variable, matching `$title$`/`$body$`'s existing style.
- **Actual mechanism for the Latin face: `\usepackage{lmodern}`, not
  `\setmainfont{Latin Modern Roman}` as first planned.** Tried first;
  fontspec's system-font search can't find "Latin Modern Roman" by that name
  on this machine — it ships inside TeX Live's own OTF tree, not as a font
  the OS's font system knows about, so `\setmainfont` fails with "font
  cannot be found" even though it's exactly what's already rendering by
  default. `lmodern` names the same choice through classical NFSS instead,
  with no visual change and no dependency on system font discovery (more
  portable, which also matters for M7's Linux port later).
- Title block: replaced the bare `\maketitle` (and the now-unused
  `\title{}`/`\author{}`/`\date{}`) with `{\LARGE\bfseries $title$}\par`, a
  thin `\hrule`, then vertical space before the body — `\noindent` in front
  so the title itself isn't paragraph-indented.
- Category headings (`##`, `\subsection` after `--shift-heading-level-by=-1`):
  redefined directly with `\@startsection` (`\Large\bfseries`, spaced above
  and below) rather than via the `titlesec` package — `titlesec.sty` isn't
  present in this machine's TeX Live "basic" scheme, and `\@startsection` is
  the same primitive `titlesec` itself would generate here. No renumbering
  change (`secnumdepth` was already `-1`).
- Margins (`margin=1in`), body size (`12pt`), row spacing
  (`\arraystretch{1.6}`): reviewed together with the above and kept as-is.
- **Hanzi sized up, per the dev's feedback on the first hand-off.**
  `_render_table` (`compile.py`) wraps the hanzi cell in `{\Large ...}`;
  pinyin and gloss stay at body size. Not in the original plan — added when
  the dev asked for it after seeing the first recompiled notebook.
- Add a short comment above the CJK/Latin font lines is unnecessary — the
  variable name and `compile.py`'s constant are already self-explanatory;
  don't add one just to restate what's obvious from the code.

## 4. `doctor.py` — done

- Remove the hardcoded `CJK_FONT_PATH = "/System/Library/Fonts/STHeiti Light.ttc"`.
- `from idiomas.compile import CJK_FONT_NAME, CJK_FONT_PATH`.
- The CJK-font `Check`'s `name` field becomes `CJK_FONT_NAME` instead of the
  literal `"Heiti SC"`; its `message` interpolates `CJK_FONT_NAME` instead of
  the hardcoded face name.

## 5. `design.md` — done

- New section, after the existing navigation/keys content, titled something
  like *The compiled notebook* — the project's first documentation of the
  PDF as a user-facing surface. States: the CJK face (named, with the reason
  it was picked being "the dev's eye against a reference image," not
  re-litigated here), the Latin face, the title-block treatment, margins,
  body size, row spacing — as a standing convention M6 (the grammar
  renderer) builds its layout on top of rather than re-deciding.

## 6. `stack.md` — done (also `readme.md`, not originally listed here: its
dependency table names the font too and would otherwise have drifted)

- CJK-font summary-table row: `Heiti SC` → the chosen face.
- *PDF* section prose (`"The CJK font is **Heiti SC**, present by default on
  macOS..."` and the doctor-check line further down) updated to match,
  including the font's install status (all four candidates are macOS
  system fonts — "nothing needs installing" stays true regardless of which
  wins, unless the dev asks for PingFang SC, which also ships with macOS
  10.15+ but may need enabling via Simplified Chinese input source — verify
  at implementation time only if PingFang is the pick).

## 7. Tests — done

- `tests/test_compile.py`: a unit test asserting `CJK_FONT_NAME` appears in
  the pandoc invocation's arguments (monkeypatch `subprocess.run`, assert
  `-V` / `cjkfont=<name>` is present) — guards against the variable being
  silently dropped later.
- `tests/test_doctor.py` (or wherever the CJK check is tested): update any
  test asserting the check's name/message is `"Heiti SC"`-shaped to assert
  against `CJK_FONT_NAME` instead, so the test doesn't itself become a
  second hardcoded copy of the font name.
- No new integration test beyond the existing real pandoc/xelatex compile
  test — it already exercises the template end to end and will naturally
  cover the new `$cjkfont$`/`$mainfont$`/title-block lines.

## 8. Real-tree rebuild and hand-off — done

- Ran `idiomas compile` (no `--force` needed) against the dev's real tree
  (`~/Documents/Idiomas`, from `~/.config/idiomas/config.toml`): all 5
  existing PDFs reported rebuilt, none skipped — confirming M2's staleness
  mechanism catches the font change on its own, with nothing deleted by
  hand. This is also the milestone's own proof that M2 works, per the
  roadmap's framing.
- Presented two real recompiled notebooks (`skel.pdf`, a short vocabulary
  file with one entry; `Clasificadores.pdf`, a grammar file with several
  categories including empty ones) for the eyeball approval against
  `image-1.png` — the milestone's step-9 hand-off, not a second comparison
  round (the dev opted out of one in the interview). **Awaiting the dev's
  approval or change requests.**
