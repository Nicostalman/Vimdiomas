# M7 · Linux support — requirements

Sprint 5 · M7. Branch `2026-09-29-m7-linux-support`.

## Anchor: the roadmap

From [`../../roadmap-sprint-5.md`](../../roadmap-sprint-5.md), *M7 · Linux
support*, in turn from the backlog's *Add linux support*: "Add whatever is
necessary for linux support."

**Deliverable** (roadmap, abridged): a Linux module in the platform layer; every
OS-specific call that leaked out of the layer moved in; a per-platform CJK font;
`doctor` reports Linux dependencies with Linux install commands; the wizard
runs on Linux end to end, including linking and the `PATH` line; the README
documents a Linux install; a Docker image for verification is checked into the
repo; macOS does not regress.

**Done when** (roadmap, verbatim): The app installs and runs inside the Docker
image from the README's Linux instructions; the wizard completes there, writes
a config, links `idiomas` and adds the `PATH` line to the right shell config;
`idiomas doctor` lists Linux install commands and no `brew`; a notebook
compiles to a correct PDF with a Linux CJK font, grammar files included; the
full test suite passes inside the container; nothing outside
`idiomas.platform` names a macOS-only tool or path; the dev confirms macOS is
unchanged by hand; and the full test suite passes on macOS.

## Decisions from the spec conversation (2026-09-29)

| # | Decision | Source |
| --- | --- | --- |
| D1 | **The verification container runs under OrbStack.** No container runtime was installed on the dev's Mac when this milestone opened (no Docker, OrbStack, Podman or Colima). This means the sprint's assumption that Docker could run the toolchain didn't hold yet. The dev installs OrbStack (`brew install orbstack`) before the hand-test. The Dockerfile is plain Docker and doesn't depend on OrbStack. | Dev |
| D2 | **The image is Arch Linux** (`archlinux:latest`). Arch's official image is amd64-only, so on the dev's Apple Silicon Mac it runs under OrbStack's Rosetta emulation (`--platform linux/amd64`). It's slower but functional. | Dev |
| D3 | **Linux input switching targets both fcitx5 and ibus.** Whichever one is running is detected at call time and cached for the process. It's best-effort and unverifiable in a container, so a missing framework makes switching and listing a silent no-op, the same as macOS without `macism`. | Dev |
| D4 | **Linux's CJK face is Noto Serif CJK SC.** It's the Ming/serif counterpart to M3's Songti SC. macOS keeps Songti SC exactly as approved in M3. PDFs compiled on the two platforms are close but not identical, and that is accepted. | Dev |
| D5 | **`doctor` and the README pick install commands by distro family.** The family comes from `/etc/os-release`'s `ID`/`ID_LIKE` and is one of `arch`, `debian` (Debian/Ubuntu/Mint…) or `fedora` (Fedora/RHEL…). An unrecognised family gets no command: the message's own wording ("pandoc not found: install it") stands alone. Only Arch is verified in the container; the apt and dnf lines are correct by reading only. | Dev |
| D6 | **The fallback shell config is per-platform.** When `$SHELL` is none of zsh, bash or fish, the fallback is `~/.zshrc` on macOS (unchanged) and `~/.bashrc` on Linux. The zsh, bash and fish mapping itself is unchanged. | Dev |
| D7 | **WSL is out of scope.** Nothing WSL-specific (such as opening files through Windows) is built or tested, though most of the app will likely work there as plain Linux. It's recorded under Postponed alongside Windows support. | Dev |

## Scope

### In

1. **`idiomas/platform/linux.py`**, dispatched from `idiomas.platform` when
   `platform.system() == "Linux"`, with the same surface as `macos.py`:
   - `open_file(path)` → `xdg-open <path>`. It never raises: a missing
     `xdg-open` (as in a bare container) is a no-op.
   - `switch_input_source(source_id)` → `fcitx5-remote -s <id>` when fcitx5
     is running, `ibus engine <id>` when ibus is. Otherwise it's a no-op, and
     it never raises.
   - `list_input_sources()` returns the user's enabled sources, in order:
     - **fcitx5**: the input-method `Name`s in `~/.config/fcitx5/profile`, an
       INI file with `[Groups/N/Items/M]` sections. They're read with
       `configparser`, so there's no D-Bus dependency.
     - **ibus**: `gsettings get org.freedesktop.ibus.general preload-engines`,
       parsed as a GVariant string list.
     - Otherwise `[]`. It never raises, the same posture as macOS.
     - Display names come from a small table covering the usual pinyin
       engines and keyboard layouts (`pinyin`, `keyboard-us`, `libpinyin`,
       `rime`, `xkb:us::eng`…). Anything else falls back to the raw ID,
       mirroring `macos.DISPLAY_NAMES`.
   - `cjk_font_installed()` → `fc-list` reports the family
     `Noto Serif CJK SC`. A missing `fc-list` means not installed.
   - `user_bin_dir()` → `~/.local/bin` (the XDG convention).
2. **The CJK font moves into the platform layer.** Today
   `compile.CJK_FONT_NAME`/`CJK_FONT_PATH` hardcode Songti SC's macOS path
   outside the layer. After this milestone:
   - each platform module states its own `CJK_FONT_NAME`, and the layer
     re-exports it;
   - `cjk_font_installed()` takes no argument, because each platform knows
     how to check for its own face (a file path on macOS, fontconfig on
     Linux);
   - `compile.py` reads the name from `idiomas.platform` and still passes it
     as `-V cjkfont=…`. `templates/xecjk.tex` already takes
     `\setCJKmainfont{$cjkfont$}` (M3), so the template needs no change.
     "The template stops being a fixed file" was already achieved by M3's
     variable.
   - M2's staleness stamp already hashes the font name, so a tree compiled
     on one OS and opened on the other recompiles. That is correct, not a
     cost.
3. **Install hints move into the platform layer.** Every `brew …` line in
   `doctor.py`, and `inspect.py`'s `MSG_NO_POPPLER`, reads its command from
   `idiomas.platform.install_hint(dependency)`:
   - It returns a one-line **shell command**, or `None` when the platform has
     none to offer. `doctor` keeps each message's own wording and appends
     `` (e.g. `<command>`)`` only when there is one. *(Settled during
     implementation: the macOS messages have different shapes — xelatex
     names no command, xeCJK's message is the bare command, the font's
     quotes a path — so a command-or-`None` contract is what keeps them
     byte-identical.)*
   - macOS returns today's exact commands (`brew install pandoc`,
     `sudo tlmgr install xecjk`, …), and `None` for xelatex and the font,
     which today name no command. `doctor.run()`'s macOS output is
     unchanged.
   - Linux returns a line from the D5 family table, and `None` for an
     unrecognised family.
   - Dependency keys: `pandoc`, `xelatex`, `xecjk`, `cjk-font`,
     `input-switcher`, `nvim`, `pdftoppm`.
   - The font message still quotes the font's file on macOS. The layer
     re-exports `CJK_FONT_PATH` for that (`None` on Linux, where the message
     names only the family) and `CJK_FONT_URL` (`""` on macOS).
4. **The input switcher is named per platform in `doctor`.** Today's optional
   `macism` check becomes the platform's own switcher check, via
   `idiomas.platform.input_switcher()`, which returns a
   `(name, available, url)` triple. *(The url was added during
   implementation: the `macism` repo link is itself a macOS-only string, so
   it moves into the layer with the name.)*
   - macOS: `macism`, the same check, message and url as today;
   - Linux: `fcitx5 or ibus`, available when `fcitx5-remote` or `ibus` is on
     `PATH`, with fcitx5's repo as the url.
5. **Distro-family detection**, `linux.distro_family()`, reads
   `platform.freedesktop_os_release()` and never raises. A missing or
   unreadable os-release gives `None`, so `install_hint` offers no command.
6. **`install.py` loses its macOS-only assumptions:**
   - `shell_config_path()` falls back to the platform's default
     (`idiomas.platform.DEFAULT_SHELL_CONFIG`: `.zshrc` / `.bashrc`), per D6;
   - `LinkState.UNSUPPORTED`'s docstring, and the wizard's text for it, now
     mean "neither macOS nor Linux";
   - the wizard's docstring saying the CJK font "ships with macOS" is made
     platform-neutral. On Linux the font check carries a URL
     (`https://github.com/notofonts/noto-cjk`); macOS still carries none.
7. **The inert-no-op fallback stays for every other platform**, such as
   Windows. It gains the new names (`CJK_FONT_NAME`, `CJK_FONT_PATH`,
   `CJK_FONT_URL`, `install_hint`, `input_switcher`, `DEFAULT_SHELL_CONFIG`) so nothing imports a name that
   isn't there.
8. **A sweep**: nothing outside `idiomas/platform/` names a macOS-only tool
   or path in executable code (`brew`, `macism`, `open`, `defaults`,
   `/System/…`, `/Library/…`, `.zshrc` as a hardcoded default). Comments and
   docstrings that claim "macOS only" are corrected where the claim is no
   longer true. A test enforces the code half so it can't regress (see
   validation).
9. **The test suite runs on both platforms.** Tests that assert macOS
   specifics (dispatch to `macos`, `.zshrc` fallback, Songti SC, `brew`
   strings) become platform-aware. `linux.py` gets unit tests that run on
   macOS too, by importing the module directly and monkeypatching
   `subprocess`/file reads, the way `macos.py` is tested today.
10. **A verification image**, `docker/Dockerfile`, checked in:
    - Arch base with pandoc, `texlive-xetex` + `texlive-langchinese` (for
      xeCJK), `noto-fonts-cjk`, `poppler`, `git`, and Python ≥ 3.14 (the
      system `python` if Arch ships 3.14, otherwise via `uv`);
    - a non-root user with bash as its login shell, so the wizard's linking
      and `PATH` steps run against a realistic `$HOME`;
    - it does **not** pre-install Idiomas, because the done-when is that the
      README's Linux instructions work inside it;
    - it's run with the repo bind-mounted for the test-suite pass. The
      README's contributor section documents both uses: interactive install
      and `pytest`.
11. **The README gains a Linux install section** next to the macOS one:
    - a dependency table with Arch, Debian/Ubuntu and Fedora commands, the
      same families as D5;
    - the rest of the install (clone, venv, first run, wizard) is shared
      text where it's identical.
12. **The README's non-editable install ships the TUI stylesheet.** Found in
    the container pass: `pip install .` (the README's step 2) left out
    `idiomas/tui/app.tcss`, because `pyproject.toml`'s package-data listed
    only `templates/*.tex`. The app then crashed on launch with
    `StylesheetError: unable to read CSS file`. The bug is platform-neutral
    and predates M7: the dev's own `idiomas` runs from an editable dev
    install, which reads the file from the checkout, so it never showed.
    M7's done-when requires the README's install to work, so the fix is
    in scope: package-data gains `tui/*.tcss`.
13. **More findings from the container pass**, each fixed here:
    - **Input-source advisories named macOS's System Settings on Linux.**
      Where sources are enabled is now the layer's
      `INPUT_SOURCES_SETTINGS` ("fcitx5's or ibus' own settings" on
      Linux; macOS's text is unchanged). The translation-side preselection
      stops matching `com.apple.keylayout.` itself and asks the layer's
      `is_keyboard_layout(id)` (`keyboard-*`/`xkb:*` on Linux). The leak
      test now also forbids `System Settings` and `com.apple.`.
    - **The wizard's dependency list misaligned** on names longer than 10
      characters ("Noto Serif CJK SC", "fcitx5 or ibus"). The name column
      is now as wide as the longest name, with 10 as the minimum, so
      macOS's layout is unchanged.
    - **`tests/test_main.py` read the machine's real config.** It patched
      `__main__.CONFIG_PATH` but not the `idiomas.config.CONFIG_PATH` that
      `load_config()` reads, and passed on the dev's Mac only because the
      real user name there matches the tests' "Nico". Both are patched
      now. This is a test bug that predates M7.
    - **One wizard test assumed macOS's check names** (it expected `macism`
      in the pending spinner list). It now fakes the checks from the start.
    - **Arch's `texlive-xetex` isn't enough to compile** (see plan
      group 2's table note). The xelatex install line, the README and the
      image all gain the recommended LaTeX and font collections.
14. **Project-level specs follow:**
    - `mission.md`'s "working in a terminal on macOS" becomes "macOS or
      Linux";
    - `stack.md`'s CJK-font row, its *PDF* prose, its environment table and
      its *Platform layer* paragraph describe both platforms and the new
      layer surface.
    - `design.md` needs nothing: no user-facing convention changes.

### Out (deferred or dropped)

- **WSL** (D7): Postponed, alongside Windows.
- **Windows support**: already Postponed at sprint start and unchanged.
- **Verifying Linux input switching.** The container has no desktop session
  and no IME daemon, so the fcitx5/ibus paths are unit-tested only (see the
  notes' Assumption).
- **Packaging for any distro** (AUR, `.deb`, Flatpak). The install stays the
  README's `git clone` + venv, the same as macOS, where brew packaging is
  also still deferred.
- **Keeping PDFs pixel-identical across platforms** (D4).
- **Non-amd64 Arch images.** The official image is the target; running it
  under emulation on Apple Silicon is accepted (D2).

## Context

- `idiomas.platform` was built in Sprint 4 M4 for exactly this milestone. Its
  docstring predicts that Linux "means adding a module here". The surface
  grows by three names (`CJK_FONT_NAME`, `install_hint`, `input_switcher`)
  plus `DEFAULT_SHELL_CONFIG`. That's because the original four were only
  what macOS needed at the time, while `doctor`'s hardcoded `brew` lines and
  font path are also OS-specific.
- `compile.CJK_FONT_NAME` was made the font's single source of truth in M3.
  Moving it into the platform layer keeps one source per platform rather
  than splitting it. `compile.py` keeps re-exporting nothing:
  `doctor.py`, the one reader outside `compile.py`, imports from the layer.
- M4's kitty-graphics preview is unaffected. Detection is by
  `TERM_PROGRAM`/`TERM` and knows nothing about the OS. Inside
  `docker run -it`, `TERM_PROGRAM` isn't forwarded by default, so
  `-e TERM_PROGRAM` is part of the documented run line if the preview
  should work there.
- The sprint notes' Assumption *"Docker on the dev's machine can run the
  full toolchain"* is where D1 lands: no runtime existed at all.
