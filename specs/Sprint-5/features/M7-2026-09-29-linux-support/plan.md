# M7 · Linux support — plan

Task groups, ordered so later groups depend only on earlier ones. References
like (R3) point to items in `requirements.md`'s *Scope → In*, and (D5) to its
decisions table.

## 1. Widen the platform layer's surface (macOS behaviour unchanged)

- `platform/macos.py` gains:
  - `CJK_FONT_NAME = "Songti SC"` and
    `CJK_FONT_PATH = "/System/Library/Fonts/Supplemental/Songti.ttc"`, moved
    from `compile.py`;
  - `cjk_font_installed()` with no arguments, checking its own
    `CJK_FONT_PATH`;
  - `DEFAULT_SHELL_CONFIG = ".zshrc"`;
  - `CJK_FONT_URL = ""` (the font ships with macOS);
  - `install_hint(dep)` returning **today's exact commands** (`brew install
    pandoc`, `sudo tlmgr install xecjk`, `brew install
    laishulu/homebrew/macism`, `brew install neovim`, `brew install poppler`)
    and `None` for xelatex and the font, which today name none;
  - `input_switcher()` → `("macism", shutil.which("macism") is not None,
    "https://github.com/laishulu/macism")`.
- `platform/__init__.py`: re-export the new names from `macos` on Darwin, and
  add inert equivalents to the non-macOS fallback branch (`CJK_FONT_NAME` =
  `"Noto Serif CJK SC"`, `CJK_FONT_PATH = None`, `CJK_FONT_URL = ""`,
  `install_hint` → `None`, `input_switcher` →
  `("input switcher", False, "")`, `DEFAULT_SHELL_CONFIG = ".profile"`).
- `compile.py`: drop `CJK_FONT_NAME`/`CJK_FONT_PATH` and import
  `CJK_FONT_NAME` from `idiomas.platform`.
- `doctor.py`:
  - read the font name and `cjk_font_installed()` from the layer;
  - every install command comes from `install_hint(...)`, appended as
    `` (e.g. `…`)`` when it isn't `None`; the xeCJK message stays the bare
    command, as today;
  - the `macism` check becomes `name, ok, url = input_switcher()`;
  - the module docstring is made platform-neutral.
- `tui/screens/inspect.py`: `MSG_NO_POPPLER` is built from
  `install_hint("pdftoppm")`.
- `install.py`: `shell_config_path()` falls back to
  `platform.DEFAULT_SHELL_CONFIG`. `LinkState.UNSUPPORTED`'s docstring
  becomes "neither macOS nor Linux".
- Update the tests this touches (`test_doctor`, `test_install`,
  `test_compile`, `test_platform`, `test_tui_wizard`) **without changing any
  macOS expectation**. Every macOS string the suite asserted before must
  still be asserted, now via the layer.
- Checkpoint: the full suite is green on macOS, and `idiomas doctor` output
  is byte-identical to `main`'s.

## 2. `platform/linux.py`

- `open_file(path)`: `subprocess.run(["xdg-open", str(path)], check=False)`,
  catching `FileNotFoundError`.
- `CJK_FONT_NAME = "Noto Serif CJK SC"`. `cjk_font_installed()` runs
  `fc-list ":family=Noto Serif CJK SC" family` and reports whether the
  output is non-empty. A missing `fc-list` or a failing call means `False`.
- `user_bin_dir()` → `Path.home() / ".local" / "bin"`.
- `DEFAULT_SHELL_CONFIG = ".bashrc"` (D6).
- Input methods (D3):
  - `_framework()` → `"fcitx5"` if `fcitx5-remote` exits 0 (which means the
    daemon is up), else `"ibus"` if `ibus engine` exits 0, else `None`. It's
    wrapped in `functools.cache`, because `switch_input_source` is called on
    every focus change and must not spawn two probes each time.
  - `switch_input_source(id)`: `fcitx5-remote -s <id>` or
    `ibus engine <id>`, a no-op on `None`. It swallows `FileNotFoundError`
    and `CalledProcessError`, like `macos.py`.
  - `list_input_sources()`:
    - fcitx5 → `_fcitx5_profile_sources(path)` parses
      `~/.config/fcitx5/profile` with `configparser` (`[Groups/0/Items/N]` →
      `Name`, keeping order and dropping duplicates);
    - ibus → `_ibus_preload_engines(text)` parses `gsettings get
      org.freedesktop.ibus.general preload-engines` output (`['xkb:us::eng',
      'libpinyin']`, and `@as []` for empty);
    - `[]` otherwise. It never raises.
  - `DISPLAY_NAMES` is a small table for the usual engines and layouts, with
    `display_name()` falling back to the raw ID.
- `input_switcher()` → `("fcitx5 or ibus", which("fcitx5-remote") or
  which("ibus"), "https://github.com/fcitx/fcitx5")`.
- `distro_family()` reads `platform.freedesktop_os_release()` and maps
  `ID` plus `ID_LIKE` tokens to `"arch"` (arch, manjaro, endeavouros),
  `"debian"` (debian, ubuntu, linuxmint, pop) or `"fedora"` (fedora, rhel,
  centos, rocky, almalinux). Anything else is `None`, and so is an
  `OSError`.
- `CJK_FONT_PATH = None`,
  `CJK_FONT_URL = "https://github.com/notofonts/noto-cjk"`.
- `install_hint(dep)`: a `{family: {dep: command}}` table (D5), `None` when
  the family is `None`:

  | dep | arch | debian | fedora |
  | --- | --- | --- | --- |
  | pandoc | `sudo pacman -S pandoc-cli` | `sudo apt install pandoc` | `sudo dnf install pandoc` |
  | xelatex | `sudo pacman -S texlive-xetex texlive-latexrecommended texlive-fontsrecommended` | `sudo apt install texlive-xetex texlive-latex-recommended texlive-fonts-recommended` | `sudo dnf install texlive-xetex texlive-collection-latexrecommended texlive-collection-fontsrecommended` |
  | xecjk | `sudo pacman -S texlive-langchinese` | `sudo apt install texlive-lang-chinese` | `sudo dnf install texlive-xecjk` |
  | cjk-font | `sudo pacman -S noto-fonts-cjk` | `sudo apt install fonts-noto-cjk` | `sudo dnf install google-noto-serif-cjk-fonts` |
  | input-switcher | `sudo pacman -S fcitx5-im fcitx5-chinese-addons` | `sudo apt install fcitx5 fcitx5-chinese-addons` | `sudo dnf install fcitx5 fcitx5-chinese-addons` |
  | nvim | `sudo pacman -S neovim` | `sudo apt install neovim` | `sudo dnf install neovim` |
  | pdftoppm | `sudo pacman -S poppler` | `sudo apt install poppler-utils` | `sudo dnf install poppler-utils` |

  *(The xelatex row gained the recommended LaTeX and font collections in
  the container pass. On Arch, `texlive-xetex` alone fails to compile:
  `fontspec.sty`, `xcolor.sty` and `caption.sty` are in
  `texlive-latexrecommended`, and lmodern's `lmroman12-regular.otf` is in
  `texlive-fontsrecommended`. `doctor` still passes without them, because
  it checks for the `xelatex` binary and `xeCJK.sty` only.)*

  The Arch column is confirmed against the real container in group 4. Any
  package name that proves wrong is corrected here and in the code together.
- `platform/__init__.py`: an `elif _platform.system() == "Linux":` branch
  importing from `linux`. The module docstring is rewritten: macOS and
  Linux are implemented, everything else gets no-ops.

## 3. Tests for Linux, runnable on macOS

- `tests/test_platform_linux.py`, importing `idiomas.platform.linux`
  directly with `subprocess.run`/`shutil.which` monkeypatched:
  - `open_file` calls `xdg-open`, and a missing `xdg-open` is a no-op;
  - `cjk_font_installed` is true on non-empty `fc-list` output, and false on
    empty output or a missing tool;
  - `_framework` prefers fcitx5, falls back to ibus, or gives `None`. The
    cache is cleared between tests;
  - `switch_input_source` issues the right command per framework and is a
    no-op with none;
  - `_fcitx5_profile_sources` handles a realistic profile fixture
    (two groups, a duplicate, a missing file → `[]`);
  - `_ibus_preload_engines` handles `['xkb:us::eng', 'libpinyin']`,
    `@as []`, and garbage → `[]`;
  - `distro_family` covers arch, ubuntu via `ID_LIKE=debian`, rocky via
    `ID_LIKE="rhel centos fedora"`, an unknown ID, and `OSError`;
  - `install_hint` gives the table's lines per family and `None` for
    `None`;
  - `display_name` covers a table hit and the raw-ID fallback.
- `tests/test_platform.py`: the dispatch test asserts `macos` on Darwin and
  `linux` on Linux (`platform.system()`), and is skipped elsewhere.
- **Leak test** (R8), `tests/test_no_platform_leaks.py`: every `.py` under
  `src/idiomas/` outside `platform/` is parsed with `ast`, and any
  **string token** containing `brew `, `macism`, `/System/`, `/Library/`,
  `defaults export` or `xdg-open` fails. Comments and docstrings are skipped,
  and so are string tokens that are docstrings, so historical notes stay
  allowed.
- Every existing test that assumes macOS is made platform-aware: it asserts
  through the layer's own values, or is skipped off-Darwin when it's
  genuinely macOS-only (`macos.py`'s own tests stay unconditional, since
  they never touch the real OS).

## 4. The verification image

*Status (2026-09-29): done. The dev installed OrbStack and handed the
container pass to the agent. Its findings (pacman's sandbox, the Arch
TeX packages, the missing `.tcss` package data, the macOS-worded
advisories, the wizard's column width, and `test_main`'s config
isolation) are folded into this plan, `requirements.md` R12–R13 and
`validation.md`. OrbStack's `docker` lives at
`/Applications/OrbStack.app/Contents/MacOS/xbin/docker` with its socket at
`~/.orbstack/run/docker.sock`, until OrbStack's own shell setup puts them
on `PATH`.*

- `docker/Dockerfile`:
  - `FROM archlinux:latest`;
  - `DisableSandbox` added to `/etc/pacman.conf` first. *(Found on the
    first real build: pacman 7's seccomp-restricted download sandbox fails
    under OrbStack's amd64 emulation with "error restricting syscalls via
    seccomp".)*;
  - `pacman -Syu --noconfirm` with `pandoc-cli texlive-xetex
    texlive-langchinese noto-fonts-cjk poppler git python fontconfig`;
  - a build step that asserts `python` is ≥ 3.14 and fails the build
    otherwise. *(Changed during implementation from "add `uv` if it's
    below": a `uv`-provided Python would make the README's `python3 -m
    venv` step untrue inside the image. If the assertion fails, the fix is
    decided with the dev then.)*;
  - `git config --system --add safe.directory '*'`, so the bind-mounted
    repo (owned by the host's uid) can be cloned;
  - a `learner` user with `/bin/bash`, `SHELL=/bin/bash`, and
    `WORKDIR /home/learner`;
  - no Idiomas install.
- *(Found in the container pass: R12.)* `pyproject.toml`'s package-data
  gains `tui/*.tcss`. `tests/test_packaging.py` fails if any non-Python
  file under `src/idiomas/` isn't covered by package-data.
- The repo is mounted read-only at `/src`. Every use inside the container
  **clones** it rather than working in the mount, which keeps the host's
  macOS `.venv` and build artefacts out of it.
- `docker/README.md` is kept short (the build and run lines only) and points
  to the main README.
- Build it for real (`docker build --platform linux/amd64 -t idiomas-linux
  docker/`) and inside it:
  - follow the README's Linux section verbatim: clone the bind-mounted repo,
    create the venv, `pip install .`, run `idiomas`, complete the wizard;
  - `idiomas doctor` shows all required checks ok, pacman lines, and no
    `brew`;
  - compile a vocabulary file and a grammar file (fixtures copied from
    `tests/fixtures/`), then `pdffonts` shows `NotoSerifCJK` embedded;
  - `pip install -e ".[dev]" && pytest` passes, integration tests included.
- Correct the plan, the requirements and the code for whatever the real
  build contradicts (package names, the Python version) as it's found.

## 5. Documentation

- `README.md`:
  - intro: macOS **or Linux**;
  - a *Linux* dependency table with Arch / Debian-Ubuntu / Fedora columns
    matching group 2's table, plus Python and git rows (the macOS table
    has Python too; git is needed for the clone and isn't a given on a
    minimal distro);
  - install steps shared where identical;
  - `~/.bashrc` is mentioned for the `PATH` step;
  - the contributor section gets *Testing on Linux (Docker)*: build, an
    interactive run with `-e TERM_PROGRAM` and the repo mounted at `/src`,
    cloning a branch from the mount in place of GitHub (for pre-merge
    testing), and a `pytest` run from such a clone.
- `specs/current/mission.md`: "on macOS" becomes "on macOS or Linux".
- `specs/current/stack.md`:
  - the CJK-font row covers both platforms;
  - the *PDF* prose names both faces;
  - the environment table gains Linux rows;
  - the *Platform layer* paragraph describes `linux.py` and the widened
    surface (font, install hints, input switcher, default shell config);
  - the *doctor* paragraph says the font name comes from the platform layer.
- `notes-sprint-5.md`: the Docker Assumption is updated with D1, the
  input-switching Assumption with D3's best-effort detail, and WSL goes into
  Postponed. The settled Decisions rows are added at merge (feature-spec
  step 9).

## 6. Hand-off

- The full suite runs on macOS, then the full suite runs in the container.
- Hand over to the dev with:
  - the OrbStack install line;
  - the build and run commands;
  - validation's manual checklist.
