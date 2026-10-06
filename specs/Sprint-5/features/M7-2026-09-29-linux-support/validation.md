# M7 · Linux support — validation

Grounded in the roadmap's done-when condition, made concrete. All of it must
hold before the branch is merged.

## Automated, on macOS

- `pytest` passes: the full suite, including every new test in `plan.md`
  group 3.
- Covered specifically:
  - `idiomas.platform` dispatches to `macos` on Darwin (and to `linux` on
    Linux, which is exercised in the container run below).
  - `linux.py`'s units, with no real Linux needed:
    - `xdg-open`;
    - the `fc-list` font check;
    - fcitx5 / ibus / none detection and switching;
    - fcitx5 profile and ibus `gsettings` parsing, including the empty and
      garbage inputs;
    - distro-family mapping;
    - the install-hint table plus `None` for an unknown family;
    - display names.
  - **The leak test**: no string literal in code under `src/idiomas/`
    outside `platform/` contains `brew `, `macism`, `/System/`,
    `/Library/`, `defaults export` or `xdg-open`.
  - **Packaging** (R12): every non-Python file under `src/idiomas/` is
    declared as package data, so a non-editable install ships it.
  - **macOS parity**: `doctor.run()`'s check names, required flags and
    messages on macOS are exactly what they were on `main`, asserted
    string for string. `shell_config_path()` still falls back to `.zshrc`
    on macOS. `CJK_FONT_NAME` is still `Songti SC`.
- `idiomas doctor` on the dev's Mac prints the same output as on `main`
  (diffed by hand against a `main` checkout).

## Automated, in the container

Built with
`docker build --platform linux/amd64 -t idiomas-linux docker/` under
OrbStack.

- [x] The image builds from a clean cache. Its build fails outright if
  Arch's `python` is below 3.14. *(2026-09-29: `--no-cache` build OK; Arch
  ships Python 3.14.7, pandoc 3.11 and TeX Live 2026.)*
- [x] Inside it, with the repo mounted and `pip install -e ".[dev]"`,
  `pytest` passes: the full suite, **integration tests included**, meaning
  real pandoc and xelatex producing PDFs with Noto Serif CJK SC. The
  commands are the README's *Testing on Linux (Docker)* ones.
  *(2026-09-29, fresh container: 690 passed, 6 skipped — the macOS-parity
  tests.)*

## Container pass, by the agent

*The dev handed this pass to the agent on 2026-09-29 ("i can install
orbstack and then you test"). The dev installed OrbStack; the agent runs
everything below itself. The wizard is driven through a scripted terminal
session in the container, and the PDFs are checked with `pdffonts` and
rendered to images to be looked at.*

Prerequisite: `brew install orbstack`, then start OrbStack once.

In the container: `docker run --rm -it --platform linux/amd64 -e
TERM_PROGRAM -v "$PWD":/src:ro idiomas-linux`.

*Results from 2026-09-29, on a fresh container from the final image. The
first pass found the packaging, texlive, advisory, alignment and test
isolation issues in `requirements.md` R12–R13; everything below is the
re-run after those fixes.*

- [x] Following the README's **Linux** section verbatim installs Idiomas.
      The one pre-merge exception: step 1 clones the mounted branch
      (`git clone -b 2026-09-29-m7-linux-support /src
      ~/.local/share/idiomas`), because GitHub's `main` doesn't have Linux
      support until this merges. The README's *Testing on Linux (Docker)*
      section documents that substitution.
- [x] `idiomas` launches the installation wizard, which:
  - [x] shows every required dependency as ok and the optional ones
        (`fcitx5 or ibus`, `nvim`) as missing, with install hints, in
        aligned columns;
  - [x] says "Add one in fcitx5's or ibus' own settings" on the
        input-methods step, not System Settings;
  - [x] writes a config;
  - [x] links `idiomas` into `~/.local/bin`;
  - [x] adds the `PATH` line to **`~/.bashrc`**, not `~/.zshrc`. A new
        *interactive* login shell (`bash -il`) in the container then
        finds `idiomas` on `PATH`. A non-interactive `bash -l` doesn't,
        because Arch's stock `~/.bashrc` returns early for non-interactive
        shells, before the appended line. That's the distro's own
        behaviour, and a real new terminal is interactive.
- [x] `idiomas doctor` lists `pacman` install commands and contains no
      `brew`.
- [x] Add a vocabulary entry and a grammar entry with a subtitle, compile,
      and copy the PDFs out (`docker cp`). `pdffonts` shows
      **Noto Serif CJK SC** embedded; rendered, the hanzi are correct and
      the grammar PDF has M6's stacked layout with the pinyin aligned under
      each hanzi. *(Both entries were added through Enter vocabulary: 葡萄
      in Food › Fruits, and 并且 under Grammar › Conjunctions › "copulative
      conjunction". The grammar entry's translation was mistyped into Note
      while driving the form and corrected by hand in the file. The
      embedded name reads `NotoSerifCJKjp`, because Noto's collection
      shares one CFF name across faces. Rendering 骨直 with the SC and JP
      faces gives different images, and fontconfig resolves "Noto Serif CJK
      SC" to face index 2 of `NotoSerifCJK-Regular.ttc`, so the Simplified
      glyphs are the ones used.)*
- [x] Extra: Inspect Tree in the container, without kitty graphics, falls
      back to the `pdftotext` text. Enter on a PDF with no `xdg-open`
      installed does nothing and doesn't crash.

## Manual, by the dev

- [ ] Optional: Inspect Tree's PDF preview, run in the container from
      Ghostty with `-e TERM_PROGRAM`, renders the page. If it doesn't, it
      degrades to the message instead of breaking. (The agent can't see
      kitty graphics, only that the fallback doesn't break.)

On macOS, from this branch:

*2026-09-29: the dev approved the merge ("ok do it") after asking whether
a Linux user gets the same program as a Mac user. There was no separate
hand-check pass. The dev's `idiomas` is an editable install of this
checkout, so their own use today ("idiomas works") ran this branch's code
on macOS. Mechanically, the parity tests pin `doctor`'s messages, the
input-source advisories, the wizard's layout, the `.zshrc` fallback and
Songti SC, and `idiomas doctor`'s output is byte-identical to `main`'s.*

- [ ] Entry, Browse, Inspect Tree (preview included), compile, the wizard
      and `idiomas doctor` all behave exactly as before. Input switching
      still works in the hanzi field.
- [ ] Recompiling the real tree needs no manual step. It is a no-op if
      nothing changed: the font name on macOS is unchanged, so M2's stamps
      are too.

## Not validated (accepted)

- Linux input switching against a real fcitx5 or ibus: there's no desktop
  session in the container (the sprint notes' Assumption, and D3).
- Debian/Ubuntu and Fedora install lines: correct by reading, not run (D5).
- WSL (D7).
