# M1 · Supported platforms — validation

The acceptance bar. Section numbers (§) refer to
[`requirements.md`](requirements.md).

## 1. Automated

- [ ] `uv run pytest` passes in full.
- [ ] `tests/test_supported_os.py` covers macOS, `arch`, an `ID_LIKE=arch`
      derivative, Debian, Ubuntu, Fedora, an unreadable `os-release`, Windows
      and FreeBSD, and the message with and without `PRETTY_NAME`.
- [ ] On a faked unsupported system, `vimdiomas`, `compile`, `doctor` and
      `wizard` each print the message to stderr, exit 1, and leave a temporary
      `HOME` empty.

## 2. Nothing Debian or Fedora is left (§3)

- [ ] `git grep -n -i -E "apt install|dnf install|apt-get|\bdnf\b|debian|fedora|distro_family|_FAMILIES" -- src tests`
      prints only the test data that deliberately names Debian, Ubuntu, Fedora
      or Rocky as unsupported systems (in `tests/test_supported_os.py`), and
      nothing under `src/` except the docstring of `supported_os.py` if it names
      a distro.
- [ ] `git grep -n "UNSUPPORTED" -- src tests` prints nothing.
- [ ] `src/vimdiomas/platform/__init__.py` has no `else:` block of stubs.

## 3. Hand-checks on the dev's Mac

- [ ] `uv run vimdiomas doctor` behaves as before (the gate is silent).
- [ ] `uv run vimdiomas` opens the landing menu with the dev's notebooks, as
      before.
- [ ] `uv run python -m vimdiomas --help` still works.
- [ ] The existing `~/.local/bin/vimdiomas` link still runs the app, with no
      reinstall.
- [ ] `vimdiomas wizard`, backed out of with `q` before the last step, still
      opens the wizard (the hidden command, as before).

## 4. Containers

Run from the repo root. Docker is OrbStack's.

- [ ] **Debian refuses**, nothing written:

      docker run --rm --platform linux/amd64 -v "$PWD":/src:ro python:3.14-slim sh -c \
        'cp -r /src /tmp/v && pip install -q /tmp/v && vimdiomas; echo "exit $?"; ls -A ~/.config ~/.cache 2>&1'

      The output is `Vimdiomas runs only on macOS and Arch Linux. This is
      Debian GNU/Linux ….`, then `exit 1`, and neither directory exists. The same
      for `vimdiomas doctor`.
- [ ] **Arch still runs**: the `docker/Dockerfile` image, following
      `docker/README.md`, runs `vimdiomas doctor` with every line `ok` as
      before, and the wizard opens.

## 5. Specs agree with the code (§4)

- [ ] `stack.md` and `design.md` each state the supported platforms once and
      neither mentions Debian or Fedora as supported.
- [ ] `mission.md` and `readme.md` say "Arch Linux" where they said "Linux".
- [ ] `plan.md`, `requirements.md` and this file describe what was built.
