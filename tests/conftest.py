import pytest

from vimdiomas import compile as compile_module


@pytest.fixture(autouse=True)
def _isolated_compile_cache(tmp_path):
    """Every test gets its own compile cache, never the dev's real one: since
    Sprint 6 M3 (#11) every compile records its stamp, including the
    autocompiles the TUI tests trigger.

    Set and restored by hand rather than through `monkeypatch`: requesting
    `monkeypatch` here would set it up before every test's own fixtures and
    so undo their patches only after their teardown has run."""
    original = compile_module.CACHE_PATH
    compile_module.CACHE_PATH = tmp_path / "cache" / "compile_cache.json"
    yield
    compile_module.CACHE_PATH = original


@pytest.fixture(autouse=True)
def _no_legacy_migration():
    """`main()` migrates the pre-rename paths under the real home folder
    (Sprint 7 M6); a test that calls it must never move the dev's config."""
    from vimdiomas import cli as main_module

    original = main_module.migrate_legacy_paths
    main_module.migrate_legacy_paths = lambda: None
    yield
    main_module.migrate_legacy_paths = original


@pytest.fixture(autouse=True)
def _no_path_extension():
    """`main()` extends the process's `PATH` with the package manager's
    directories (Sprint 8 M3); a test that calls it must not change the real
    environment for the tests after it."""
    from vimdiomas import cli as main_module

    original = main_module.extend_path
    main_module.extend_path = lambda: None
    yield
    main_module.extend_path = original
