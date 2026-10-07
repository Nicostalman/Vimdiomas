"""The support gate (Sprint 8 M1): macOS and Arch Linux, nothing else."""

import platform

import pytest

from vimdiomas import __main__ as entry
from vimdiomas import supported_os


def _fake_system(monkeypatch, system, release=None):
    """`release` of `OSError` makes `freedesktop_os_release()` raise it."""
    monkeypatch.setattr(platform, "system", lambda: system)

    def freedesktop_os_release():
        if release is OSError:
            raise OSError("no os-release")
        return release or {}

    monkeypatch.setattr(platform, "freedesktop_os_release", freedesktop_os_release)


@pytest.mark.parametrize(
    ("system", "release", "expected"),
    [
        ("Darwin", None, "macos"),
        ("Linux", {"ID": "arch"}, "arch"),
        ("Linux", {"ID": "endeavouros", "ID_LIKE": "arch"}, "arch"),
        ("Linux", {"ID": "manjaro", "ID_LIKE": "arch"}, "arch"),
        ("Linux", {"ID": "archarm", "ID_LIKE": "arch"}, "arch"),
        ("Linux", {"ID": "debian"}, None),
        ("Linux", {"ID": "ubuntu", "ID_LIKE": "debian"}, None),
        ("Linux", {"ID": "fedora"}, None),
        ("Linux", {"ID": "rocky", "ID_LIKE": "rhel centos fedora"}, None),
        ("Linux", {"ID": "opensuse-tumbleweed", "ID_LIKE": "opensuse suse"}, None),
        ("Linux", {}, None),
        ("Linux", OSError, None),
        ("Windows", None, None),
        ("FreeBSD", None, None),
    ],
)
def test_current(monkeypatch, system, release, expected):
    _fake_system(monkeypatch, system, release)

    assert supported_os.current() == expected


def _refusal(monkeypatch, capsys, system, release=None):
    _fake_system(monkeypatch, system, release)
    with pytest.raises(SystemExit) as exit_info:
        supported_os.refuse_unless_supported()
    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    return captured.err


def test_refusal_names_the_pretty_name(monkeypatch, capsys):
    err = _refusal(
        monkeypatch, capsys, "Linux", {"ID": "debian", "PRETTY_NAME": "Debian GNU/Linux 13 (trixie)"}
    )

    assert err == (
        "Vimdiomas runs only on macOS and Arch Linux. This is Debian GNU/Linux 13 (trixie).\n"
    )


def test_refusal_falls_back_to_the_id(monkeypatch, capsys):
    err = _refusal(monkeypatch, capsys, "Linux", {"ID": "fedora"})

    assert err == "Vimdiomas runs only on macOS and Arch Linux. This is fedora.\n"


@pytest.mark.parametrize("release", [{}, OSError])
def test_refusal_falls_back_to_the_system(monkeypatch, capsys, release):
    err = _refusal(monkeypatch, capsys, "Linux", release)

    assert err == "Vimdiomas runs only on macOS and Arch Linux. This is Linux.\n"


def test_refusal_names_a_non_linux_system(monkeypatch, capsys):
    err = _refusal(monkeypatch, capsys, "Windows")

    assert err == "Vimdiomas runs only on macOS and Arch Linux. This is Windows.\n"


@pytest.mark.parametrize(
    "system, release", [("Darwin", None), ("Linux", {"ID": "arch", "PRETTY_NAME": "Arch Linux"})]
)
def test_supported_systems_pass_silently(monkeypatch, capsys, system, release):
    _fake_system(monkeypatch, system, release)

    supported_os.refuse_unless_supported()

    captured = capsys.readouterr()
    assert captured.out == captured.err == ""


# --- The gate, through main() ---------------------------------------------


@pytest.mark.parametrize("argv", [[], ["compile"], ["doctor"], ["wizard"]])
def test_unsupported_system_refuses_every_command_and_writes_nothing(
    monkeypatch, capsys, tmp_path, argv
):
    _fake_system(monkeypatch, "Linux", {"ID": "debian", "PRETTY_NAME": "Debian GNU/Linux"})
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("sys.argv", ["vimdiomas", *argv])
    from vimdiomas import cli

    def reached(*_args, **_kwargs):
        raise AssertionError("the gate let the command through")

    for name in ("main", "_tui", "_compile", "_doctor", "_run_wizard", "migrate_legacy_paths"):
        monkeypatch.setattr(cli, name, reached)

    with pytest.raises(SystemExit) as exit_info:
        entry.main()

    assert exit_info.value.code == 1
    assert "Vimdiomas runs only on macOS and Arch Linux. This is Debian GNU/Linux." in (
        capsys.readouterr().err
    )
    assert list(tmp_path.iterdir()) == []


def test_supported_system_reaches_the_real_main(monkeypatch):
    from vimdiomas import cli

    _fake_system(monkeypatch, "Darwin")
    calls = []
    monkeypatch.setattr(cli, "main", lambda: calls.append("main"))

    entry.main()

    assert calls == ["main"]
