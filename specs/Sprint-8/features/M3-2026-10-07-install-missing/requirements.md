# M3 · Install missing — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M3 · Install
missing*:

> The backlog: "The first screen of the wizard checks for missing dependencies.
> If one is missing, a third button should be added: "install missing". No
> instructions should be shown on how to do it. The app should just run the
> commands".
>
> **Deliverable.**
>
> - Step 1 shows a third button, **Install missing**, whenever a required or
>   optional dependency is missing. Language dependencies (xeCJK, the CJK font)
>   are left to step 3's existing offer.
> - Pressing it runs the platform's commands for everything missing, with the
>   TUI suspended so `sudo` (pacman) or the BasicTeX `.pkg` installer can ask
>   for a password, then rechecks. (macOS: `brew install` for pandoc, poppler,
>   neovim and macism; BasicTeX only when there is no `xelatex`; then `sudo
>   tlmgr update --self` and `sudo tlmgr install` for what M2's check reports
>   missing. Arch: one `sudo pacman -S --needed …`.)
> - The failure lines no longer show commands or install hints. They say what's
>   missing and nothing else.
> - Fix: step 3's xeCJK offer fails on a fresh BasicTeX; the xeCJK install
>   becomes `sudo tlmgr update --self` then `sudo tlmgr install xecjk`, through
>   the one code path both share.
> - The recheck finds a TeX installed during this session even though the
>   wizard's `PATH` predates it (`xelatex`, `kpsewhich` and `tlmgr`).
> - `design.md`'s *A language's missing dependencies* and the dependency
>   conventions are updated.
> - A way to verify on a bare Arch machine.
>
> **Done when.** On a bare Arch container with only `python` and `git`,
> following the README's *Installing* and pressing *Install missing* leaves
> every required and optional check `ok`, and a Chinese notebook compiles once
> step 3 has installed its dependencies. On macOS, a missing dependency is
> installed by the button and passes the recheck without restarting the
> wizard; on a Mac with no TeX, *Install missing* followed by ticking Chinese at
> step 3 ends with a Chinese notebook that compiles, with no new terminal
> opened. No install command or hint appears anywhere on step 1. The full test
> suite passes.

The backlog ([`../../guidelines/backlog.md`](../../guidelines/backlog.md),
*Fix wizard*): "Take for granted Brew and Pacman are installed." / "The first
screen of the wizard checks for missing dependencies. If one is missing, a
third button should be added: "install missing"." / "No instructions should be
shown on how to do it. The app should just run the commands".

## Decisions

Settled with the dev in the spec conversation, 2026-10-07.

| Decision | Rationale |
| --- | --- |
| **Install missing asks for confirmation first** (a `ConfirmDialog`, `y`/`n`) | Dev's choice. Same as step 3's offer; it runs `sudo`. |
| **Commands run in sequence and a failure doesn't stop the rest.** The recheck decides what is still missing | Dev's choice. Same rule as step 3 today ("the recheck decides, not the exit code"). The one exception: the `tlmgr` commands are skipped when no `tlmgr` can be found, since they could only fail. |
| **No `brew` / `pacman`: a one-line failure, nothing runs** | Dev's choice, over letting the command fail in the terminal. `Homebrew isn't installed, so Vimdiomas can't install anything.` (`pacman` on Arch). |
| **After a partial success the button stays as it is.** It is shown whenever something it can install is missing, and pressing it again retries only what's left. It hides when nothing is left | Dev's choice. |
| **No commands anywhere in the app**: step 1, step 3, Settings › Add a language, `vimdiomas doctor`, and Inspect Tree's nvim and poppler messages | Dev's choice for each surface (step 3 / Settings, `doctor`, Inspect Tree). One rule: say what's missing, never how to get it. |
| **`vimdiomas doctor` prints `missing`, or `missing: <detail>`** | Dev's choice ("drop hints there too"). Exit status unchanged. |
| **On macOS the app adds the known install directories to its own `PATH` at startup**, and again after each install command | Dev's choice, over doing it only around an install. The dirs are `/opt/homebrew/bin`, `/usr/local/bin` and `/Library/TeX/texbin`, each appended only if it exists and isn't already there. In-process only: no shell file is touched. It covers a TeX installed mid-session (`xelatex`, `kpsewhich`, `tlmgr`), and a shell that never ran `brew shellenv`. Arch installs into `/usr/bin`, so nothing is added there. |
| **The bare Arch image is a build argument**, `--build-arg BARE=1`, on the existing Dockerfile | Dev's choice, over a second Dockerfile or making the existing one bare. |
| **The macOS done-when is checked in a throwaway macOS VM** (Tart) with only Homebrew, Python and git | Dev's choice for the no-TeX case. It also covers the "a missing dependency is installed and passes the recheck" case: a spare account on the dev's Mac can't run `brew install`, because Homebrew's prefix belongs to the dev's user (found while writing this spec). The dev's own Mac gets a regression check only (§9). |

Proposed by the agent in this spec, for the dev to confirm in review:

| Decision | Rationale |
| --- | --- |
| **The URL arrow on step 1 goes too** (`missing <-- https://github.com/jgm/pandoc` becomes `missing`) | The roadmap: failure lines "say what's missing and nothing else". A link to a project's page is a pointer to how to get it. `Check.url` is removed. |
| **The `Check.message` sentences go too** ("nvim not found: Inspect Tree's MD mode won't be able to open files (e.g. …)") | They exist only for `vimdiomas doctor` and carry the hints. With `doctor` printing `missing`, nothing reads them. `Check.message` is removed. |
| **pacman runs with `--noconfirm`** | The dev already said yes in the app. Without it pacman asks again, and asks which members of the `fcitx5-im` group to install. |
| **`sudo` runs `tlmgr` by its absolute path** | `sudo` may reset `PATH`, and a freshly installed BasicTeX is only on the app's extended `PATH` (§4). |
| **The bare image sets `learner`'s password to `learner`** and puts it in `wheel` with `sudo` | So the run asks for a password through the suspended TUI, as on a real machine. |

## 1. Step 1: the button

`DependenciesScreen` gains a third button, **Install missing**
(`#install-button`), placed first: *Install missing*, *Recheck*, *Next*.

- **Shown** when at least one check is not ok, is `required` or optional (no
  `needed_for`), and the platform can install it (§3,
  `platform.installable(key)`). Hidden (`display = False`) otherwise. Tab skips
  it while hidden.
- **Focus** starts on it when it is shown at mount; otherwise focus starts where
  it does today.
- Visibility is recomputed whenever the checks are (mount, *Recheck*, after an
  install). If it hides while focused, focus moves to *Next*.
- The footer hint is unchanged.

Pressing it:

1. If the package manager is missing (`platform.package_manager_available()` is
   false), the error line under the list says `Homebrew isn't installed, so
   Vimdiomas can't install anything.` (`pacman` on Arch) and nothing else
   happens.
2. Otherwise a `ConfirmDialog`: `<names> <is|are> missing. Install <it|them>
   now? Your password may be asked for in the terminal.` `<names>` are the
   checks being installed, in list order, joined as step 3 joins them
   (`pandoc, xelatex and nvim`). No commands.
3. `n`/`esc`: nothing happens.
4. `y`: the TUI suspends, the install runs (§2), the TUI resumes, and the
   existing recheck runs (with its spinner). After it:
   - nothing installable left missing: the error line is hidden, and the button
     hides;
   - something still missing: the error line says `Still missing: <names>.`
     (the installable checks still failing). The button stays.

*Next* keeps blocking on a missing required check. Its error line becomes `A
required dependency is still missing.` (drops "fix it and recheck").

## 2. Running the install

A new module, `vimdiomas/installer.py`, is the one code path step 1, step 3 and
Settings › Add a language use (`install.py` stays the wizard's linking step).

- `installer.join_names(names)` joins names the way step 3 does (`a, b and c`),
  for step 1's dialog and `Still missing:` line and for step 3.
- `installer.run(app, checks)`: with `app.suspend()`, prints a header
  (`Installing pandoc, xelatex and nvim.`), hands the checks' keys to
  `platform.install(keys, run, missing_latex)` (§3), calls
  `platform.extend_path()` once more, then waits for Enter (`Press Enter to
  return to Vimdiomas.`, `EOFError` tolerated). It never raises: an exception from the platform's `install` is printed in the
  terminal (`Could not finish: <reason>`) and the run still resumes the TUI.
- `run_command(argv)`, the runner it passes: prints `$ <argv joined with shlex>`, runs
  it with `subprocess.run(argv, check=False)` (no shell), and returns whether it
  exited 0. An `OSError` prints `Could not run it: <reason>` and returns false.
  The commands are visible in the terminal while they run. That is the
  commands' own output, not instructions on the TUI.
- `missing_latex`, the callback it passes, is `doctor`'s package probe (one
  `kpsewhich` call): the names missing, or `None` without `kpsewhich`. The
  platform calls it after installing a TeX, so it sees what the new TeX lacks.
- Nothing from the run is shown in the TUI. The recheck alone decides what is
  reported.

## 3. The platform layer

Each platform module replaces `INSTALL_HINTS`, `install_hint` and
`latex_install_hint` with:

- **The package tables.** Keys are the dependency keys of §5.
  - macOS: `BREW_FORMULAS` = `pandoc` → `pandoc`, `input-switcher` →
    `laishulu/homebrew/macism`, `nvim` → `neovim`, `pdftoppm` → `poppler`;
    `BASICTEX_CASK = "basictex"`; `LATEX_PACKAGES` (M2's table, unchanged) and
    `xecjk` → `xecjk` for `tlmgr`. No entry for `cjk-font` (it ships with the
    OS).
  - Arch: `PACMAN_PACKAGES` = `pandoc` → `pandoc-cli`, `xelatex` →
    `texlive-xetex`, `xecjk` → `texlive-langchinese`, `cjk-font` →
    `noto-fonts-cjk`, `input-switcher` → `fcitx5-im fcitx5-chinese-addons`,
    `nvim` → `neovim`, `pdftoppm` → `poppler`; `LATEX_PACKAGES` (M2's table,
    unchanged).
- **`PACKAGE_MANAGER`**: `"Homebrew"` / `"pacman"`, for the one-line failure.
- **`package_manager_available()`**: `shutil.which("brew")` /
  `shutil.which("pacman")`. It doesn't call `extend_path()` itself: `cli.main()`
  did at startup (§4) and `installer.run` does after each install.
- **`installable(key) -> bool`**: whether `install` can do anything for it.
  macOS: the `BREW_FORMULAS` keys, `xelatex`, `latex-packages`, `xecjk`. Arch:
  the `PACMAN_PACKAGES` keys and `latex-packages`.
- **`extend_path()`**: macOS appends to `os.environ["PATH"]` each of
  `/opt/homebrew/bin`, `/usr/local/bin`, `/Library/TeX/texbin` that exists and
  isn't already an entry. Arch: a no-op.
- **`install(keys, run, missing_latex)`**: runs the commands for `keys`,
  through `run`, in this order. Keys it can't install are ignored.

**macOS**, each step only if it has something to do:

1. `brew install <formulas>` — one command for every key in `BREW_FORMULAS`.
2. `brew install --cask basictex` if `xelatex` is in `keys`; then
   `extend_path()`.
3. The `tlmgr` packages: if `xelatex` or `latex-packages` is in `keys`, the
   `tlmgr` names of whatever `missing_latex()` reports (none when it returns
   `None`); plus `xecjk` if it is in `keys`. If there are any and
   `shutil.which("tlmgr")` finds one: `sudo <tlmgr> update --self`, then `sudo
   <tlmgr> install <names>`, both with `tlmgr`'s absolute path. With no `tlmgr`
   both are skipped.

On a stock BasicTeX, step 3 finds nothing missing at step 1 (verified, see
notes, Assumptions), so it runs only when Chinese is ticked at step 3, for
`xecjk`. That is the roadmap's fix: the xeCJK install now always runs `update
--self` first, through this same function.

**Arch**: one command, `sudo pacman -S --needed --noconfirm <packages>`, for
the `PACMAN_PACKAGES` of every key, plus, if `xelatex` or `latex-packages` is
in `keys`, the `LATEX_PACKAGES` targets of what `missing_latex()` reports, or
of every row when it returns `None` (a bare machine has no `kpsewhich` yet).
Deduplicated, first-seen order. `--needed` skips anything already there.

`tlmgr`, `pacman`, `brew` and `sudo` stay inside the platform layer.
`tests/test_no_platform_leaks.py`'s list gains `tlmgr`, `pacman` and `sudo `.

## 4. `PATH` at startup

`cli.main()` calls `platform.extend_path()` before it dispatches, so the TUI,
`compile` and `doctor` all see the same tools. It runs after `supported_os`'s
gate, which is unchanged.

## 5. `doctor`

- `Check` gains `key: str`, the dependency key the platform layer understands:
  `pandoc`, `xelatex`, `latex-packages`, `xecjk`, `cjk-font`,
  `input-switcher`, `nvim`, `pdftoppm`.
- `Check.install`, `Check.message` and `Check.url` are removed, along with
  `_example()`. `name`, `required`, `ok`, `needed_for`, `detail` stay. `key` is
  the second positional field: `Check(name, key, required=…, ok=…)`.
- `input_switcher()` keeps returning `(name, available, url)` and the platform
  layer keeps `CJK_FONT_URL`: they are no longer read by `doctor` (nothing shows
  a link), and are left in place rather than widening this milestone to the
  platform tests that pin them.
- The package probe (`_missing_latex_packages`) becomes public as
  `missing_latex_packages()`, for `installer.py`. `LATEX_PACKAGES`, `NO_TEX`
  and the `detail` rules stay as M2 left them.
- `vimdiomas doctor` prints `[<label>] <name>: ok`, `[<label>] <name>:
  missing`, or `[<label>] <name>: missing: <detail>`. Which checks set the exit
  status is unchanged (`missing_for`).

## 6. Step 1's list

`_checks_text` drops the URL arrow: a failing line is `missing`, followed by its
`detail` lines as M2 left them. Nothing else changes in the layout.

## 7. Step 3 and Settings › Add a language

`tui/screens/dependencies.py` keeps `ensure_dependencies` and its flow, with
three changes:

- **Offerable** (`dependencies._installable`, which replaces `_offerable`):
  every missing check is a language check (`needed_for`) and
  `platform.installable(check.key)`. The package manager is checked next, so a
  missing one gets its own line instead of the plain refusal.
- **The confirmation** keeps its head and drops the command: `Chinese needs
  xeCJK, which is missing. Install it now? Your password may be asked for in
  the terminal.` (plural: `… need xeCJK and Noto Serif CJK SC, which are
  missing. Install them now? …`).
- **The refusal** names what is missing only: `Chinese needs xeCJK, which is
  missing.`, `LaTeX packages missing: caption, xcolor.`, `pandoc is missing.`.
  No command, no message. When the reason it wasn't offered is a missing
  package manager, one more line follows: `Homebrew isn't installed, so
  Vimdiomas can't install it.` (`them` for several).
- **The install** goes through `installer.run` (§2) instead of its own
  `_install`. The "Could not run …" lines are no longer added to the refusal,
  since they would show commands. They are printed in the terminal during the
  run.

The module docstring's "Only the dependencies a language itself needs … are
ever offered" is rewritten (step 1 now installs the others).

## 8. Inspect Tree

- `MSG_NO_POPPLER` becomes `poppler isn't installed, so there's no PDF
  preview.`
- `MSG_NO_NVIM` becomes `nvim isn't installed, so MD mode can't open files.`
- `inspect.py` stops importing from `vimdiomas.platform` for these.

## 9. Verification support

- **`docker/Dockerfile`** takes `ARG BARE=0`. With `BARE=1` the `pacman` line
  installs only `python git sudo`. Otherwise it installs the current list plus
  `sudo`. In both cases, `learner` gets the password `learner`, is in `wheel`,
  and `/etc/sudoers.d/wheel` allows `%wheel ALL=(ALL:ALL) ALL`. The comment at
  the top says what each variant is for.
- **`docker/README.md`** gains a *Bare image* paragraph: the build command with
  `--build-arg BARE=1 -t vimdiomas-linux-bare`, that the wizard's *Install
  missing* is what installs everything, and that the password is `learner`.
- **The macOS VM** procedure is in [`validation.md`](validation.md) §4. It is
  not added to the repo's docs: it is a one-off check of this milestone, and
  the README stays out of this sprint.

## 10. Docs

- **`design.md`**:
  - *A language's missing dependencies* is rewritten: the confirmation and
    refusal no longer show commands, and the bullet "Only a language's own
    dependencies are ever offered for installation" is removed.
  - A new subsection, *Installing missing dependencies*, states the
    cross-cutting rule: the app never shows an install command or hint, on any
    surface. Step 1's *Install missing* (§1) and the shared run (§2, the
    suspended terminal, the recheck decides, the missing-manager line) are
    stated there once.
  - Inspect Tree's two nvim/poppler passages (*Failures are reported, never
    fatal*, and the preview list) are reworded to §8's messages.
- **`stack.md`**: the platform layer's surface (§3 replaces `install_hint` /
  `latex_install_hint`; `extend_path`), `installer.py`, the `Check` fields (§5:
  `key` in, `install`/`message`/`url` out), and the leak test's new words.
  Sprint 6 M7's "suspends the TUI and runs the platform's command" sentence is
  updated to point at `installer.py`.
- **Notes**: the Assumptions rows on the fresh TeX's `PATH`, the xeCJK offer on
  BasicTeX, the bare Arch image and macOS hand-testing are settled when this
  milestone merges.

- **Tests.** `tests/conftest.py` gets an autouse fixture that stubs
  `cli.extend_path`, so a test that calls `main()` cannot change the real
  `PATH` for the tests after it.

## 11. Out of scope

- Installing Homebrew or pacman (backlog: taken for granted).
- `pacman -Syu`. A stale package database is the user's to sync. The
  recheck reports what didn't install.
- Full MacTeX. An existing TeX of any kind is kept.
- The README, including its *Dependencies* line (Postponed).
- A `doctor --install` CLI command.
- A spare-account test on the dev's Mac (Homebrew's prefix is single-user).
- Arch derivatives beyond `archlinux:latest`.
