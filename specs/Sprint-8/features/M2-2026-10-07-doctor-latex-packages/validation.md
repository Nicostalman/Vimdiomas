# M2 · `doctor` checks the LaTeX packages — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [x] `uv run pytest` passes in full.
- [x] Doctor tests cover: a complete TeX (`ok`, empty `detail`, empty
      `install`); one missing package; several missing in table order; two
      missing packages that share an Arch target (one package in the command);
      no `kpsewhich` (`needs a TeX distribution`, empty `install`); the macOS
      and Arch command shapes.
- [x] `missing_for(checks, ["German"])` and `missing_for(checks, [])` include
      `LaTeX packages` when it fails.
- [x] The consistency test passes: every unconditional `\usepackage` in
      `xecjk.tex` has a row, and the doctor table, the macOS table and the Arch
      table list the same names.
- [x] Wizard tests: a failing check with a detail shows `missing` and the
      detail beneath, wrapped inside the panel; *Next* is blocked by it; an ok
      check has no detail line.
- [x] `git grep -n -E "tlmgr|pacman|brew" -- src/vimdiomas/doctor.py` prints
      nothing, and `tests/test_no_platform_leaks.py` passes.

## 2. What the greps should find

- [x] `git grep -n "texlive-latexrecommended" -- src` appears only in
      `platform/linux.py`'s `LATEX_PACKAGES` table (and comments), no longer in
      `INSTALL_HINTS["xelatex"]`.
- [x] `git grep -n "latex_install_hint" -- src` shows the two definitions, the
      `platform/__init__.py` exports and `doctor.py`'s use.

## 3. Bare Arch: the check fails, names the packages, and its command fixes it

Run from the repo root, with Docker (OrbStack). A throwaway container, not a
file: `texlive-xetex` alone, plus the other required tools.

- [x] **The check fails and names the packages**:

      docker run --rm --platform linux/amd64 -v "$PWD":/src:ro archlinux:latest bash -c '
        sed -i "/^\[options\]/a DisableSandbox" /etc/pacman.conf
        pacman -Syu --noconfirm --needed python git pandoc-cli texlive-xetex >/dev/null
        cp -r /src /tmp/srccopy && python -m venv /tmp/v && /tmp/v/bin/pip install -q /tmp/srccopy
        /tmp/v/bin/vimdiomas doctor; echo "exit $?"'

      The source is copied first because setuptools can't write its build
      files into the read-only mount.

      Passing: `[required] pandoc: ok`, `[required] xelatex: ok`, then
      `[required] LaTeX packages: LaTeX packages missing: fontspec, caption,
      xcolor, lmodern, lmodern fonts (e.g. `sudo pacman -S
      texlive-latexrecommended texlive-fontsrecommended`)` and `exit 1`.
      `geometry`, `longtable` and `array` are not named.
- [x] **Its command makes it pass.** In the same container, run exactly the
      command printed, then `vimdiomas doctor` again: `LaTeX packages: ok` and
      the required checks all `ok`.
- [x] **A partial TeX names only what is missing**: with `texlive-xetex` and
      `texlive-latexrecommended` installed but not `texlive-fontsrecommended`,
      the line names `lmodern, lmodern fonts` and the command is
      `sudo pacman -S texlive-fontsrecommended`.
- [x] **It confirms the list by compiling** (§6). With the bare container:
      a compile of `tests/fixtures/german/Essen.md` fails; after the printed
      command it succeeds (`compile_file` from `vimdiomas.compile` with
      `ALPHABETICAL`, from a `python -c` against `/src/tests/fixtures`, output
      to a temporary directory); and after also installing `texlive-langchinese
      noto-fonts-cjk fontconfig`, `tests/fixtures/Food.md` compiles with
      `CHARACTER_PHONETIC`. If a compile asks for a file the table does not
      cover, the spec and the table are corrected before merging.
- [x] **No TeX**: in a container without `texlive-xetex`, `vimdiomas doctor`
      shows `xelatex` failing and `LaTeX packages` failing with `needs a TeX
      distribution` (message: `LaTeX packages can't be checked …`), no command.
- [x] **The existing verification image stays green**: the `docker/Dockerfile`
      image prints `ok` for every required and Chinese line of `vimdiomas
      doctor` (`LaTeX packages` among them); its optional `fcitx5 or ibus` and
      `nvim` were never installed there.

## 4. Hand-checks on the dev's Mac

- [ ] `uv run vimdiomas doctor` prints `[required] LaTeX packages: ok`, and
      every line is `ok` as before.
- [ ] `uv run vimdiomas` → the wizard (or `vimdiomas wizard`, backed out of
      with `q` before the last step): step 1 lists `LaTeX packages` with
      `ok`, the columns aligned, and *Next* works.
- [ ] **A missing package, faked.** Put a `kpsewhich` wrapper first on `PATH`
      that hides `caption.sty`, and run `vimdiomas doctor` and the wizard:

      mkdir -p /tmp/fakebin && cat > /tmp/fakebin/kpsewhich <<'EOF'
      #!/bin/sh
      /Library/TeX/texbin/kpsewhich $(printf '%s\n' "$@" | grep -v '^caption.sty$')
      EOF
      chmod +x /tmp/fakebin/kpsewhich
      PATH=/tmp/fakebin:$PATH uv run vimdiomas doctor

      Passing: `LaTeX packages missing: caption (e.g. `sudo tlmgr install
      caption`)`, exit 1. In the wizard, step 1 shows `missing` with `caption`
      beneath it, *Next* is blocked with the usual message, and removing the
      wrapper from `PATH` and pressing *Recheck* clears it without restarting.
- [ ] Several hidden at once (`caption.sty` and `lmodern.sty`) gives
      `sudo tlmgr install caption lm`, `lm` once.
- [ ] A Chinese notebook and a German one still compile from the app, as
      before.
