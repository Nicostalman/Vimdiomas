import os
import platform
import plistlib
import subprocess
from pathlib import Path

import pytest

import vimdiomas.platform as platform_layer
from vimdiomas.platform import InputSource, linux, macos

_SYSTEM = platform.system()
on_macos = pytest.mark.skipif(_SYSTEM != "Darwin", reason="dispatch on macOS")
_EXPECTED_MODULE = {"Darwin": macos, "Linux": linux}.get(_SYSTEM)

LAYER_NAMES = [
    "CJK_FONT_NAME",
    "CJK_FONT_PATH",
    "CJK_FONT_URL",
    "DEFAULT_SHELL_CONFIG",
    "INPUT_SOURCES_SETTINGS",
    "PACKAGE_MANAGER",
    "cjk_font_installed",
    "extend_path",
    "input_switcher",
    "install",
    "installable",
    "is_keyboard_layout",
    "list_input_sources",
    "open_file",
    "package_manager_available",
    "switch_input_source",
    "user_bin_dir",
]


@pytest.mark.parametrize("name", LAYER_NAMES)
def test_dispatches_to_this_machines_module(name):
    # vimdiomas.platform should resolve to this OS's own module — macos.py on
    # the dev's Mac, linux.py in the verification image (Sprint 5 M7).
    assert getattr(platform_layer, name) is getattr(_EXPECTED_MODULE, name)


def test_both_modules_offer_the_whole_surface():
    for module in (macos, linux):
        for name in LAYER_NAMES:
            assert hasattr(module, name), f"{module.__name__} lacks {name}"


@on_macos
def test_macos_input_source_advisories_are_unchanged():
    from vimdiomas.tui.screens.input_methods import NO_SOURCES_MESSAGE, ONE_SOURCE_MESSAGE

    assert NO_SOURCES_MESSAGE == (
        "No input sources found. Add one in System Settings › Keyboard › "
        "Input Sources; until then, Vimdiomas won't switch input for you."
    )
    assert ONE_SOURCE_MESSAGE == (
        "Only one input source is enabled, so both fields use it and nothing "
        "will switch. Add another in System Settings › Keyboard › Input Sources, "
        "then set it here from Settings › Input methods."
    )


def test_macos_keyboard_layouts_are_the_keylayout_ids():
    assert macos.is_keyboard_layout("com.apple.keylayout.US")
    assert not macos.is_keyboard_layout("com.apple.inputmethod.SCIM.ITABC")


@on_macos
def test_macos_font_is_still_songti_sc():
    # Approved in Sprint 5 M3; M7 must not change it (and so M2's stamps
    # stay valid on the dev's real tree).
    assert platform_layer.CJK_FONT_NAME == "Songti SC"


def test_open_file_shells_out_to_open(monkeypatch):
    calls = []
    monkeypatch.setattr(macos.subprocess, "run", lambda args, **kw: calls.append(args))

    macos.open_file(Path("/tmp/x.pdf"))

    assert calls == [["open", "/tmp/x.pdf"]]


def test_switch_input_source_calls_macism(monkeypatch):
    calls = []
    monkeypatch.setattr(macos.subprocess, "run", lambda args, **kw: calls.append(args))

    macos.switch_input_source("com.apple.inputmethod.SCIM.ITABC")

    assert calls == [["macism", "com.apple.inputmethod.SCIM.ITABC"]]


def test_switch_input_source_missing_macism_is_a_noop(monkeypatch):
    def _raise(*a, **kw):
        raise FileNotFoundError("macism not found")

    monkeypatch.setattr(macos.subprocess, "run", _raise)

    macos.switch_input_source("com.apple.inputmethod.SCIM.ITABC")  # must not raise


def test_switch_input_source_rejected_source_is_a_noop(monkeypatch):
    def _raise(*a, **kw):
        raise subprocess.CalledProcessError(1, ["macism"])

    monkeypatch.setattr(macos.subprocess, "run", _raise)

    macos.switch_input_source("com.apple.inputmethod.SCIM.ITABC")  # must not raise


def test_cjk_font_installed_checks_its_own_path(monkeypatch, tmp_path):
    present = tmp_path / "Heiti.ttc"
    present.write_bytes(b"")

    monkeypatch.setattr(macos, "CJK_FONT_PATH", str(present))
    assert macos.cjk_font_installed() is True
    monkeypatch.setattr(macos, "CJK_FONT_PATH", str(tmp_path / "missing.ttc"))
    assert macos.cjk_font_installed() is False


def _recorder(fail=()):
    """A `run` that records each command and fails those whose second word
    (or first, for `brew`) is in `fail`."""
    calls = []

    def run(argv):
        calls.append(argv)
        return not any(word in argv for word in fail)

    return calls, run


def _stub_tlmgr(monkeypatch, path="/Library/TeX/texbin/tlmgr"):
    monkeypatch.setattr(macos.shutil, "which", lambda name: path if name == "tlmgr" else None)


def test_macos_brew_installs_every_formula_in_one_command(monkeypatch):
    _stub_tlmgr(monkeypatch, None)
    calls, run = _recorder()
    macos.install(["pandoc", "input-switcher", "nvim", "pdftoppm"], run, lambda: [])
    assert calls == [["brew", "install", "pandoc", "laishulu/homebrew/macism", "neovim", "poppler"]]


def test_macos_no_tex_installs_basictex_then_tlmgr_for_what_it_lacks(monkeypatch):
    _stub_tlmgr(monkeypatch)
    monkeypatch.setattr(macos, "extend_path", lambda: calls.append("extend_path"))
    calls, run = _recorder()
    macos.install(["xelatex", "latex-packages"], run, lambda: ["caption", "longtable", "array"])
    assert calls == [
        ["brew", "install", "--cask", "basictex"],
        "extend_path",
        ["sudo", "/Library/TeX/texbin/tlmgr", "update", "--self"],
        ["sudo", "/Library/TeX/texbin/tlmgr", "install", "caption", "tools"],
    ]


def test_macos_stock_basictex_runs_no_tlmgr(monkeypatch):
    # A stock BasicTeX has every package the check looks for (Sprint 8 notes).
    _stub_tlmgr(monkeypatch)
    monkeypatch.setattr(macos, "extend_path", lambda: None)
    calls, run = _recorder()
    macos.install(["xelatex", "latex-packages"], run, lambda: [])
    assert calls == [["brew", "install", "--cask", "basictex"]]


def test_macos_a_tex_that_cant_be_asked_runs_no_tlmgr(monkeypatch):
    _stub_tlmgr(monkeypatch)
    monkeypatch.setattr(macos, "extend_path", lambda: None)
    calls, run = _recorder()
    macos.install(["xelatex", "latex-packages"], run, lambda: None)
    assert calls == [["brew", "install", "--cask", "basictex"]]


def test_macos_latex_packages_alone_skips_the_cask(monkeypatch):
    _stub_tlmgr(monkeypatch)
    calls, run = _recorder()
    macos.install(["latex-packages"], run, lambda: ["xcolor", "fontspec"])
    assert calls == [
        ["sudo", "/Library/TeX/texbin/tlmgr", "update", "--self"],
        ["sudo", "/Library/TeX/texbin/tlmgr", "install", "xcolor", "fontspec"],
    ]


def test_macos_xecjk_updates_tlmgr_itself_first(monkeypatch):
    _stub_tlmgr(monkeypatch)
    calls, run = _recorder()
    macos.install(["xecjk"], run, lambda: pytest.fail("xelatex wasn't installed"))
    assert calls == [
        ["sudo", "/Library/TeX/texbin/tlmgr", "update", "--self"],
        ["sudo", "/Library/TeX/texbin/tlmgr", "install", "xecjk"],
    ]


def test_macos_xecjk_joins_the_missing_latex_packages_in_one_install(monkeypatch):
    _stub_tlmgr(monkeypatch)
    monkeypatch.setattr(macos, "extend_path", lambda: None)
    calls, run = _recorder()
    macos.install(["xelatex", "latex-packages", "xecjk"], run, lambda: ["caption"])
    assert calls[-1] == ["sudo", "/Library/TeX/texbin/tlmgr", "install", "caption", "xecjk"]


def test_macos_without_tlmgr_both_tlmgr_commands_are_skipped(monkeypatch):
    _stub_tlmgr(monkeypatch, None)
    calls, run = _recorder()
    macos.install(["xecjk"], run, lambda: [])
    assert calls == []


def test_macos_a_failing_command_does_not_stop_the_next(monkeypatch):
    _stub_tlmgr(monkeypatch)
    monkeypatch.setattr(macos, "extend_path", lambda: None)
    calls, run = _recorder(fail=("brew", "--self"))
    macos.install(["pandoc", "xelatex", "xecjk"], run, lambda: [])
    assert [c[0:2] for c in calls] == [
        ["brew", "install"],
        ["brew", "install"],
        ["sudo", "/Library/TeX/texbin/tlmgr"],
        ["sudo", "/Library/TeX/texbin/tlmgr"],
    ]


def test_macos_ignores_keys_it_cannot_install(monkeypatch):
    _stub_tlmgr(monkeypatch)
    calls, run = _recorder()
    macos.install(["cjk-font", "no-such-key"], run, lambda: pytest.fail("not asked"))
    assert calls == []


def test_macos_installable_keys():
    for key in ("pandoc", "input-switcher", "nvim", "pdftoppm", "xelatex", "latex-packages", "xecjk"):
        assert macos.installable(key), key
    assert not macos.installable("cjk-font")
    assert not macos.installable("no-such-key")


def test_macos_package_manager_is_brew(monkeypatch):
    assert macos.PACKAGE_MANAGER == "Homebrew"
    monkeypatch.setattr(macos.shutil, "which", lambda name: "/x/brew" if name == "brew" else None)
    assert macos.package_manager_available() is True
    monkeypatch.setattr(macos.shutil, "which", lambda name: None)
    assert macos.package_manager_available() is False


def test_macos_extend_path_appends_the_known_dirs_that_exist(monkeypatch, tmp_path):
    present, absent = tmp_path / "brew", tmp_path / "texbin"
    present.mkdir()
    monkeypatch.setattr(macos, "EXTRA_PATH_DIRS", (str(present), str(absent)))
    monkeypatch.setenv("PATH", "/usr/bin")
    macos.extend_path()
    assert os.environ["PATH"] == f"/usr/bin{os.pathsep}{present}"


def test_macos_extend_path_never_duplicates(monkeypatch, tmp_path):
    (tmp_path / "brew").mkdir()
    monkeypatch.setattr(macos, "EXTRA_PATH_DIRS", (str(tmp_path / "brew"),))
    monkeypatch.setenv("PATH", "/usr/bin")
    macos.extend_path()
    macos.extend_path()
    assert os.environ["PATH"].split(os.pathsep) == ["/usr/bin", str(tmp_path / "brew")]


def test_macos_extend_path_sees_a_dir_that_appears_later(monkeypatch, tmp_path):
    texbin = tmp_path / "texbin"
    monkeypatch.setattr(macos, "EXTRA_PATH_DIRS", (str(texbin),))
    monkeypatch.setenv("PATH", "/usr/bin")
    macos.extend_path()
    assert os.environ["PATH"] == "/usr/bin"
    texbin.mkdir()
    macos.extend_path()
    assert os.environ["PATH"] == f"/usr/bin{os.pathsep}{texbin}"


def test_macos_extend_path_with_an_empty_path_adds_no_blank_entry(monkeypatch, tmp_path):
    (tmp_path / "brew").mkdir()
    monkeypatch.setattr(macos, "EXTRA_PATH_DIRS", (str(tmp_path / "brew"),))
    monkeypatch.setenv("PATH", "")
    macos.extend_path()
    assert os.environ["PATH"] == str(tmp_path / "brew")


def test_macos_input_switcher_is_macism(monkeypatch):
    monkeypatch.setattr(macos.shutil, "which", lambda name: "/bin/macism")
    assert macos.input_switcher() == ("macism", True, "https://github.com/laishulu/macism")
    monkeypatch.setattr(macos.shutil, "which", lambda name: None)
    assert macos.input_switcher()[1] is False


# --- Listing the enabled input sources (Sprint 4 M6) ---------------------


def _defaults_output(entries):
    """What `defaults export com.apple.HIToolbox -` writes to stdout."""
    return plistlib.dumps({"AppleEnabledInputSources": entries})


def _patch_defaults(monkeypatch, entries):
    class _Result:
        stdout = _defaults_output(entries)

    monkeypatch.setattr(macos.subprocess, "run", lambda args, **kw: _Result())


def test_keyboard_layout_gets_the_keylayout_prefix(monkeypatch):
    _patch_defaults(
        monkeypatch,
        [
            {
                "InputSourceKind": "Keyboard Layout",
                "KeyboardLayout Name": "USInternational-PC",
                "KeyboardLayout ID": 15000,
            }
        ],
    )

    assert macos.list_input_sources() == [
        InputSource(
            id="com.apple.keylayout.USInternational-PC",
            name="U.S. International – PC",
        )
    ]


def test_input_mode_is_used_verbatim(monkeypatch):
    _patch_defaults(
        monkeypatch,
        [
            {
                "InputSourceKind": "Input Mode",
                "Bundle ID": "com.apple.inputmethod.SCIM",
                "Input Mode": "com.apple.inputmethod.SCIM.ITABC",
            }
        ],
    )

    assert macos.list_input_sources() == [
        InputSource(
            id="com.apple.inputmethod.SCIM.ITABC", name="Pinyin – Simplified"
        )
    ]


def test_ime_container_is_dropped_when_one_of_its_modes_is_enabled(monkeypatch):
    """A multi-mode IME appears twice — once as the container, once per
    mode. Offering both would be a duplicate that switches to an arbitrary
    mode."""
    _patch_defaults(
        monkeypatch,
        [
            {
                "InputSourceKind": "Input Mode",
                "Bundle ID": "com.apple.inputmethod.SCIM",
                "Input Mode": "com.apple.inputmethod.SCIM.ITABC",
            },
            {
                "InputSourceKind": "Keyboard Input Method",
                "Bundle ID": "com.apple.inputmethod.SCIM",
            },
        ],
    )

    assert [source.id for source in macos.list_input_sources()] == [
        "com.apple.inputmethod.SCIM.ITABC"
    ]


def test_ime_container_is_kept_when_it_has_no_enabled_mode(monkeypatch):
    _patch_defaults(
        monkeypatch,
        [
            {
                "InputSourceKind": "Keyboard Input Method",
                "Bundle ID": "com.example.inputmethod.Solo",
            }
        ],
    )

    assert [source.id for source in macos.list_input_sources()] == [
        "com.example.inputmethod.Solo"
    ]


def test_non_keyboard_input_methods_are_dropped(monkeypatch):
    _patch_defaults(
        monkeypatch,
        [
            {
                "InputSourceKind": "Non Keyboard Input Method",
                "Bundle ID": "com.apple.CharacterPaletteIM",
            },
            {
                "InputSourceKind": "Non Keyboard Input Method",
                "Bundle ID": "com.apple.PressAndHold",
            },
        ],
    )

    assert macos.list_input_sources() == []


def test_order_is_preserved_and_duplicates_collapse(monkeypatch):
    _patch_defaults(
        monkeypatch,
        [
            {"InputSourceKind": "Keyboard Layout", "KeyboardLayout Name": "German"},
            {"InputSourceKind": "Keyboard Layout", "KeyboardLayout Name": "US"},
            {"InputSourceKind": "Keyboard Layout", "KeyboardLayout Name": "German"},
        ],
    )

    assert [source.id for source in macos.list_input_sources()] == [
        "com.apple.keylayout.German",
        "com.apple.keylayout.US",
    ]


def test_unknown_source_falls_back_to_its_last_segment(monkeypatch):
    _patch_defaults(
        monkeypatch,
        [{"InputSourceKind": "Keyboard Layout", "KeyboardLayout Name": "Klingon"}],
    )

    assert macos.list_input_sources() == [
        InputSource(id="com.apple.keylayout.Klingon", name="Klingon")
    ]


def test_missing_defaults_binary_returns_no_sources(monkeypatch):
    def _raise(*a, **kw):
        raise FileNotFoundError("defaults not found")

    monkeypatch.setattr(macos.subprocess, "run", _raise)

    assert macos.list_input_sources() == []


def test_failing_defaults_call_returns_no_sources(monkeypatch):
    def _raise(*a, **kw):
        raise subprocess.CalledProcessError(1, ["defaults"])

    monkeypatch.setattr(macos.subprocess, "run", _raise)

    assert macos.list_input_sources() == []


def test_unparseable_output_returns_no_sources(monkeypatch):
    class _Result:
        stdout = b"not a plist"

    monkeypatch.setattr(macos.subprocess, "run", lambda args, **kw: _Result())

    assert macos.list_input_sources() == []
