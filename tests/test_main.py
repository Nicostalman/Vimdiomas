import subprocess
import sys

import pytest

from vimdiomas import cli as main_module
from vimdiomas.compile import CompileReport
from vimdiomas.config import Config


def _point_config_at(monkeypatch, path):
    """Both names for the config file: `cli` checks its own import of
    `CONFIG_PATH`, but `load_config()` reads `vimdiomas.config`'s. Patching
    only the first let these tests read the machine's real config — which
    passed on the dev's Mac only because its user name happens to be the
    tests' own "Nico" (found in Sprint 5 M7's container run)."""
    monkeypatch.setattr(main_module, "CONFIG_PATH", path)
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", path)


class _FakeWizardApp:
    """Stands in for `WizardApp`: `.run()` returns whatever the test wants,
    without actually driving a Textual app."""

    instances: list["_FakeWizardApp"] = []

    def __init__(self, result):
        self.result = result
        _FakeWizardApp.instances.append(self)

    def run(self):
        return self.result


class _FakeVimdiomasApp:
    instances: list["_FakeVimdiomasApp"] = []

    def __init__(self, config):
        self.config = config
        _FakeVimdiomasApp.instances.append(self)

    def run(self):
        pass


def _patch_apps(monkeypatch, wizard_result):
    _FakeWizardApp.instances = []
    _FakeVimdiomasApp.instances = []
    monkeypatch.setattr(main_module, "WizardApp", lambda: _FakeWizardApp(wizard_result))
    monkeypatch.setattr(main_module, "VimdiomasApp", _FakeVimdiomasApp)


def test_tui_runs_wizard_when_no_config_exists(tmp_path, monkeypatch):
    config = Config(user_name="Nico", root=tmp_path, languages=[])
    _point_config_at(monkeypatch, tmp_path / "config.toml")
    _patch_apps(monkeypatch, wizard_result=config)

    main_module._tui()

    assert len(_FakeWizardApp.instances) == 1
    assert _FakeVimdiomasApp.instances[0].config is config


def test_tui_does_not_start_app_when_wizard_aborted(tmp_path, monkeypatch):
    _point_config_at(monkeypatch, tmp_path / "config.toml")
    _patch_apps(monkeypatch, wizard_result=None)

    main_module._tui()

    assert len(_FakeWizardApp.instances) == 1
    assert _FakeVimdiomasApp.instances == []


def test_tui_loads_config_directly_when_one_exists(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n', encoding="utf-8"
    )
    _point_config_at(monkeypatch, config_path)
    _patch_apps(monkeypatch, wizard_result=None)

    main_module._tui()

    assert _FakeWizardApp.instances == []
    assert _FakeVimdiomasApp.instances[0].config.user_name == "Nico"


def test_run_wizard_opens_wizard_even_with_a_config_present(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n', encoding="utf-8"
    )
    _point_config_at(monkeypatch, config_path)
    _patch_apps(monkeypatch, wizard_result=None)

    main_module._run_wizard()

    assert len(_FakeWizardApp.instances) == 1
    # Aborting the wizard doesn't touch the real config on disk.
    assert config_path.read_text(encoding="utf-8").startswith('user_name = "Nico"')


def test_wizard_subcommand_dispatches_to_run_wizard(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n', encoding="utf-8"
    )
    _point_config_at(monkeypatch, config_path)
    monkeypatch.setattr("sys.argv", ["vimdiomas", "wizard"])
    _patch_apps(monkeypatch, wizard_result=None)

    main_module.main()

    assert len(_FakeWizardApp.instances) == 1


def test_compile_passes_force_flag_through_to_compile_all(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n\n'
        '[[languages]]\nname = "Chinese"\n',
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, config_path)

    calls = []
    monkeypatch.setattr(
        main_module,
        "compile_all",
        lambda tree_root, kind, force=False: calls.append(force) or CompileReport(),
    )

    main_module._compile(force=True)

    assert calls == [True]


def test_compile_defaults_force_to_false(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n\n'
        '[[languages]]\nname = "Chinese"\n',
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, config_path)

    calls = []
    monkeypatch.setattr(
        main_module,
        "compile_all",
        lambda tree_root, kind, force=False: calls.append(force) or CompileReport(),
    )

    main_module._compile()

    assert calls == [False]


def test_compile_subcommand_parses_force_flag(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n\n'
        '[[languages]]\nname = "Chinese"\n',
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, config_path)
    monkeypatch.setattr("sys.argv", ["vimdiomas", "compile", "--force"])

    calls = []
    monkeypatch.setattr(
        main_module,
        "compile_all",
        lambda tree_root, kind, force=False: calls.append(force) or CompileReport(),
    )

    main_module.main()

    assert calls == [True]


def test_wizard_subcommand_is_invisible_to_help():
    # "wizard" is checked directly against sys.argv before argparse ever
    # sees it (not registered via `add_parser`, unlike `argparse.SUPPRESS`,
    # which still leaks the name into --help's usage/choices line) — so
    # `vimdiomas --help` never mentions it.
    result = subprocess.run(
        [sys.executable, "-m", "vimdiomas", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert "wizard" not in result.stdout
    assert "wizard" not in result.stderr


# -- Sprint 6 M2 · #12: the CLI reports failures and exits 1 ---------------


def _chinese_config(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n\n[[languages]]\nname = "Chinese"\n',
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, config_path)
    monkeypatch.setattr("vimdiomas.compile.CACHE_PATH", tmp_path / "cache.json")
    vocab = tmp_path / "tree-Chinese" / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Good.md").write_text("# Good\n\n字\tzi4\tchar\n", encoding="utf-8")
    return vocab


def test_compile_cli_prints_failures_to_stderr_and_exits_1(tmp_path, monkeypatch, capsys):
    import pytest

    vocab = _chinese_config(tmp_path, monkeypatch)
    (vocab / "Bad.md").write_text("# Bad\n\n字\tzi4\tchar\n", encoding="utf-8")

    def _fake(src, dst, **kwargs):
        if src.stem == "Bad":
            raise subprocess.CalledProcessError(
                43, ["pandoc"], stderr=b"! Undefined control sequence.\n"
            )
        dst.write_bytes(b"%PDF fake")

    monkeypatch.setattr("vimdiomas.compile.compile_file", _fake)

    with pytest.raises(SystemExit) as exit_info:
        main_module._compile()

    assert exit_info.value.code == 1
    out, err = capsys.readouterr()
    assert "Good.pdf" in out
    assert "Traceback" not in out + err
    assert "Bad.md" in err
    assert "! Undefined control sequence." in err


def test_compile_cli_exits_0_on_a_clean_tree(tmp_path, monkeypatch, capsys):
    _chinese_config(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "vimdiomas.compile.compile_file", lambda src, dst, **kwargs: dst.write_bytes(b"%PDF")
    )

    main_module._compile()  # no SystemExit

    out, err = capsys.readouterr()
    assert "Good.pdf" in out
    assert err == ""


def test_compile_cli_prints_warnings_without_failing(tmp_path, monkeypatch, capsys):
    """Sprint 6 M3, #4: a syllable printed without its tone mark is reported
    on stderr, and — the file having compiled — the exit code stays 0."""
    vocab = _chinese_config(tmp_path, monkeypatch)
    (vocab / "Odd.md").write_text("# Odd\n\n字\tx4\tchar\n", encoding="utf-8")
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", lambda md, dst, kind: dst.write_bytes(b"%PDF"))

    main_module._compile()  # no SystemExit

    out, err = capsys.readouterr()
    assert "Odd.pdf" in out
    assert "1 warning(s)" in err
    assert "Odd.md" in err
    assert "x4" in err


def test_compile_skips_a_language_that_is_not_in_the_registry(tmp_path, monkeypatch):
    """Sprint 6 M5: a hand-edited config naming a language the registry
    doesn't know is skipped, as a non-functional language is — no exception."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n\n[[languages]]\nname = "Klingon"\n',
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, config_path)
    calls = []
    monkeypatch.setattr(
        main_module,
        "compile_all",
        lambda tree_root, kind, force=False: calls.append(tree_root) or CompileReport(),
    )

    main_module._compile()  # no exception

    assert calls == []


def test_compile_compiles_a_german_tree_with_the_alphabetical_kind(tmp_path, monkeypatch, capsys):
    """Sprint 6 M6: German is functional, so `vimdiomas compile` builds its tree
    — with no CJK font handed to pandoc."""
    from vimdiomas.languages import ALPHABETICAL

    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path}"\n\n[[languages]]\nname = "German"\n',
        encoding="utf-8",
    )
    _point_config_at(monkeypatch, config_path)
    monkeypatch.setattr("vimdiomas.compile.CACHE_PATH", tmp_path / "cache.json")
    vocab = tmp_path / "tree-German" / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "Essen.md").write_text("# Essen\n\nHaus\thouse\n", encoding="utf-8")
    kinds = []
    monkeypatch.setattr(
        "vimdiomas.compile._run_pandoc",
        lambda md, dst, kind: (kinds.append(kind), dst.write_bytes(b"%PDF")),
    )

    main_module._compile()  # no SystemExit

    assert kinds == [ALPHABETICAL]
    assert (vocab / "Essen.pdf").exists()
    assert "German: compiled 1 file(s)" in capsys.readouterr().out


# -- Sprint 6 M7: doctor knows which languages need what -------------------


def _doctor_with(monkeypatch, tmp_path, languages, *, xecjk_ok):
    from vimdiomas import doctor
    from vimdiomas.config import LanguageConfig, save_config

    _point_config_at(monkeypatch, tmp_path / "config.toml")
    if languages is not None:
        save_config(
            Config(
                user_name="Nico",
                root=tmp_path,
                languages=[LanguageConfig(name=name) for name in languages],
            )
        )
    monkeypatch.setattr(doctor.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(doctor, "_has_xecjk", lambda: xecjk_ok)
    monkeypatch.setattr(doctor, "cjk_font_installed", lambda: xecjk_ok)


def test_doctor_cli_passes_a_german_only_config_without_xecjk(tmp_path, monkeypatch, capsys):
    _doctor_with(monkeypatch, tmp_path, ["German"], xecjk_ok=False)

    main_module._doctor()  # no SystemExit

    assert "[Chinese] xeCJK:" in capsys.readouterr().out


def test_doctor_cli_fails_a_chinese_config_without_xecjk(tmp_path, monkeypatch):
    _doctor_with(monkeypatch, tmp_path, ["German", "Chinese"], xecjk_ok=False)

    with pytest.raises(SystemExit) as exit_info:
        main_module._doctor()

    assert exit_info.value.code == 1


def test_doctor_cli_without_a_config_fails_only_on_required_checks(tmp_path, monkeypatch):
    _doctor_with(monkeypatch, tmp_path, None, xecjk_ok=False)

    main_module._doctor()  # no SystemExit: xeCJK is not required of every install


def test_compile_cli_with_no_language_registered_exits_0(tmp_path, monkeypatch, capsys):
    """Sprint 6 M8: every language can be removed, so an empty list is a
    config like any other: nothing to compile."""
    from vimdiomas.config import save_config

    _point_config_at(monkeypatch, tmp_path / "config.toml")
    monkeypatch.setattr("vimdiomas.compile.CACHE_PATH", tmp_path / "cache.json")
    save_config(Config(user_name="Nico", root=tmp_path, languages=[]))

    main_module._compile()  # no SystemExit

    assert capsys.readouterr().err == ""


def test_doctor_cli_with_no_language_registered_exits_0(tmp_path, monkeypatch):
    _doctor_with(monkeypatch, tmp_path, [], xecjk_ok=False)

    main_module._doctor()  # no SystemExit


def test_compile_cli_prints_parse_warnings_grouped_and_exits_zero(tmp_path, monkeypatch, capsys):
    """Sprint 6 M9: a file holding something outside the format is reported
    on stderr, grouped under its path, and still compiles — so the exit code
    stays 0."""
    vocab = _chinese_config(tmp_path, monkeypatch)
    (vocab / "Odd.md").write_text(
        "# Odd\n\n字\tzi4\tchar\tjunk\n\n| word | gloss |\n", encoding="utf-8"
    )
    monkeypatch.setattr("vimdiomas.compile._run_pandoc", lambda md, dst, kind: dst.write_bytes(b"%PDF"))

    main_module._compile()  # no SystemExit

    out, err = capsys.readouterr()
    assert "Odd.pdf" in out
    assert "2 warning(s)" in err
    assert err.count("Odd.md") == 1
    # The message, then the offending line indented under it.
    assert "    line 3: extra column(s) never rendered: junk\n" in err
    assert "        字\tzi4\tchar\tjunk\n" in err
    assert "    line 5: unrecognized line\n        | word | gloss |\n" in err


def test_compile_cli_still_exits_one_when_a_file_fails(tmp_path, monkeypatch, capsys):
    """A warning does not change the exit status; a failure still does."""
    import subprocess

    vocab = _chinese_config(tmp_path, monkeypatch)
    (vocab / "Odd.md").write_text("# Odd\n\n字\tzi4\tchar\n\n| a | b |\n", encoding="utf-8")

    def _boom(md, dst, kind):
        raise subprocess.CalledProcessError(1, "pandoc", stderr=b"! nope")

    monkeypatch.setattr("vimdiomas.compile._run_pandoc", _boom)

    with pytest.raises(SystemExit) as exc:
        main_module._compile()

    assert exc.value.code == 1
    _, err = capsys.readouterr()
    assert "file(s) failed" in err
    assert "warning(s)" in err


# -- Sprint 8 M3: PATH, and doctor says what is missing, never how ------------


def test_main_extends_the_path_before_it_dispatches(tmp_path, monkeypatch):
    _point_config_at(monkeypatch, tmp_path / "config.toml")
    order = []
    monkeypatch.setattr(main_module, "extend_path", lambda: order.append("extend_path"))
    monkeypatch.setattr(main_module, "_doctor", lambda: order.append("doctor"))
    monkeypatch.setattr("sys.argv", ["vimdiomas", "doctor"])

    main_module.main()

    assert order == ["extend_path", "doctor"]


def test_main_extends_the_path_for_the_wizard_too(tmp_path, monkeypatch):
    _point_config_at(monkeypatch, tmp_path / "config.toml")
    order = []
    monkeypatch.setattr(main_module, "extend_path", lambda: order.append("extend_path"))
    monkeypatch.setattr(main_module, "_run_wizard", lambda: order.append("wizard"))
    monkeypatch.setattr("sys.argv", ["vimdiomas", "wizard"])

    main_module.main()

    assert order == ["extend_path", "wizard"]


def test_doctor_cli_prints_ok_missing_and_missing_with_a_detail(tmp_path, monkeypatch, capsys):
    from vimdiomas import doctor

    _point_config_at(monkeypatch, tmp_path / "config.toml")
    monkeypatch.setattr(
        doctor,
        "run",
        lambda: [
            doctor.Check("pandoc", "pandoc", required=True, ok=True),
            doctor.Check("xelatex", "xelatex", required=True, ok=False),
            doctor.Check(
                "LaTeX packages", "latex-packages", required=True, ok=False, detail="caption, xcolor"
            ),
            doctor.Check("nvim", "nvim", required=False, ok=False),
        ],
    )

    with pytest.raises(SystemExit) as exit_info:
        main_module._doctor()

    assert exit_info.value.code == 1
    assert capsys.readouterr().out.splitlines() == [
        "[required] pandoc: ok",
        "[required] xelatex: missing",
        "[required] LaTeX packages: missing: caption, xcolor",
        "[optional] nvim: missing",
    ]


def test_doctor_cli_exit_status_ignores_a_missing_optional_check(tmp_path, monkeypatch):
    from vimdiomas import doctor

    _point_config_at(monkeypatch, tmp_path / "config.toml")
    monkeypatch.setattr(
        doctor,
        "run",
        lambda: [
            doctor.Check("pandoc", "pandoc", required=True, ok=True),
            doctor.Check("nvim", "nvim", required=False, ok=False),
        ],
    )

    main_module._doctor()  # no SystemExit
