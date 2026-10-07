# M3 · Install missing — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [x] `uv run pytest` passes in full.
- [x] Platform tests cover each `install` sequence listed in
      [`plan.md`](plan.md) §1, on both platforms, plus `extend_path` and
      `installable`.
- [x] Installer tests: the runner prints and runs without a shell, reports an
      `OSError` as a failure, and the Enter prompt tolerates `EOFError`.
- [x] Wizard tests listed in [`plan.md`](plan.md) §5 pass, including: no
      rendered text on step 1 (list, error line, dialog) contains `brew`,
      `pacman`, `tlmgr`, `sudo`, a backtick or `http`.
- [x] Dependencies tests: no dialog or refusal text contains a command or a
      backtick.
- [x] `tests/test_no_platform_leaks.py` passes with `tlmgr`, `pacman` and
      `sudo ` added.

## 2. What the greps should find

- [x] `git grep -n -E "install_hint|INSTALL_HINTS|\.install\b|check\.message|check\.url" -- src`
      prints nothing.
- [x] `grep -rn -E "tlmgr|pacman|brew |sudo " src --include=*.py --exclude-dir=platform`
      finds docstrings and comments only.
- [x] `grep -rn "e\.g\. \`" src` finds only `compile.py`'s unrelated docstring
      about `deck.uncategorized`, none in a message.
- [x] `grep -rn "extend_path" src` shows the two definitions, the export,
      `cli.main()`, `installer.py`, and the one call inside `macos.install`.

## 3. Arch (run by the agent, in Docker)

Build: `docker build --platform linux/amd64 --build-arg BARE=1 -t
vimdiomas-linux-bare docker/`.

- [x] **Bare image is bare.** Inside, `which pandoc xelatex kpsewhich nvim
      pdftoppm` finds none; `python`, `git` and `sudo` are there.
- [x] **The install, headless.** As `learner`, follow the README's
      *Installing* up to `pip install .` (cloning `/src` at this branch).
      `vimdiomas doctor` lists pandoc, xelatex, LaTeX packages (`needs a TeX
      distribution`), the input switcher, nvim and pdftoppm as `missing`. Then
      run `installer.run` with the checks step 1 would install, through a stub
      `app` whose `suspend()` is a no-op, with `sudo` given `learner`.
      Afterwards `vimdiomas doctor` shows every `required` and `optional` check
      `ok`. The pacman command printed is the one §3 describes (one command,
      `--needed --noconfirm`, no duplicates).
- [x] **Chinese through step 3's path.** The same with the xeCJK and font
      checks (`texlive-langchinese noto-fonts-cjk`): both then `ok`. With a
      config for Chinese and `tests/fixtures/Food.md` in `tree-Chinese`,
      `vimdiomas compile` exits 0 and writes the PDF.
- [ ] **The TUI flow, by hand in the container** (the dev, or the agent if
      it can drive the TUI): run `~/.local/share/vimdiomas/.venv/bin/vimdiomas`.
      Step 1 shows *Install missing* focused, with no command or URL on screen.
      `y`: pacman asks for `learner`'s password in the terminal, installs,
      Enter returns, the recheck shows every required and optional check `ok`,
      and the button is gone. Ticking Chinese at step 3 offers xeCJK and the
      font with no command shown. `y` installs them, the wizard finishes, and a
      Chinese notebook compiles from the notebook menu.
- [x] **No pacman.** With `pacman` hidden from `PATH` (a test, not the
      container), step 1 shows `pacman isn't installed, so Vimdiomas can't
      install anything.` and runs nothing.
- [x] **The full image still works.** `docker build … -t vimdiomas-linux
      docker/` (no build arg): after the README install, `vimdiomas doctor`
      shows every required check and both Chinese checks `ok`. Its `fcitx5 or
      ibus` and `nvim` are `missing`, as before this milestone (the Dockerfile
      has never installed them), so step 1 shows *Install missing*, for
      exactly those two.

## 4. macOS VM (the dev)

A throwaway VM with nothing but Homebrew, Python and git. One-time setup on the
dev's Mac:

```sh
brew install cirruslabs/cli/tart
tart clone ghcr.io/cirruslabs/macos-tahoe-vanilla:latest vimdiomas-bare
tart run vimdiomas-bare          # user admin, password admin
```

Inside the VM: install Homebrew with its official script, and **don't** add
`brew shellenv` to `~/.zprofile` (this checks §4's `PATH` extension). Then
`/opt/homebrew/bin/brew install python@3.14`. Follow the README's *Installing*
with `/opt/homebrew/bin/python3.14 -m venv .venv` in place of `python3 -m venv
.venv`, cloning this branch.

- [ ] Step 1 lists pandoc, xelatex, LaTeX packages, macism, nvim and pdftoppm
      as `missing`, with no command and no URL, and *Install missing* focused.
- [ ] `y` in the dialog: the terminal shows `brew install pandoc
      laishulu/homebrew/macism neovim poppler`, then `brew install --cask
      basictex`, which asks for the password. No `tlmgr` runs (a stock
      BasicTeX has every package step 1 checks). Enter returns to the wizard.
- [ ] The recheck, **without restarting the wizard or opening a new
      terminal**, shows every required and optional check `ok`, and the button
      is gone.
- [ ] Step 3: tick Chinese. The dialog says Chinese needs xeCJK, with no
      command. `y`: the terminal shows `sudo /Library/TeX/texbin/tlmgr update
      --self`, then `sudo …/tlmgr install xecjk`. Chinese is accepted.
- [ ] Finish the wizard; copy `tests/fixtures/Food.md` into `tree-Chinese`;
      Compile from the notebook menu succeeds and the PDF shows the hanzi.
- [ ] Partial success (a fresh VM, or after `brew uninstall neovim`): turn
      the VM's network off in System Settings › Network, then *Install
      missing*. The recheck says `Still missing: …` naming what failed, and the
      button stays. Turn the network back on and press it again: everything
      `ok`, button gone.
- [ ] Inspect Tree without nvim: after `brew uninstall neovim poppler`, start
      the app, open Inspect Tree. PDF mode's preview says `poppler isn't
      installed, so there's no PDF preview.` and `Enter` in MD mode warns
      `nvim isn't installed, so MD mode can't open files.` Neither names a
      command.
- [ ] `vimdiomas doctor` prints `missing` / `ok` lines only, with no hints.

## 5. The dev's own Mac (regression)

- [ ] With everything installed, move `~/.config/vimdiomas/config.toml` aside
      and start the app: step 1 shows every line `ok` and no *Install missing*.
      Quit, and put the config back.
- [ ] Optional: `brew uninstall neovim`, then the same: *Install missing*
      reinstalls it and the recheck shows it `ok`.
- [ ] Settings › Add a language behaves as before on a machine with
      everything installed.

## 6. Specs

- [ ] `design.md` and `stack.md` updated as §10 lists, with no remaining claim
      that only language dependencies are installed, or that `doctor` or any
      screen shows a command.
- [ ] Code and these three files agree.
