import os
import platform
from pathlib import Path

import pytest

from vimdiomas import install
from vimdiomas.install import LinkState


def _bin_dir(monkeypatch, tmp_path: Path) -> Path:
    """Point the platform layer's user-bin directory at a temp dir.

    Patched on `install` rather than on `vimdiomas.platform`, since that's the
    name `install.py` imported and therefore the one it calls.
    """
    bin_dir = tmp_path / "bin"
    monkeypatch.setattr(install, "user_bin_dir", lambda: bin_dir)
    return bin_dir


def _script(tmp_path: Path) -> Path:
    """Stand in for a venv's `bin/vimdiomas` console script."""
    script = tmp_path / "venv-bin" / "vimdiomas"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/bin/sh\n")
    script.chmod(0o755)
    return script


# --- console_script_path -------------------------------------------------


def test_console_script_found_from_argv(monkeypatch, tmp_path):
    script = _script(tmp_path)
    monkeypatch.setattr(install.sys, "argv", [str(script)])

    assert install.console_script_path() == script


def test_python_m_vimdiomas_has_no_script_to_link(monkeypatch, tmp_path):
    # `python -m vimdiomas` puts the module file in argv[0], which is not a
    # console script and must not be linked.
    module = tmp_path / "vimdiomas" / "__main__.py"
    module.parent.mkdir(parents=True)
    module.write_text("")
    monkeypatch.setattr(install.sys, "argv", [str(module)])

    assert install.console_script_path() is None


def test_missing_argv0_has_no_script(monkeypatch):
    monkeypatch.setattr(install.sys, "argv", [])

    assert install.console_script_path() is None


# --- link_status ---------------------------------------------------------


def test_ready_when_nothing_is_in_the_way(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)

    status = install.link_status(target=script)

    assert status.state is LinkState.READY
    assert status.can_create
    assert status.link_path == bin_dir / "vimdiomas"
    assert status.target == script


def test_already_linked_when_the_link_points_at_this_script(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    bin_dir.mkdir()
    (bin_dir / "vimdiomas").symlink_to(script)

    status = install.link_status(target=script)

    assert status.state is LinkState.ALREADY_LINKED
    assert not status.can_create


def test_occupied_by_another_target(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    other = tmp_path / "other-checkout" / "vimdiomas"
    other.parent.mkdir()
    other.write_text("")
    bin_dir.mkdir()
    (bin_dir / "vimdiomas").symlink_to(other)

    status = install.link_status(target=script)

    assert status.state is LinkState.OCCUPIED
    assert status.occupant == other
    assert not status.can_create


def test_occupied_by_a_regular_file(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    bin_dir.mkdir()
    (bin_dir / "vimdiomas").write_text("someone else's program")

    status = install.link_status(target=script)

    assert status.state is LinkState.OCCUPIED


def test_broken_link_counts_as_occupied(monkeypatch, tmp_path):
    # A link whose target was deleted: exists() is False but it is still
    # something sitting in the way, so it must be reported, not replaced.
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    bin_dir.mkdir()
    (bin_dir / "vimdiomas").symlink_to(tmp_path / "gone")

    status = install.link_status(target=script)

    assert status.state is LinkState.OCCUPIED


def test_no_script_state(monkeypatch, tmp_path):
    _bin_dir(monkeypatch, tmp_path)
    monkeypatch.setattr(install.sys, "argv", [])

    assert install.link_status().state is LinkState.NO_SCRIPT


# --- create_link ---------------------------------------------------------


def test_creates_the_link(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)

    result = install.create_link(install.link_status(target=script))

    assert result.created
    assert (bin_dir / "vimdiomas").is_symlink()
    assert (bin_dir / "vimdiomas").resolve() == script


def test_creates_the_bin_directory_when_missing(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    assert not bin_dir.exists()

    assert install.create_link(install.link_status(target=script)).created
    assert bin_dir.is_dir()


def test_already_linked_is_left_alone(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    bin_dir.mkdir()
    link = bin_dir / "vimdiomas"
    link.symlink_to(script)
    before = link.lstat().st_ino

    result = install.create_link(install.link_status(target=script))

    assert not result.created
    assert result.error is None
    # Not recreated: the same link, not an identical replacement.
    assert link.lstat().st_ino == before


def test_occupied_path_is_never_overwritten(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)
    bin_dir.mkdir()
    (bin_dir / "vimdiomas").write_text("someone else's program")

    result = install.create_link(install.link_status(target=script))

    assert not result.created
    assert (bin_dir / "vimdiomas").read_text() == "someone else's program"


def test_failure_is_reported_not_raised(monkeypatch, tmp_path):
    bin_dir = _bin_dir(monkeypatch, tmp_path)
    script = _script(tmp_path)

    def boom(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(Path, "symlink_to", boom)

    result = install.create_link(install.link_status(target=script))

    assert not result.created
    assert "read-only file system" in result.error


# --- on_path -------------------------------------------------------------


def test_on_path_matches_an_unresolved_entry(monkeypatch, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", f"/usr/bin{os.pathsep}{bin_dir}")

    assert install.on_path(bin_dir)


def test_not_on_path(monkeypatch, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", "/usr/bin")

    assert not install.on_path(bin_dir)


def test_on_path_ignores_empty_entries(monkeypatch, tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    monkeypatch.setenv("PATH", f"{os.pathsep}{os.pathsep}/usr/bin")

    assert not install.on_path(bin_dir)


# --- the shell-config hint -----------------------------------------------


def test_shell_config_follows_shell_env(monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/bash")
    assert install.shell_config_path().name == ".bashrc"

    monkeypatch.setenv("SHELL", "/opt/homebrew/bin/fish")
    assert install.shell_config_path().name == "config.fish"


def test_shell_config_falls_back_to_the_platform_default(monkeypatch):
    monkeypatch.delenv("SHELL", raising=False)

    assert install.shell_config_path().name == install.DEFAULT_SHELL_CONFIG


@pytest.mark.parametrize("default", [".zshrc", ".bashrc"])
def test_shell_config_fallback_per_platform(monkeypatch, default):
    """macOS falls back to `.zshrc`, Linux to `.bashrc` (Sprint 5 M7's D6)."""
    monkeypatch.setenv("SHELL", "/usr/bin/nu")
    monkeypatch.setattr(install, "DEFAULT_SHELL_CONFIG", default)

    assert install.shell_config_path().name == default


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS parity")
def test_shell_config_still_falls_back_to_zshrc_on_macos(monkeypatch):
    monkeypatch.delenv("SHELL", raising=False)

    assert install.shell_config_path().name == ".zshrc"


def test_export_line_is_home_relative(monkeypatch):
    monkeypatch.setenv("SHELL", "/bin/zsh")

    line = install.path_export_line(Path.home() / ".local" / "bin")

    assert line == 'export PATH="$HOME/.local/bin:$PATH"'


def test_export_line_for_fish(monkeypatch):
    monkeypatch.setenv("SHELL", "/opt/homebrew/bin/fish")

    line = install.path_export_line(Path.home() / ".local" / "bin")

    assert line == "fish_add_path $HOME/.local/bin"


# --- ensure_on_path / directory_already_in_shell_config -------------------


def _config_file(monkeypatch, tmp_path: Path) -> Path:
    """Point `shell_config_path()` at a temp file, so these tests never
    touch the real ~/.zshrc."""
    config_path = tmp_path / "shell-rc"
    monkeypatch.setattr(install, "shell_config_path", lambda: config_path)
    return config_path


def test_ensure_on_path_creates_a_missing_config_file(monkeypatch, tmp_path):
    config_path = _config_file(monkeypatch, tmp_path)
    bin_dir = Path.home() / ".local" / "bin"
    assert not config_path.exists()

    result = install.ensure_on_path(bin_dir)

    assert result.added
    assert not result.already_present
    assert result.error is None
    assert install.path_export_line(bin_dir) in config_path.read_text()


def test_ensure_on_path_appends_without_disturbing_existing_content(
    monkeypatch, tmp_path
):
    config_path = _config_file(monkeypatch, tmp_path)
    config_path.write_text("# my existing config\nalias ll='ls -la'\n")
    bin_dir = Path.home() / ".local" / "bin"

    install.ensure_on_path(bin_dir)

    text = config_path.read_text()
    assert text.startswith("# my existing config\nalias ll='ls -la'\n")
    assert install.path_export_line(bin_dir) in text


def test_ensure_on_path_never_duplicates_the_line(monkeypatch, tmp_path):
    config_path = _config_file(monkeypatch, tmp_path)
    bin_dir = Path.home() / ".local" / "bin"

    first = install.ensure_on_path(bin_dir)
    after_first = config_path.read_text()
    second = install.ensure_on_path(bin_dir)
    after_second = config_path.read_text()

    assert first.added
    assert not second.added
    assert second.already_present
    # Byte-for-byte identical: a second run must not append a second copy.
    assert after_first == after_second
    assert after_second.count(install.path_export_line(bin_dir)) == 1


def test_ensure_on_path_recognises_a_hand_written_line(monkeypatch, tmp_path):
    # A line the user (or a previous, un-instrumented run) already added,
    # not necessarily byte-identical to path_export_line's own formatting.
    config_path = _config_file(monkeypatch, tmp_path)
    bin_dir = Path.home() / ".local" / "bin"
    config_path.write_text('export PATH="$HOME/.local/bin:$PATH"  # added by me\n')

    result = install.ensure_on_path(bin_dir)

    assert not result.added
    assert result.already_present


def test_ensure_on_path_reports_failure_without_raising(monkeypatch, tmp_path):
    config_path = _config_file(monkeypatch, tmp_path)
    bin_dir = Path.home() / ".local" / "bin"

    def boom(*args, **kwargs):
        raise OSError("permission denied")

    monkeypatch.setattr(Path, "open", boom)

    result = install.ensure_on_path(bin_dir)

    assert not result.added
    assert result.error is not None
    assert "permission denied" in result.error


def test_directory_already_in_shell_config_false_when_file_missing(
    monkeypatch, tmp_path
):
    _config_file(monkeypatch, tmp_path)
    assert not install.directory_already_in_shell_config(Path.home() / ".local" / "bin")


def test_directory_already_in_shell_config_true_after_ensure(monkeypatch, tmp_path):
    _config_file(monkeypatch, tmp_path)
    bin_dir = Path.home() / ".local" / "bin"

    install.ensure_on_path(bin_dir)

    assert install.directory_already_in_shell_config(bin_dir)
