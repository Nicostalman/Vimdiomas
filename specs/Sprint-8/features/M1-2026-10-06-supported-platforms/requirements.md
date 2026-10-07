# M1 · Supported platforms — requirements

## Anchor: the roadmap

From [`../../roadmap-sprint-8.md`](../../roadmap-sprint-8.md), *M1 · Supported
platforms*:

> **Deliverable.**
>
> - The platform layer identifies exactly two supported platforms: **macOS** and
>   **Arch Linux** (by `/etc/os-release`, the way `distro_family()` already reads
>   it, Arch derivatives included or not as the spec decides).
> - On anything else, **the wizard refuses to start**: a message saying only
>   macOS and Arch Linux are supported, and nothing written.
> - The Debian and Fedora tables in `platform/linux.py`'s `INSTALL_HINTS`, and any
>   code that exists only to choose between them, are removed.
> - `stack.md` and `design.md` state the supported platforms once.
>
> **Done when.** On macOS and Arch the wizard runs as before. On another distro
> (checked in a Debian container, or with `os-release` faked in tests) it refuses
> with the agreed message and writes nothing. No Debian or Fedora command is left
> in the code, and the full test suite passes.

The backlog, *Fix wizard* ([`../../guidelines/backlog.md`](../../guidelines/backlog.md)):
"The wizard should check for the os. For now, only Macos and Arch linux will be
supported." and "Take for granted Brew and Pacman are installed." The second
line is M3's concern; here it only means the gate checks the OS, never whether
`brew` or `pacman` exist.

## Decisions

Settled with the dev in the spec conversation, 2026-10-06.

| Decision | Rationale |
| --- | --- |
| **"Refuses" covers the whole app**: the TUI (wizard, or an existing config), `vimdiomas compile`, `vimdiomas doctor`, and the hidden `vimdiomas wizard` | Dev's choice, over wizard-only and wizard-plus-TUI. A config copied from another machine gets the same answer as a fresh install, and no unsupported code path survives. |
| **The refusal is one line on stderr and exit status 1**, printed before any TUI starts | Dev's choice, over a TUI screen. It is the only form that also works for `compile` and `doctor`, and it needs nothing from Textual. |
| **Arch derivatives count as Arch**: `ID` is `arch`, or `ID_LIKE` lists `arch` | Dev's choice. Manjaro, EndeavourOS and Arch ARM share pacman and the package names. Only `archlinux:latest` is tested; the docs say "Arch Linux" and the derivatives are best-effort. |
| **A stdlib-only check runs first, and the inert fallback block is removed** | Dev's choice, over keeping the stubs or gating in `vimdiomas/__init__.py`. Nothing past the gate runs on an unsupported OS, so the stubs in `platform/__init__.py` would be dead code. See §2 for how the gate gets in front of the imports. |

## 1. What is supported

Exactly two platforms, decided by one function in a new module,
`src/vimdiomas/supported_os.py`, which imports nothing from the package (it
must run where `vimdiomas.platform` cannot even be imported):

- **macOS**: `platform.system() == "Darwin"`.
- **Arch Linux**: `platform.system() == "Linux"` and
  `platform.freedesktop_os_release()` has `ID == "arch"` or `"arch"` among the
  words of `ID_LIKE`.
- **Anything else is unsupported**: other distros, Linux with a missing or
  unreadable `/etc/os-release` (`OSError`), Windows, the BSDs. WSL reports
  `Linux` and is judged by its distro like any other Linux.

`supported_os.current()` returns `"macos"`, `"arch"` or `None`.

## 2. The gate

- **`vimdiomas/__main__.py` becomes a thin entry point.** Its `main()` calls
  `supported_os.refuse_unless_supported()` first, then imports and runs the
  real `main` from `vimdiomas/cli.py` (the current body of `__main__.py`, moved
  by `git mv`; `cli.py` has no `if __name__ == "__main__"` of its own, so
  `python -m vimdiomas.cli` cannot go around the gate). The console script stays `vimdiomas.__main__:main`, so an
  existing install's link keeps working with no reinstall, and
  `install.py`'s reading of `.../vimdiomas/__main__.py` for `python -m
  vimdiomas` still holds.
- **The gate runs before anything else**, in particular before
  `migrate_legacy_paths()` (which writes) and before the hidden `wizard`
  command is looked at. `cli.py`'s imports (`doctor`, `compile`, `languages`,
  the TUI) are what reach `vimdiomas.platform`, so they stay at module top in
  `cli.py` and are simply not imported until the gate has passed.
- **The refusal**: `refuse_unless_supported()` does nothing on a supported
  platform. On any other it prints to stderr and raises `SystemExit(1)`:

  ```
  Vimdiomas runs only on macOS and Arch Linux. This is <name>.
  ```

  `<name>` is `PRETTY_NAME` from `os-release` when there is one, else its
  `ID`, else `platform.system()` (`Linux` for an unreadable `os-release`,
  `Windows`, `FreeBSD`). One line, no hint of
  what to install, nothing else printed.
- **Nothing is written**: no config, no cache, no migration of the legacy
  Idiomas paths, no link. The refusal happens before any of those code paths
  is reachable.
- `pip install` itself is not gated: `pyproject.toml` stays as it is. The
  refusal is the first thing the user meets on running the command.

## 3. The platform layer

- **`platform/__init__.py`**: Darwin imports `macos`, Linux imports `linux`;
  the `else:` block of inert stubs is deleted. Any other system raises
  `ImportError` naming the two platforms, a backstop that is unreachable
  through the app because of §2. (Linux modules are imported on any distro,
  since importing `linux.py` has no side effects; the gate is what refuses
  Debian, not the import.)
- **`platform/linux.py` is the Arch module.** Deleted: `_FAMILIES`,
  `distro_family()`, the `debian` and `fedora` tables. `INSTALL_HINTS` becomes
  the flat Arch table (the commands are unchanged, `pacman` only), and
  `install_hint(dependency)` is a plain lookup, `INSTALL_HINTS.get(dependency)`.
  The docstrings that describe "distro family" and (D5) are rewritten. The
  module keeps the name `linux.py`, since the Arch-vs-other question is the
  gate's, not the layer's.
- **`user_bin_dir()` can no longer be `None`**, since the only implementation
  that returned `None` was the deleted fallback. Removed with it:
  `install.LinkState.UNSUPPORTED`, the `bin_dir is None` branch of
  `install.link_status`, the wizard's "isn't supported on this platform yet"
  text, and the `if bin_dir is None: return` guard in
  `config.migrate_legacy_paths`. The return type is `Path`.
- **`doctor` and the other callers are untouched** in behaviour. `install_hint`
  keeps returning the Arch and macOS commands; M3 is what stops showing them.

## 4. Specs and docs

- **`specs/current/stack.md`** states the supported platforms once, in its
  opening line and in the *Platform layer* bullet (which currently says every
  other platform gets inert no-ops, and that hints are picked by distro
  family). The Linux wording that names Debian, Fedora, or "the distro" is
  corrected; the Arch image remains the Linux reference machine.
- **`specs/current/design.md`** gains one subsection, *Supported platforms*:
  macOS and Arch Linux (derivatives included), and what an unsupported system
  gets (the one-line refusal, exit 1, for every command, before anything is
  written). It is the one place the convention is stated.
- **`specs/current/mission.md`** line 32 ("macOS or Linux") becomes "macOS or
  Arch Linux".
- **`readme.md`** line 26 ("macOS and Linux") becomes "macOS and Arch Linux".
  This is the one README edit; the dangling *Dependencies* link and the claim
  that the user installs tools first stay as they are (see notes, Postponed).
  *Proposed by the agent, not asked: the roadmap names only `stack.md` and
  `design.md`; dev to confirm or strike in the spec review.*

## 5. Tests

- **`tests/test_supported_os.py`** (new): `current()` over a table of faked
  `platform.system()` and `freedesktop_os_release()` values: Darwin; `arch`;
  `endeavouros` and `manjaro` with `ID_LIKE=arch`; `archarm`; `debian`,
  `ubuntu` (`ID_LIKE=debian`), `fedora`, `rocky`, `opensuse-tumbleweed`, an
  empty release, an unreadable one (`OSError`); `Windows` and `FreeBSD`. The
  refusal message with and without `PRETTY_NAME`.
- **The gate, through `main()`**: on a faked unsupported system, each of
  `vimdiomas`, `compile`, `doctor` and `wizard` prints the message to stderr,
  exits 1, and leaves a temporary `HOME` empty (no config file, no cache,
  `migrate_legacy_paths` and the TUI never called). On a supported system
  `main()` reaches `cli.main()` as before.
- **Removed or rewritten**: the Debian and Fedora cases in
  `tests/test_platform_linux.py` (`test_distro_family`,
  `test_unreadable_os_release_has_no_family`, the parametrized
  every-family test, `test_unknown_family_offers_no_command`; what is left is
  the Arch commands and a lookup of an unknown dependency); the same
  monkeypatching of `linux.distro_family` in `tests/test_doctor.py`
  (`_as_linux_arch`; `test_unknown_distro_offers_no_command` is deleted, and
  the "no platform command" test patches `doctor.install_hint` to return
  `None` instead); the `UNSUPPORTED` cases in `tests/test_install.py` and
  `tests/test_tui_wizard.py`; the `apt` command in `tests/test_tui_dependencies.py`'s
  fixtures, now a pacman one (the test is about the offer, not the distro).
- **`tests/test_main.py`, `tests/test_config.py`, `tests/conftest.py`**
  import `vimdiomas.cli` where they imported `vimdiomas.__main__`. Their
  assertions are unchanged.
- **`tests/test_platform.py`**: `LAYER_NAMES` and its dispatch test are
  unchanged; the skipif for "neither macOS nor Linux" goes with the fallback.
  (Only `test_dispatches_to_this_machines_module` had it.)

## Context

- `distro_family()` came from Sprint 5 M7 (D5), together with the Debian and
  Fedora tables. Those specs are frozen and keep them.
- The refusal text is user-facing, but it is a one-line stderr message, not a
  screen, so it follows *Failures are reported, never fatal*'s spirit (say what
  happened and nothing else) rather than a new convention.
- M2 and M3 build on `supported_os.current()`: M3 chooses its commands by
  `"macos"` or `"arch"`.

## Out of scope

- Checking that `brew` or `pacman` exist (backlog: taken for granted).
- Any change to what `doctor` prints or to the wizard's screens (M2, M3).
- Windows and WSL support; Debian, Fedora and other distros (Postponed).
- Gating `pip install`.
