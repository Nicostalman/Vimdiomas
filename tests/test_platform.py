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
    "cjk_font_installed",
    "input_switcher",
    "install_hint",
    "is_keyboard_layout",
    "list_input_sources",
    "open_file",
    "switch_input_source",
    "user_bin_dir",
]


@pytest.mark.skipif(_EXPECTED_MODULE is None, reason="neither macOS nor Linux")
@pytest.mark.parametrize("name", LAYER_NAMES)
def test_dispatches_to_this_machines_module(name):
    # vimdiomas.platform should resolve to this OS's own module rather than the
    # cross-platform no-ops — macos.py on the dev's Mac, linux.py in the
    # verification image (Sprint 5 M7).
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


def test_macos_install_hints_are_todays_commands():
    assert macos.install_hint("pandoc") == "brew install pandoc"
    assert macos.install_hint("xecjk") == "sudo tlmgr install xecjk"
    assert macos.install_hint("input-switcher") == "brew install laishulu/homebrew/macism"
    assert macos.install_hint("nvim") == "brew install neovim"
    assert macos.install_hint("pdftoppm") == "brew install poppler"
    assert macos.install_hint("xelatex") is None
    assert macos.install_hint("cjk-font") is None


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
