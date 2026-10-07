# M2 · `doctor` checks the LaTeX packages — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M2 · `doctor`
checks the LaTeX packages*:

> Carried from Sprints 5–7's Postponed tables: "on Arch a bare `texlive-xetex`
> passes `doctor` and then fails to compile."
>
> **Deliverable.**
>
> - The list of LaTeX packages the template loads (beyond xeCJK, which already
>   has its own check), worked out from the template and confirmed by compiling.
> - A `doctor` check for them through `kpsewhich`, the way xeCJK is checked now,
>   reported as `required` and blocking step 1's *Next* when missing.
> - For each platform, the command that installs whatever is missing: `tlmgr
>   install …` on macOS, the pacman TeX Live packages on Arch. M3 runs these
>   commands. Until then they're only shown.
>
> **Done when.** A TeX that's missing one of the template's packages fails the
> check on step 1 and in `vimdiomas doctor`, with the package named. A complete
> TeX passes as before. The full test suite passes.

The backlog ([`../../guidelines/backlog.md`](../../guidelines/backlog.md)) has no
line for this milestone: it joined the sprint from Sprint 7's Postponed table by
the dev's choice (see [`../../guidelines/notes-sprint-8.md`](../../guidelines/notes-sprint-8.md)).
It exists because *Install missing* (M3) can only fix what `doctor` reports.

## Decisions

Settled with the dev in the spec conversation, 2026-10-07.

| Decision | Rationale |
| --- | --- |
| **One check for the whole set**, named `LaTeX packages`, `required` | Dev's choice, over one check per package and one per TeX group. One line of the wizard's ~8, and the failing line can name what is missing. Per-package would put seven lines on every screen. A per-group check would bake Arch's collection split into the check, which macOS doesn't have. |
| **When there is no `kpsewhich`, the check fails without naming packages**: `missing: needs a TeX distribution`, and an empty install command | Dev's choice. The `xelatex` line already says the real problem; seven names nobody can act on would be noise. Reporting `ok` would be a lie, and M3 rechecks after it installs a TeX. |
| **The install command is built from the missing packages only, each mapped to its platform package, deduplicated** | Dev's choice, over always installing both Arch collections. Bare `texlive-xetex` gives `sudo pacman -S texlive-latexrecommended texlive-fontsrecommended`; a TeX missing only `lmodern` gives `sudo pacman -S texlive-fontsrecommended`; on macOS `sudo tlmgr install caption xcolor`. |

## 1. The package list

Worked out from `src/vimdiomas/templates/xecjk.tex`, confirmed by compiling
(§6). The template loads, unconditionally, `fontspec`, `lmodern`, `geometry`,
`longtable`, `caption`, `array` and `xcolor`; `xeCJK` only inside
`$if(cjkfont)$`, so it stays with its own check (Sprint 6 M7) and is not in this
set. Pandoc's own `\usepackage` lines are not involved: the template replaces
pandoc's.

`lmodern` is checked twice, because the style file and the OpenType fonts it
makes `fontspec` use are separate files: a TeX can have one without the other.
`xelatex` run at 12pt (the template's size) loads `lmroman12-regular.otf` (and
its bold and italic, `lmmono12-regular.otf`, `lmsans12-regular.otf`); one probe
stands for the directory, since they ship together.

| Name shown | `kpsewhich` probe | macOS `tlmgr` package | Arch package |
| --- | --- | --- | --- |
| `fontspec` | `fontspec.sty` | `fontspec` | `texlive-latexrecommended` |
| `geometry` | `geometry.sty` | `geometry` | `texlive-latex` |
| `longtable` | `longtable.sty` | `tools` | `texlive-latex` |
| `caption` | `caption.sty` | `caption` | `texlive-latexrecommended` |
| `array` | `array.sty` | `tools` | `texlive-latex` |
| `xcolor` | `xcolor.sty` | `xcolor` | `texlive-latexrecommended` |
| `lmodern` | `lmodern.sty` | `lm` | `texlive-fontsrecommended` |
| `lmodern fonts` | `lmroman12-regular.otf` | `lm` | `texlive-fontsrecommended` |

The Arch column was read from `pacman -F` in an `archlinux:latest` container
(2026-10-07), not from memory. The same container, with only `texlive-xetex`
(which depends on `texlive-bin`, `texlive-basic` and `texlive-latex`), finds
`geometry`, `longtable` and `array` and **lacks `fontspec`, `caption`, `xcolor`,
`lmodern` and the fonts**. That corrects the notes: they list `caption`,
`xcolor` and `lmodern`'s fonts as what a bare `texlive-xetex` lacks, and
`fontspec` is missing too. On the dev's Mac (BasicTeX 2026) every probe
resolves under `/usr/local/texlive/2026basic`, matching the BasicTeX finding
that only xeCJK is missing.

The list is a table in `doctor.py` (name and probe); the two mappings are in
the platform layer (§3). A package the template starts loading later is a row,
and a test (§5) fails if the template and the table disagree.

## 2. The check

- **One `kpsewhich` call for the whole set**, `kpsewhich <probe> <probe> …`: it
  prints one path per file it finds and nothing for a missing one (exit status
  1 when any is missing, so `check=False`). Found files are matched back by
  their basename. The spinner on *Recheck* gains no extra call.
- `doctor._missing_latex_packages() -> list[str] | None`: the names of the
  missing rows, in table order, `[]` when none, and `None` when `kpsewhich`
  isn't found (`FileNotFoundError`). Tests patch this, as they patch
  `_has_xecjk`.
- A `Check` named `LaTeX packages`, `required=True`, placed right after
  `xelatex` and before xeCJK, `url=""` (there is nothing to link to, and a
  line that already names packages has no room for one), `needed_for=()`.
- A new `Check` field, **`detail: str = ""`**: the short text that says what is
  missing, shown by the wizard after `missing`. `"caption, xcolor"` for named
  packages, `"needs a TeX distribution"` when the probe is `None`. `""` for
  every other check, whose `missing` stays bare.
- **`message`** (what `vimdiomas doctor` prints) is `LaTeX packages missing:
  caption, xcolor` plus the platform's example command, `(e.g. `sudo tlmgr
  install caption xcolor`)`, in the same `_example` form as the other checks;
  with no `kpsewhich` it is `LaTeX packages can't be checked: no TeX
  distribution found (kpsewhich is missing)`, with no example.
- **`install`** is the platform's command for exactly the missing packages
  (§3), or `""` when none is missing, there's no command, or `kpsewhich` is
  missing.
- `ok` is `True` only for `[]`.

## 3. The platform layer

Each of `platform/macos.py` and `platform/linux.py` gains one function with the
same shape, exported from `platform/__init__.py` next to `install_hint`:

- `latex_install_hint(packages: list[str]) -> str | None`: takes the names from
  §1's first column, maps each through the platform's table, drops duplicates
  keeping first-seen order, and returns the one-line command: `sudo tlmgr
  install <names>` on macOS, `sudo pacman -S <names>` on Arch. `None` for an
  empty list. A name the table doesn't know raises `KeyError`: the doctor table
  and the platform tables are tested against each other (§5), so that can't
  happen in a release.
- The tables are module constants (`LATEX_PACKAGES` in each module, name →
  platform package), commented with where the column was verified.
- **The macOS command is the bare `sudo tlmgr install …`**, the way the xeCJK
  hint is today. A fresh BasicTeX needs `tlmgr update --self` before it
  (found in the BasicTeX check); that fix, and the single code path that runs
  the sequence, is M3's and covers this command and the xeCJK one together.
  Until M3 the command is only shown.
- **Arch's `xelatex` hint narrows to `sudo pacman -S texlive-xetex`.** Today it
  also lists `texlive-latexrecommended texlive-fontsrecommended` because a bare
  `texlive-xetex` can't compile (Sprint 5 M7); that is now the `LaTeX packages`
  check's job, and listing it twice would let the two drift. The comment above
  `INSTALL_HINTS` in `linux.py` is rewritten to say so. A user on a bare Arch
  who has no `xelatex` therefore sees two lines in turn: `xelatex` first, then,
  once it is installed, `LaTeX packages` with its own command.
- `tests/test_no_platform_leaks.py` keeps passing: `tlmgr` and `pacman` stay
  inside the layer, and `doctor.py` names neither.

## 4. Where it shows

- **`vimdiomas doctor`** prints the line like any other,
  `[required] LaTeX packages: <message>`, and exits 1 through `missing_for`,
  since `required` checks always count. Nothing else changes in `cli.py`.
- **Wizard step 1** lists it. A failing check with a `detail` shows `missing`
  on its own line, as today, and **the detail on the line(s) under it**,
  red, indented two spaces and wrapped to the panel's content width, so the
  columns above stay aligned and the status column is not pushed off a 60-wide
  panel:

  ```
  [required] xelatex        ok
  [required] LaTeX packages missing
    fontspec, caption, xcolor, lmodern, lmodern fonts
  [ Chinese] xeCJK          missing <-- https://github.com/texjporg/xecjk
  ```

  `_pending_checks_text` (the *Recheck* spinner) does not show a detail. The
  name column widens to 14 for `LaTeX packages` by the existing
  `_name_width` rule; the macOS layout therefore changes by that width, a
  consequence accepted here rather than special-cased.
- **`Next` is blocked** by the existing `_blocking()` rule (`required` and not
  ok); its message ("A required dependency is still missing; fix it and
  recheck.") is unchanged.
- **Step 3 and Settings › Add a language**, through
  `tui/screens/dependencies.py`: `missing_for(checks, languages)` already
  includes a missing `required` check, so a TeX that lost a package between
  step 1 and step 3 refuses the language. `refusal()` words a check with a
  `detail` as `<name> missing: <detail>.` (`LaTeX packages missing: caption,
  xcolor.`) instead of "is missing", then the command or message as it does
  now. `_offerable` is unchanged: the check has no `needed_for`, so nothing is
  offered and the language is refused; installing it is M3's.
- **The `Check` for `LaTeX packages` is never offered for install** in M2.
  Offering is M3.

## 5. Tests

- `tests/test_doctor.py`: required checks become `pandoc`, `xelatex` and
  `LaTeX packages`; `_all_missing` patches `_missing_latex_packages`; the
  macOS parity tests (`test_macos_messages_are_unchanged`, the URL one) are
  updated for the new check; the Arch message test gets the narrowed `xelatex`
  hint and the new line.
- New doctor tests: complete → `ok`, empty `detail`, empty `install`; some
  missing → named in table order, `detail` and `message` list them, `install`
  covers only them (macOS and Arch shapes, with the platform patched the way
  `_as_linux_arch` does); `None` → not ok, `detail` is `needs a TeX
  distribution`, `install` empty; `missing_for(..., ["German"])` and `([])`
  contain `LaTeX packages` when it is missing.
- `_missing_latex_packages` itself, with `subprocess.run` patched: some paths
  printed, none printed, `FileNotFoundError`; one call for the whole set.
- A consistency test: every `\usepackage` in `xecjk.tex` outside the
  `$if(cjkfont)$` block has a row in the table, and the table's names are
  exactly the keys of each platform's `LATEX_PACKAGES`.
- `tests/test_platform.py` / `test_platform_linux.py`: `latex_install_hint`
  per platform: one package, two sharing a target (deduplicated), the empty
  list, order.
- `tests/test_tui_wizard.py`: `_FakeCheck` gains `detail`; the failing line
  shows `missing` and the detail underneath, wrapped, with no line wider than
  the panel's content; an ok check shows no detail; a blocked `LaTeX packages`
  blocks *Next*; the spinner text has no detail.
- `tests/test_tui_dependencies.py`: `refusal()` wording for a check with a
  detail.

## 6. Confirmed by compiling

The package list is a claim about what compiling needs, so it is checked the
way compiling checks it, not only by reading the template:

- On the Arch image of §7 with `texlive-xetex` alone, compiling a fixture
  fails at the first missing file (`fontspec.sty`); installing exactly the
  command the check printed makes both a German and a Chinese fixture compile.
- On the dev's Mac the check passes on BasicTeX 2026 and MacTeX alike (every
  probe resolves), and the notebooks compile as before.

The exact commands are in [`validation.md`](validation.md).

## 7. Specs and docs

- **`specs/current/stack.md`**: the *Platform layer* bullet lists
  `latex_install_hint(packages)` next to `install_hint`; the `doctor` bullet
  names the new required check and `detail`; the Arch table row for xelatex is
  split to say `texlive-xetex` provides xelatex and the packages check asks for
  the rest; the macOS "Verified present" table gets the packages row; the line
  that says `doctor` prints "exactly that line" for xeCJK stays as it is (xeCJK
  is untouched).
- **`specs/current/design.md`**: the dependency conventions (*A language's
  missing dependencies* and the step-1 description) gain the one rule this
  milestone adds: a failing check can say what is missing, on the line under
  it. Only that; the larger rewrite of "only a language's own dependencies are
  ever offered" is M3's.
- **`docker/Dockerfile`** is untouched: it installs every package up front, and
  the bare image M3 needs is M3's decision. §6's bare run is a throwaway
  container, not a file.

## 8. Not in this milestone

- Running any install command, or offering one: M3.
- Removing the install hints from messages ("No instructions should be shown"):
  M3 does it on step 1; this milestone adds a hint in the same shape as the
  existing ones and M3 removes all of them together.
- `tlmgr update --self` before `tlmgr install`: M3.
- Finding a TeX that is installed but not on `PATH`: M3. `kpsewhich` is looked
  up on `PATH` here, as `xelatex` is today.
- Probing the xeCJK or CJK-font checks differently. They keep their own checks.
- Any change to the template or to what compiling does.
