# M1 · Supported platforms — plan

The task groups are ordered so that each one depends only on the groups before
it. Section numbers (§) refer to [`requirements.md`](requirements.md).

## 1. The check (§1)

- `src/vimdiomas/supported_os.py`, stdlib only: `current()`, the message, and
  `refuse_unless_supported()` (prints to stderr, `SystemExit(1)`).
- `tests/test_supported_os.py`: the table of faked systems, and the message
  with and without `PRETTY_NAME`.

## 2. The gate (§2)

- `git mv src/vimdiomas/__main__.py src/vimdiomas/cli.py`.
- New `src/vimdiomas/__main__.py`: `main()` runs the gate, then imports and
  calls `cli.main`; `if __name__ == "__main__": main()`.
- Point `tests/test_main.py`, `tests/test_config.py` and `tests/conftest.py` at
  `vimdiomas.cli`.
- Gate tests through `main()` for the four commands, with a temporary `HOME`
  checked empty afterwards.

## 3. The platform layer (§3)

- `platform/linux.py`: delete `_FAMILIES`, `distro_family()` and the Debian and
  Fedora tables; flatten `INSTALL_HINTS`; simplify `install_hint`; rewrite the
  docstrings.
- `platform/__init__.py`: delete the fallback block; `ImportError` for any
  other system; update the module docstring.
- Remove `LinkState.UNSUPPORTED`, the `None` branches (`install.link_status`,
  `config.migrate_legacy_paths`), the wizard's unsupported text; `user_bin_dir`
  returns `Path`.
- Update `test_platform_linux.py`, `test_doctor.py`, `test_install.py`,
  `test_tui_wizard.py`, `test_platform.py` as §5 lists.

## 4. Specs and docs (§4)

- `stack.md`, `design.md` (*Supported platforms*), `mission.md` line 32,
  `readme.md` line 26.
- If anything comes up while implementing, the three files here are updated
  first.

## 5. Checks before the hand-off

- Full test suite.
- The greps and the container runs in [`validation.md`](validation.md).
- Stop for the dev's review and hand-testing on the Mac.

## 6. Hand-off, merge

- PR, squash-merge, cleanup per `feature-spec` step 9.
- Notes on `main`: M1's decisions into settled form; anything newly postponed.
