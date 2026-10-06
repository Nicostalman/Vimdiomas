from pathlib import Path

import pytest

from vimdiomas.config import (
    migrate_legacy_paths,
    Config,
    ConfigNotFoundError,
    LanguageConfig,
    _toml_lines,
    load_config,
    save_config,
    validate_tree_root,
)


def test_raises_when_config_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", tmp_path / "config.toml")

    with pytest.raises(ConfigNotFoundError):
        load_config()


def test_loads_user_name_root_and_languages(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\n'
        f'root = "{tmp_path / "Vimdiomas"}"\n'
        "\n"
        "[[languages]]\n"
        'name = "Chinese"\n'
        "\n"
        "[[languages]]\n"
        'name = "German"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = load_config()

    assert config.user_name == "Nico"
    assert config.root == tmp_path / "Vimdiomas"
    assert config.languages == [
        LanguageConfig(name="Chinese"),
        LanguageConfig(name="German"),
    ]


def test_language_input_methods_default_empty_when_omitted(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\n'
        f'root = "{tmp_path}"\n'
        "\n"
        "[[languages]]\n"
        'name = "Chinese"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = load_config()

    assert config.languages[0].input_method == ""
    assert config.languages[0].translation_input_method == ""


def test_language_input_methods_read_when_present(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\n'
        f'root = "{tmp_path}"\n'
        "\n"
        "[[languages]]\n"
        'name = "Chinese"\n'
        'input_method = "com.apple.inputmethod.SCIM.ITABC"\n'
        'translation_input_method = "com.apple.keylayout.USInternational-PC"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = load_config()

    assert config.languages[0].input_method == "com.apple.inputmethod.SCIM.ITABC"
    assert config.languages[0].translation_input_method == "com.apple.keylayout.USInternational-PC"


def test_tree_root_derives_from_root_and_language(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\n'
        f'root = "{tmp_path / "Vimdiomas"}"\n'
        "\n"
        "[[languages]]\n"
        'name = "Chinese"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = load_config()

    assert config.tree_root("Chinese") == tmp_path / "Vimdiomas" / "tree-Chinese"


def test_save_config_round_trips_through_load_config(tmp_path, monkeypatch):
    config_path = tmp_path / "nested" / "config.toml"
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = Config(
        user_name="Nico",
        root=tmp_path / "Vimdiomas",
        languages=[
            LanguageConfig(name="Chinese"),
            LanguageConfig(
                name="German",
                input_method="",
                translation_input_method="com.apple.keylayout.German",
            ),
        ],
    )

    save_config(config)

    assert load_config() == config


def test_save_config_round_trips_with_no_languages(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = Config(user_name="Nico", root=tmp_path / "Vimdiomas", languages=[])

    save_config(config)

    assert load_config() == config


def test_save_config_creates_missing_parent_directory(tmp_path, monkeypatch):
    config_path = tmp_path / "deep" / "nested" / "config.toml"
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    save_config(Config(user_name="Nico", root=tmp_path, languages=[]))

    assert config_path.exists()


def test_save_config_leaves_no_temp_file_behind(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    save_config(Config(user_name="Nico", root=tmp_path, languages=[]))

    assert sorted(p.name for p in tmp_path.iterdir()) == ["config.toml"]


def test_validate_tree_root_rejects_path_inside_package():
    from vimdiomas.config import PACKAGE_ROOT

    assert validate_tree_root(PACKAGE_ROOT / "trees") is not None


def test_validate_tree_root_rejects_unwritable_path(tmp_path):
    unwritable = tmp_path / "locked"
    unwritable.mkdir()
    unwritable.chmod(0o500)
    try:
        assert validate_tree_root(unwritable / "Vimdiomas") is not None
    finally:
        unwritable.chmod(0o700)


def test_validate_tree_root_accepts_writable_path(tmp_path):
    assert validate_tree_root(tmp_path / "Vimdiomas") is None


def test_hanzi_input_method_key_is_ignored_not_migrated(tmp_path, monkeypatch):
    """Sprint 4 M6 renamed the key. M4's standing rule is that old config
    keys are ignored rather than migrated, so a file still carrying the old
    one loads as unconfigured."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\n'
        f'root = "{tmp_path}"\n'
        "\n"
        "[[languages]]\n"
        'name = "Chinese"\n'
        'hanzi_input_method = "com.apple.inputmethod.SCIM.ITABC"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = load_config()

    assert config.languages[0].input_method == ""


def test_language_looks_up_a_registered_language(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\n'
        f'root = "{tmp_path}"\n'
        "\n"
        "[[languages]]\n"
        'name = "Chinese"\n'
        'input_method = "com.apple.inputmethod.SCIM.ITABC"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    config = load_config()

    assert config.language("Chinese").input_method == "com.apple.inputmethod.SCIM.ITABC"
    assert config.language("German") is None


# -- Sprint 6 M1 · #6: the config survives a quote or a backslash ----------


def _config(tmp_path, monkeypatch, **kwargs) -> Config:
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", tmp_path / "config.toml")
    defaults = dict(user_name="Nico", root=tmp_path / "Vimdiomas", languages=[])
    return Config(**{**defaults, **kwargs})


def test_apostrophe_in_user_name_survives_a_save(tmp_path, monkeypatch):
    """The report's #6 reproduction: `!r` wrote a TOML *basic* string escaped
    by Python's rules, so a user named O'Brien finished the wizard and then
    could not launch the app again."""
    config = _config(tmp_path, monkeypatch, user_name='O\'Brien "Nico"')
    save_config(config)
    assert load_config().user_name == 'O\'Brien "Nico"'


def test_both_quote_characters_and_a_backslash_round_trip(tmp_path, monkeypatch):
    """The milestone's done-when line, exactly."""
    name = 'O\'Brien "Nico" C:\\Users\\path'
    save_config(_config(tmp_path, monkeypatch, user_name=name))
    assert load_config().user_name == name


def test_control_characters_in_user_name_round_trip(tmp_path, monkeypatch):
    name = "a\nb\tc\x00d\x7fe\bf"
    save_config(_config(tmp_path, monkeypatch, user_name=name))
    assert load_config().user_name == name


def test_root_path_with_a_quote_and_a_backslash_round_trips(tmp_path, monkeypatch):
    root = tmp_path / "it's a \\ tree"
    save_config(_config(tmp_path, monkeypatch, root=root))
    assert load_config().root == root


def test_language_fields_with_quotes_round_trip(tmp_path, monkeypatch):
    language = LanguageConfig(
        name="O'Brien's Chinese",
        input_method='com.apple."odd".id',
        translation_input_method="back\\slash",
    )
    save_config(_config(tmp_path, monkeypatch, languages=[language]))
    assert load_config().languages == [language]


def test_an_ordinary_config_is_written_byte_identically_to_before(tmp_path):
    """A correctness fix that reformatted every working config would be a
    worse outcome than the bug, so a value TOML can hold in a literal string
    is still written as one — which is byte-for-byte what `!r` produced."""
    config = Config(
        user_name="Nico",
        root=tmp_path / "Vimdiomas",
        languages=[LanguageConfig(name="Chinese", input_method="com.apple.x")],
    )
    assert _toml_lines(config) == (
        f"user_name = {'Nico'!r}\n"
        f"root = {str(config.root)!r}\n"
        "\n"
        "[[languages]]\n"
        f"name = {'Chinese'!r}\n"
        f"input_method = {'com.apple.x'!r}\n"
    )


def test_a_broken_encoder_raises_and_leaves_the_existing_config_alone(
    tmp_path, monkeypatch
):
    config_path = tmp_path / "config.toml"
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)
    save_config(Config(user_name="Nico", root=tmp_path, languages=[]))
    before = config_path.read_text(encoding="utf-8")

    monkeypatch.setattr("vimdiomas.config._toml_string", lambda value: "'wrong'")
    with pytest.raises(ValueError):
        save_config(Config(user_name="Changed", root=tmp_path, languages=[]))

    assert config_path.read_text(encoding="utf-8") == before
    assert list(tmp_path.glob("*.tmp")) == []


# -- Sprint 6 M1 · #7: a relative root is anchored, not re-interpreted ------


def test_relative_root_loads_identically_from_any_working_directory(
    tmp_path, monkeypatch
):
    """The bug: a relative root was re-interpreted against whatever directory
    the process was launched from, so the same command found a different tree
    — or none — depending on where it was run."""
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        'user_name = "Nico"\nroot = "notebooks"\n', encoding="utf-8"
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()

    monkeypatch.chdir(tmp_path / "a")
    from_a = load_config().root
    monkeypatch.chdir(tmp_path / "b")
    from_b = load_config().root

    assert from_a == from_b
    assert from_a.is_absolute()
    assert from_a == (Path.home() / "notebooks").resolve()


def test_a_relative_root_is_not_rewritten_on_load(tmp_path, monkeypatch):
    """Loading is a read: the app doesn't edit the user's config behind their
    back. The next `save_config` is what stores the resolved form."""
    config_path = tmp_path / "config.toml"
    original = 'user_name = "Nico"\nroot = "notebooks"\n'
    config_path.write_text(original, encoding="utf-8")
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)

    load_config()

    assert config_path.read_text(encoding="utf-8") == original


def test_an_absolute_root_is_left_exactly_as_stored(tmp_path, monkeypatch):
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f'user_name = "Nico"\nroot = "{tmp_path / "Vimdiomas"}"\n', encoding="utf-8"
    )
    monkeypatch.setattr("vimdiomas.config.CONFIG_PATH", config_path)
    assert load_config().root == tmp_path / "Vimdiomas"


# --- Sprint 7 M6: migrating an install from before the rename ---------------


def test_migration_moves_config_and_cache(tmp_path):
    (tmp_path / ".config" / "idiomas").mkdir(parents=True)
    (tmp_path / ".config" / "idiomas" / "config.toml").write_text("x = 1\n")
    (tmp_path / ".config" / "idiomas" / "config.toml.bak").write_text("old\n")
    (tmp_path / ".cache" / "idiomas").mkdir(parents=True)
    (tmp_path / ".cache" / "idiomas" / "compile_cache.json").write_text("{}")

    migrate_legacy_paths(home=tmp_path, bin_dir=tmp_path / "bin")

    assert (tmp_path / ".config" / "vimdiomas" / "config.toml").read_text() == "x = 1\n"
    assert (tmp_path / ".config" / "vimdiomas" / "config.toml.bak").exists()
    assert not (tmp_path / ".config" / "idiomas").exists()
    assert (tmp_path / ".cache" / "vimdiomas" / "compile_cache.json").exists()
    assert not (tmp_path / ".cache" / "idiomas").exists()


def test_migration_never_overwrites_a_new_config(tmp_path):
    (tmp_path / ".config" / "idiomas").mkdir(parents=True)
    (tmp_path / ".config" / "idiomas" / "config.toml").write_text("old\n")
    (tmp_path / ".config" / "vimdiomas").mkdir(parents=True)
    (tmp_path / ".config" / "vimdiomas" / "config.toml").write_text("new\n")

    migrate_legacy_paths(home=tmp_path, bin_dir=tmp_path / "bin")

    assert (tmp_path / ".config" / "vimdiomas" / "config.toml").read_text() == "new\n"
    assert (tmp_path / ".config" / "idiomas" / "config.toml").read_text() == "old\n"


def test_migration_is_a_no_op_on_a_fresh_machine(tmp_path):
    migrate_legacy_paths(home=tmp_path, bin_dir=tmp_path / "bin")

    assert list(tmp_path.iterdir()) == []


def test_migration_removes_only_a_dangling_idiomas_link(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "idiomas").symlink_to(tmp_path / "venv" / "bin" / "idiomas")

    migrate_legacy_paths(home=tmp_path, bin_dir=bin_dir)

    assert not (bin_dir / "idiomas").is_symlink()


def test_migration_keeps_a_working_link_and_a_plain_file(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    target = tmp_path / "venv" / "bin" / "idiomas"
    target.parent.mkdir(parents=True)
    target.write_text("#!/bin/sh\n")
    (bin_dir / "idiomas").symlink_to(target)

    migrate_legacy_paths(home=tmp_path, bin_dir=bin_dir)
    assert (bin_dir / "idiomas").is_symlink()

    (bin_dir / "idiomas").unlink()
    (bin_dir / "idiomas").write_text("someone else's script\n")
    migrate_legacy_paths(home=tmp_path, bin_dir=bin_dir)
    assert (bin_dir / "idiomas").read_text() == "someone else's script\n"


def test_migration_swallows_os_errors(tmp_path, monkeypatch):
    (tmp_path / ".config" / "idiomas").mkdir(parents=True)

    def fail(*_args):
        raise OSError("disk on fire")

    monkeypatch.setattr("vimdiomas.config.os.replace", fail)
    migrate_legacy_paths(home=tmp_path, bin_dir=tmp_path / "bin")

    assert (tmp_path / ".config" / "idiomas").is_dir()


def test_main_migrates_before_loading_the_config(monkeypatch):
    from vimdiomas import __main__ as main_module

    calls = []
    monkeypatch.setattr(main_module, "migrate_legacy_paths", lambda: calls.append("migrate"))
    monkeypatch.setattr(main_module, "_tui", lambda: calls.append("tui"))
    monkeypatch.setattr("sys.argv", ["vimdiomas"])

    main_module.main()

    assert calls == ["migrate", "tui"]
