"""`vimdiomas.platform.linux`, unit-tested on any OS (Sprint 5 M7): the module
is imported directly and every call out to the system is monkeypatched, the
way `macos.py` is tested in `test_platform.py`."""

import os
import subprocess
from pathlib import Path

import pytest

from vimdiomas.platform import InputSource, linux


class _Result:
    def __init__(self, stdout=""):
        self.stdout = stdout


@pytest.fixture(autouse=True)
def _fresh_framework_cache():
    linux._framework.cache_clear()
    yield
    linux._framework.cache_clear()


def _recording_run(monkeypatch, fails=(), stdout=""):
    """Patch `subprocess.run` to record every command; any command whose
    first word is in `fails` exits non-zero."""
    calls = []

    def _run(args, **kwargs):
        calls.append(args)
        if args[0] in fails:
            raise subprocess.CalledProcessError(1, args)
        return _Result(stdout)

    monkeypatch.setattr(linux.subprocess, "run", _run)
    return calls


def _missing(*args, **kwargs):
    raise FileNotFoundError("not installed")


# --- opening files ----------------------------------------------------------


def test_open_file_shells_out_to_xdg_open(monkeypatch):
    calls = _recording_run(monkeypatch)

    linux.open_file(Path("/tmp/x.pdf"))

    assert calls == [["xdg-open", "/tmp/x.pdf"]]


def test_open_file_without_xdg_open_is_a_noop(monkeypatch):
    monkeypatch.setattr(linux.subprocess, "run", _missing)

    linux.open_file(Path("/tmp/x.pdf"))  # must not raise


# --- the CJK font -------------------------------------------------------------


def test_font_is_noto_serif_cjk_sc():
    assert linux.CJK_FONT_NAME == "Noto Serif CJK SC"


def test_font_installed_when_fc_list_finds_the_family(monkeypatch):
    calls = _recording_run(monkeypatch, stdout="Noto Serif CJK SC,Noto Serif CJK SC SemiBold\n")

    assert linux.cjk_font_installed() is True
    assert calls == [["fc-list", ":family=Noto Serif CJK SC", "family"]]


def test_font_missing_when_fc_list_prints_nothing(monkeypatch):
    _recording_run(monkeypatch, stdout="\n")

    assert linux.cjk_font_installed() is False


def test_font_missing_without_fc_list(monkeypatch):
    monkeypatch.setattr(linux.subprocess, "run", _missing)

    assert linux.cjk_font_installed() is False


# --- the user-bin dir and shell config -----------------------------------------


def test_user_bin_dir_is_local_bin(monkeypatch, tmp_path):
    monkeypatch.setattr(linux.Path, "home", lambda: tmp_path)

    assert linux.user_bin_dir() == tmp_path / ".local" / "bin"


def test_default_shell_config_is_bashrc():
    assert linux.DEFAULT_SHELL_CONFIG == ".bashrc"


# --- input-method framework detection and switching -----------------------------


def test_framework_prefers_fcitx5(monkeypatch):
    _recording_run(monkeypatch)

    assert linux._framework() == "fcitx5"


def test_framework_falls_back_to_ibus(monkeypatch):
    _recording_run(monkeypatch, fails={"fcitx5-remote"})

    assert linux._framework() == "ibus"


def test_framework_is_none_with_neither_running(monkeypatch):
    _recording_run(monkeypatch, fails={"fcitx5-remote", "ibus"})

    assert linux._framework() is None


def test_framework_is_none_with_neither_installed(monkeypatch):
    monkeypatch.setattr(linux.subprocess, "run", _missing)

    assert linux._framework() is None


def test_framework_is_probed_once(monkeypatch):
    calls = _recording_run(monkeypatch)

    linux._framework()
    linux._framework()

    assert calls == [["fcitx5-remote"]]


def test_switch_with_fcitx5(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: "fcitx5")
    calls = _recording_run(monkeypatch)

    linux.switch_input_source("pinyin")

    assert calls == [["fcitx5-remote", "-s", "pinyin"]]


def test_switch_with_ibus(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: "ibus")
    calls = _recording_run(monkeypatch)

    linux.switch_input_source("libpinyin")

    assert calls == [["ibus", "engine", "libpinyin"]]


def test_switch_with_no_framework_is_a_noop(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: None)
    calls = _recording_run(monkeypatch)

    linux.switch_input_source("pinyin")

    assert calls == []


def test_failing_switch_is_a_noop(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: "fcitx5")
    _recording_run(monkeypatch, fails={"fcitx5-remote"})

    linux.switch_input_source("pinyin")  # must not raise


def test_input_switcher_is_available_with_either_framework(monkeypatch):
    monkeypatch.setattr(linux.shutil, "which", lambda name: "/usr/bin/ibus" if name == "ibus" else None)
    assert linux.input_switcher() == ("fcitx5 or ibus", True, "https://github.com/fcitx/fcitx5")

    monkeypatch.setattr(linux.shutil, "which", lambda name: None)
    assert linux.input_switcher()[1] is False


# --- listing sources: fcitx5's profile --------------------------------------------

FCITX5_PROFILE = """\
[Groups/0]
Name=Default
Default Layout=us
DefaultIM=pinyin

[Groups/0/Items/0]
Name=keyboard-us
Layout=

[Groups/0/Items/1]
Name=pinyin
Layout=

[Groups/1]
Name=Other
Default Layout=de

[Groups/1/Items/0]
Name=keyboard-de
Layout=

[Groups/1/Items/1]
Name=pinyin
Layout=

[GroupOrder]
0=Default
1=Other
"""


def test_fcitx5_profile_names_in_order_without_duplicates(tmp_path):
    profile = tmp_path / "profile"
    profile.write_text(FCITX5_PROFILE)

    assert linux._fcitx5_profile_sources(profile) == ["keyboard-us", "pinyin", "keyboard-de"]


def test_missing_fcitx5_profile_gives_nothing(tmp_path):
    assert linux._fcitx5_profile_sources(tmp_path / "missing") == []


def test_garbled_fcitx5_profile_gives_nothing(tmp_path):
    profile = tmp_path / "profile"
    profile.write_text("Name=pinyin with no section\n")

    assert linux._fcitx5_profile_sources(profile) == []


def test_lists_fcitx5_sources_with_display_names(monkeypatch, tmp_path):
    (tmp_path / ".config" / "fcitx5").mkdir(parents=True)
    (tmp_path / ".config" / "fcitx5" / "profile").write_text(FCITX5_PROFILE)
    monkeypatch.setattr(linux.Path, "home", lambda: tmp_path)
    monkeypatch.setattr(linux, "_framework", lambda: "fcitx5")

    assert linux.list_input_sources() == [
        InputSource(id="keyboard-us", name="English (US)"),
        InputSource(id="pinyin", name="Pinyin"),
        InputSource(id="keyboard-de", name="German"),
    ]


# --- listing sources: ibus' gsettings ---------------------------------------------


def test_ibus_engines_parse():
    assert linux._ibus_preload_engines("['xkb:us::eng', 'libpinyin']\n") == [
        "xkb:us::eng",
        "libpinyin",
    ]


def test_ibus_empty_list_parses():
    assert linux._ibus_preload_engines("@as []\n") == []


@pytest.mark.parametrize("garbage", ["", "not a list", "[1, 2]", "{'a': 'b'}", "['unclosed"])
def test_ibus_garbage_gives_nothing(garbage):
    assert linux._ibus_preload_engines(garbage) == []


def test_lists_ibus_sources(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: "ibus")
    calls = _recording_run(monkeypatch, stdout="['xkb:us::eng', 'libpinyin']\n")

    assert linux.list_input_sources() == [
        InputSource(id="xkb:us::eng", name="English (US)"),
        InputSource(id="libpinyin", name="Pinyin"),
    ]
    assert calls == [["gsettings", "get", "org.freedesktop.ibus.general", "preload-engines"]]


def test_ibus_without_gsettings_lists_nothing(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: "ibus")
    monkeypatch.setattr(linux.subprocess, "run", _missing)

    assert linux.list_input_sources() == []


def test_no_framework_lists_nothing(monkeypatch):
    monkeypatch.setattr(linux, "_framework", lambda: None)

    assert linux.list_input_sources() == []


def test_keyboard_layouts_for_both_frameworks():
    assert linux.is_keyboard_layout("keyboard-us")
    assert linux.is_keyboard_layout("xkb:us::eng")
    assert not linux.is_keyboard_layout("pinyin")
    assert not linux.is_keyboard_layout("libpinyin")


def test_unknown_source_keeps_its_raw_id():
    assert linux.display_name("mozc") == "mozc"
    assert linux.display_name("pinyin") == "Pinyin"


# --- install ------------------------------------------------------------------------


DEPENDENCIES = ["pandoc", "xelatex", "xecjk", "cjk-font", "input-switcher", "nvim", "pdftoppm"]


def _installing(keys, missing_latex=lambda: []):
    calls = []
    linux.install(keys, lambda argv: calls.append(argv) or True, missing_latex)
    return calls


def test_install_is_one_pacman_command():
    calls = _installing(["pandoc", "nvim", "pdftoppm"])
    assert calls == [["sudo", "pacman", "-S", "--needed", "--noconfirm", "pandoc-cli", "neovim", "poppler"]]


def test_install_a_tex_adds_whatever_the_template_lacks():
    calls = _installing(["xelatex", "latex-packages"], lambda: ["caption", "lmodern", "geometry"])
    assert calls == [
        [
            "sudo", "pacman", "-S", "--needed", "--noconfirm",
            "texlive-xetex", "texlive-latexrecommended", "texlive-fontsrecommended", "texlive-latex",
        ]
    ]


def test_install_a_bare_machine_gets_every_latex_package():
    # No kpsewhich to ask yet: `missing_latex` is None.
    calls = _installing(["xelatex", "latex-packages"], lambda: None)
    assert set(calls[0][5:]) == {
        "texlive-xetex",
        "texlive-latex",
        "texlive-latexrecommended",
        "texlive-fontsrecommended",
    }


def test_install_names_each_package_once():
    calls = _installing(["xelatex", "input-switcher"], lambda: ["fontspec", "caption", "xcolor"])
    packages = calls[0][5:]
    assert len(packages) == len(set(packages))
    assert packages[:3] == ["texlive-xetex", "fcitx5-im", "fcitx5-chinese-addons"]


def test_install_latex_packages_alone_does_not_install_the_tex():
    calls = _installing(["latex-packages"], lambda: ["xcolor"])
    assert calls[0][5:] == ["texlive-latexrecommended"]


def test_install_asks_about_the_template_only_with_a_tex_key():
    assert _installing(["nvim"], lambda: pytest.fail("not asked")) != []


def test_install_with_nothing_to_install_runs_nothing():
    assert _installing(["no-such-key"], lambda: pytest.fail("not asked")) == []
    assert _installing([]) == []
    assert _installing(["latex-packages"], lambda: []) == []


def test_install_a_language_adds_xecjk_and_the_font():
    calls = _installing(["xecjk", "cjk-font"])
    assert calls[0][5:] == ["texlive-langchinese", "noto-fonts-cjk"]


def test_every_dependency_but_latex_packages_is_installable():
    for dependency in DEPENDENCIES:
        assert linux.installable(dependency), dependency
    assert linux.installable("latex-packages")
    assert not linux.installable("no-such-key")


def test_pacman_is_the_package_manager(monkeypatch):
    assert linux.PACKAGE_MANAGER == "pacman"
    monkeypatch.setattr(linux.shutil, "which", lambda name: "/usr/bin/pacman" if name == "pacman" else None)
    assert linux.package_manager_available() is True
    monkeypatch.setattr(linux.shutil, "which", lambda name: None)
    assert linux.package_manager_available() is False


def test_extend_path_changes_nothing(monkeypatch):
    monkeypatch.setenv("PATH", "/usr/bin")
    linux.extend_path()
    assert os.environ["PATH"] == "/usr/bin"
