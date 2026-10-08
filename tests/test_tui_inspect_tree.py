from pathlib import Path

import pytest
from textual.app import App

from vimdiomas.languages import CHARACTER_PHONETIC
from vimdiomas.tui.screens.inspect import InspectTree, InspectTreeScreen
from vimdiomas.tui.screens.panels import Panel


class _HostApp(App):
    def __init__(self, tree_root: Path) -> None:
        super().__init__()
        self._tree_root = tree_root

    def on_mount(self) -> None:
        self.push_screen(InspectTreeScreen(self._tree_root, kind=CHARACTER_PHONETIC))


def _find_all(node, kind):
    results = []
    if node.data is not None and node.data.kind == kind:
        results.append(node)
    for child in node.children:
        results.extend(_find_all(child, kind))
    return results


@pytest.fixture
def source_tree(tmp_path):
    vocab = tmp_path / "Vocabulary"
    vocab.mkdir()
    (vocab / "Food.md").write_text(
        "# Food\n\n苹果\tping2guo3\tapple\n", encoding="utf-8"
    )
    (vocab / "Food.pdf").write_bytes(b"%PDF-fake")
    (vocab / "NoPdf.md").write_text("# NoPdf\n\n字\tzi4\tcharacter\n", encoding="utf-8")
    return tmp_path


async def test_tree_structure(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        files = _find_all(tree.root, "file")
        labels = sorted(str(n.label) for n in files)
        assert labels == ["Food", "NoPdf"]


async def test_starts_in_pdf_mode(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        assert pilot.app.screen.mode == "pdf"


async def test_tab_toggles_mode(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.screen.mode == "md"
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.screen.mode == "pdf"


async def test_tree_border_class_reflects_mode(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert tree.has_class("mode-pdf")
        assert not tree.has_class("mode-md")

        await pilot.press("tab")
        await pilot.pause()
        assert tree.has_class("mode-md")
        assert not tree.has_class("mode-pdf")

        await pilot.press("tab")
        await pilot.pause()
        assert tree.has_class("mode-pdf")
        assert not tree.has_class("mode-md")


async def test_mode_badge_reflects_mode(source_tree):
    from textual.widgets import Static

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        badge = pilot.app.screen.query_one("#mode-badge", Static)
        assert badge.has_class("mode-pdf")
        assert not badge.has_class("mode-md")
        assert str(badge.render()) == "PDF MODE"

        await pilot.press("tab")
        await pilot.pause()
        assert badge.has_class("mode-md")
        assert not badge.has_class("mode-pdf")
        assert str(badge.render()) == "MD MODE"

        await pilot.press("tab")
        await pilot.pause()
        assert badge.has_class("mode-pdf")
        assert str(badge.render()) == "PDF MODE"


async def test_fresh_screen_always_starts_in_pdf_mode(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.screen.mode == "md"

        pilot.app.pop_screen()
        await pilot.pause()
        pilot.app.push_screen(InspectTreeScreen(source_tree, kind=CHARACTER_PHONETIC))
        await pilot.pause()
        assert pilot.app.screen.mode == "pdf"


async def test_enter_in_pdf_mode_opens_existing_pdf(source_tree, monkeypatch):
    # _open_pdf moved into the shared `open_source_pdf` (M3, requirements.md
    # §3.6), which lives in base.py alongside the other shared compile
    # utilities (autocompile_one) -- so that's where compile_file/open_file
    # are resolved from now, not inspect.py.
    calls = []
    monkeypatch.setattr("vimdiomas.tui.screens.base.open_file", calls.append)
    compile_calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: compile_calls.append((src, dst)),
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        food = next(n for n in _find_all(tree.root, "file") if str(n.label) == "Food")
        tree.move_cursor(food)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert compile_calls == []
        assert calls == [source_tree / "Vocabulary" / "Food.pdf"]


async def test_enter_in_pdf_mode_compiles_missing_pdf_first(source_tree, monkeypatch):
    calls = []
    monkeypatch.setattr("vimdiomas.tui.screens.base.open_file", calls.append)
    compile_calls = []

    def _fake_compile(src, dst, **kwargs):
        compile_calls.append((src, dst))
        dst.write_bytes(b"%PDF-fake")

    monkeypatch.setattr("vimdiomas.tui.screens.base.compile_file", _fake_compile)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        no_pdf = next(n for n in _find_all(tree.root, "file") if str(n.label) == "NoPdf")
        tree.move_cursor(no_pdf)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        md_path = source_tree / "Vocabulary" / "NoPdf.md"
        pdf_path = source_tree / "Vocabulary" / "NoPdf.pdf"
        assert compile_calls == [(md_path, pdf_path)]
        assert calls == [pdf_path]


async def test_enter_in_md_mode_suspends_and_runs_nvim(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.shutil.which", lambda name: "/bin/nvim")
    run_calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.inspect.subprocess.run", lambda args: run_calls.append(args)
    )

    class _FakeSuspend:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    suspend_calls = []

    def _fake_suspend():
        suspend_calls.append(1)
        return _FakeSuspend()

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        monkeypatch.setattr(pilot.app, "suspend", _fake_suspend)
        await pilot.press("tab")
        await pilot.pause()

        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        food = next(n for n in _find_all(tree.root, "file") if str(n.label) == "Food")
        tree.move_cursor(food)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert suspend_calls == [1]
        assert run_calls == [
            ["nvim", "-c", "set noexpandtab", str(source_tree / "Vocabulary" / "Food.md")]
        ]


async def test_md_mode_recompiles_when_file_changed(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.shutil.which", lambda name: "/bin/nvim")
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda args: None)

    class _FakeSuspend:
        def __enter__(self):
            md_path = source_tree / "Vocabulary" / "Food.md"
            # Simulate vim editing+saving the file while the app is suspended.
            md_path.write_text(md_path.read_text(encoding="utf-8") + "\nchanged\n", encoding="utf-8")
            return self

        def __exit__(self, *exc_info):
            return False

    compile_calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: compile_calls.append((src, dst)),
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        monkeypatch.setattr(pilot.app, "suspend", lambda: _FakeSuspend())
        await pilot.press("tab")
        await pilot.pause()

        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        food = next(n for n in _find_all(tree.root, "file") if str(n.label) == "Food")
        tree.move_cursor(food)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        md_path = source_tree / "Vocabulary" / "Food.md"
        pdf_path = source_tree / "Vocabulary" / "Food.pdf"
        assert compile_calls == [(md_path, pdf_path)]


async def test_md_mode_does_not_recompile_when_unchanged(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.shutil.which", lambda name: "/bin/nvim")
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda args: None)

    class _FakeSuspend:
        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    compile_calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: compile_calls.append((src, dst)),
    )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        monkeypatch.setattr(pilot.app, "suspend", lambda: _FakeSuspend())
        await pilot.press("tab")
        await pilot.pause()

        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        food = next(n for n in _find_all(tree.root, "file") if str(n.label) == "Food")
        tree.move_cursor(food)
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert compile_calls == []


async def test_q_from_inspect_tree_pops_the_screen(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.focus()
        await pilot.pause()
        screens_before = len(pilot.app.screen_stack)
        await pilot.press("q")
        await pilot.pause()
        assert len(pilot.app.screen_stack) == screens_before - 1


async def test_q_clears_any_kitty_image_before_leaving(source_tree):
    # A kitty image sits in its own layer above the text grid, outside
    # Textual's own repaint, so leaving the screen without an explicit
    # delete would leave it visibly covering the menu underneath.
    from vimdiomas.tui.screens.inspect import InspectTreeScreen

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        assert isinstance(screen, InspectTreeScreen)
        writes = []
        monkeypatch_write = pilot.app._driver.write
        pilot.app._driver.write = lambda data: (writes.append(data), monkeypatch_write(data))[0]

        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.focus()
        await pilot.pause()
        await pilot.press("q")
        await pilot.pause()

        assert any("\x1b_Ga=d;" in write for write in writes)


async def test_opening_focuses_the_tree(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert pilot.app.focused is tree


async def test_escape_climbs_panel_then_backpanel(source_tree):
    # M4 gives Inspect Tree a second panel, so unlike Sprint 4's one-panel
    # behaviour, a second escape now reaches the backpanel (design.md's
    # standing rule for any screen with more than one panel).
    from vimdiomas.tui.screens.panels import Backpanel

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert pilot.app.focused is tree

        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#inspect-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("escape")
        await pilot.pause()
        backpanel = pilot.app.screen.query_one(Backpanel)
        assert pilot.app.focused is backpanel


async def test_shift_arrows_on_tree_do_not_move_the_cursor(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.focus()
        await pilot.pause()
        line_before = tree.cursor_line

        for key in ("shift+left", "shift+right", "shift+up", "shift+down", "H", "L"):
            await pilot.press(key)
            await pilot.pause()
            assert tree.cursor_line == line_before
            assert pilot.app.focused is tree


async def test_tab_from_panel_focuses_the_tree(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()
        panel = pilot.app.screen.query_one("#inspect-panel", Panel)
        assert pilot.app.focused is panel

        await pilot.press("tab")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert pilot.app.focused is tree
        # tab on the panel focuses the tree, not a mode toggle.
        assert pilot.app.screen.mode == "pdf"


async def test_jk_move_tree_cursor(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.focus()
        await pilot.pause()
        line_before = tree.cursor_line
        await pilot.press("j")
        await pilot.pause()
        assert tree.cursor_line == line_before + 1
        await pilot.press("k")
        await pilot.pause()
        assert tree.cursor_line == line_before


def _select(tree, label, kind="file"):
    node = next(n for n in _find_all(tree.root, kind) if str(n.label) == label)
    tree.move_cursor(node)
    return node


async def test_delete_file_confirmed_hides_it_but_keeps_it_on_disk(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        labels = [str(n.label) for n in _find_all(tree.root, "file")]
        assert "Food" not in labels
        assert (source_tree / "Vocabulary" / "Food.md").exists()
        assert (source_tree / "Vocabulary" / "Food.pdf").exists()


async def test_delete_confirmed_then_leaving_the_screen_commits_it(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        pilot.app.pop_screen()
        await pilot.pause()

        assert not (source_tree / "Vocabulary" / "Food.md").exists()
        assert not (source_tree / "Vocabulary" / "Food.pdf").exists()


async def test_delete_file_cancelled_keeps_files(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()

        labels = [str(n.label) for n in _find_all(tree.root, "file")]
        assert "Food" in labels
        assert (source_tree / "Vocabulary" / "Food.md").exists()
        assert (source_tree / "Vocabulary" / "Food.pdf").exists()


async def test_confirm_dialog_enter_does_nothing(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()

        from vimdiomas.tui.screens.base import ConfirmDialog

        assert isinstance(pilot.app.screen, ConfirmDialog)
        await pilot.press("enter")
        await pilot.pause()

        assert isinstance(pilot.app.screen, ConfirmDialog)
        labels = [str(n.label) for n in _find_all(tree.root, "file")]
        assert "Food" in labels
        await pilot.press("n")


async def test_undo_restores_a_pending_delete(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        labels = [str(n.label) for n in _find_all(tree.root, "file")]
        assert "Food" not in labels

        await pilot.press("u")
        await pilot.pause()

        labels = [str(n.label) for n in _find_all(tree.root, "file")]
        assert "Food" in labels

        pilot.app.pop_screen()
        await pilot.pause()
        assert (source_tree / "Vocabulary" / "Food.md").exists()
        assert (source_tree / "Vocabulary" / "Food.pdf").exists()


async def test_undo_with_nothing_pending_notifies(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.focus()
        await pilot.pause()
        await pilot.press("u")
        await pilot.pause()
        # No crash, nothing removed.
        assert (source_tree / "Vocabulary" / "Food.md").exists()


async def test_delete_nonempty_directory_confirmed_hides_everything(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()
        await pilot.press("y")
        await pilot.pause()

        assert list(tree.root.children) == []
        assert (source_tree / "Vocabulary").exists()

        pilot.app.pop_screen()
        await pilot.pause()
        assert not (source_tree / "Vocabulary").exists()


async def test_delete_directory_confirmation_names_file_count(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("d")
        await pilot.pause()

        from vimdiomas.tui.screens.base import ConfirmDialog

        dialog = pilot.app.screen
        assert isinstance(dialog, ConfirmDialog)
        assert "2" in dialog.message
        await pilot.press("n")


async def test_delete_on_root_is_a_noop(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.move_cursor(tree.root)
        await pilot.pause()
        screens_before = len(pilot.app.screen_stack)
        await pilot.press("d")
        await pilot.pause()

        assert len(pilot.app.screen_stack) == screens_before
        assert (source_tree / "Vocabulary").exists()


async def test_rename_file_with_pdf_renames_both_and_recompiles(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda *a, **kw: None)
    # This monkeypatch replaces the shared subprocess module's run(), which
    # the PDF preview's extract_text also calls when the cursor lands back
    # on a file after the rename — irrelevant to what this test checks.
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.extract_text", lambda pdf_path: "")
    compile_calls = []

    def _fake_compile(src, dst, **kwargs):
        compile_calls.append((src, dst))
        dst.write_bytes(b"%PDF-fake")

    monkeypatch.setattr("vimdiomas.tui.screens.base.compile_file", _fake_compile)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        for char in "Fruit":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert not (source_tree / "Vocabulary" / "Food.md").exists()
        assert not (source_tree / "Vocabulary" / "Food.pdf").exists()
        new_md = source_tree / "Vocabulary" / "Fruit.md"
        new_pdf = source_tree / "Vocabulary" / "Fruit.pdf"
        assert new_md.exists()
        assert new_pdf.exists()
        assert compile_calls == [(new_md, new_pdf)]


async def test_rename_updates_the_md_header(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        for char in "Renamed":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        content = (source_tree / "Vocabulary" / "Renamed.md").read_text(encoding="utf-8")
        assert content.startswith("# Renamed\n")


async def test_rename_file_without_pdf_only_renames_md(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        for char in "Renamed":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert not (source_tree / "Vocabulary" / "NoPdf.md").exists()
        assert (source_tree / "Vocabulary" / "Renamed.md").exists()
        assert not (source_tree / "Vocabulary" / "Renamed.pdf").exists()


async def test_rename_directory(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        for char in "Words":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert not (source_tree / "Vocabulary").exists()
        assert (source_tree / "Words" / "Food.md").exists()


async def test_rename_empty_submission_cancels(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert (source_tree / "Vocabulary" / "Food.md").exists()


async def test_rename_on_root_is_a_noop(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        tree.move_cursor(tree.root)
        await pilot.pause()
        screens_before = len(pilot.app.screen_stack)
        await pilot.press("r")
        await pilot.pause()

        assert len(pilot.app.screen_stack) == screens_before


async def test_rename_refuses_duplicate_name(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await pilot.press("r")
        await pilot.pause()
        for char in "Food":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert (source_tree / "Vocabulary" / "NoPdf.md").exists()
        assert (source_tree / "Vocabulary" / "Food.md").exists()


async def test_new_dir_targets_root_regardless_of_cursor(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("n")
        await pilot.pause()
        for char in "Grammar":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert (source_tree / "Grammar").is_dir()


async def test_new_dir_empty_submission_cancels(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        await pilot.press("n")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert list(source_tree.iterdir()) == [source_tree / "Vocabulary"]


async def test_new_dir_refuses_duplicate_name(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("n")
        await pilot.pause()
        for char in "Vocabulary":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert len(list(source_tree.iterdir())) == 1


async def test_new_file_in_cursor_directory(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda *a, **kw: None)
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        for char in "Drinks":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        new_md = source_tree / "Vocabulary" / "Drinks.md"
        assert new_md.read_text(encoding="utf-8") == "# Drinks\n"


async def test_new_file_in_selected_files_directory(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda *a, **kw: None)
    # See the same note in test_rename_file_with_pdf_renames_both_and_recompiles:
    # the cursor lands back on "Food" (which has a real PDF), so the preview
    # would otherwise call the now-monkeypatched subprocess.run itself.
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.extract_text", lambda pdf_path: "")
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        for char in "Drinks":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        assert (source_tree / "Vocabulary" / "Drinks.md").exists()


async def test_new_file_compiles_immediately(source_tree, monkeypatch):
    compile_calls = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file",
        lambda src, dst, **kwargs: compile_calls.append((src, dst)),
    )
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        for char in "Drinks":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()

        new_md = source_tree / "Vocabulary" / "Drinks.md"
        new_pdf = source_tree / "Vocabulary" / "Drinks.pdf"
        assert compile_calls == [(new_md, new_pdf)]


async def test_new_file_empty_submission_cancels(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert sorted(p.name for p in (source_tree / "Vocabulary").iterdir()) == [
            "Food.md",
            "Food.pdf",
            "NoPdf.md",
        ]


async def test_new_file_refuses_duplicate_name(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda args: None)
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await pilot.press("m")
        await pilot.pause()
        for char in "Food":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert (source_tree / "Vocabulary" / "Food.md").read_text(encoding="utf-8").startswith(
            "# Food\n\n苹果"
        )


async def test_all_edit_keys_work_in_md_mode(source_tree):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.screen.mode == "md"

        await pilot.press("n")
        await pilot.pause()
        for char in "Grammar":
            await pilot.press(char)
        await pilot.press("enter")
        await pilot.pause()

        assert (source_tree / "Grammar").is_dir()


# -- Sprint 6 M1 · #1: a pending delete can't survive a rename -------------


async def _rename(pilot, name):
    await pilot.press("r")
    await pilot.pause()
    for char in name:
        await pilot.press(char)
    await pilot.press("enter")
    await pilot.pause()


async def _delete(pilot):
    await pilot.press("d")
    await pilot.pause()
    await pilot.press("y")
    await pilot.pause()


@pytest.fixture
def nested_tree(tmp_path):
    old = tmp_path / "Old"
    old.mkdir()
    (old / "DeleteMe.md").write_text("# DeleteMe\n\n原文\tyuan2wen2\toriginal\n", encoding="utf-8")
    (old / "Keep.md").write_text("# Keep\n\n留\tliu2\tkeep\n", encoding="utf-8")
    return tmp_path


async def test_renaming_the_parent_does_not_undelete_the_file(nested_tree):
    """The report's P1 reproduction, first half: the rename un-deleted the
    file in the tree, because `_prune` hid it by a path the rename had just
    invalidated."""
    app = _HostApp(nested_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "DeleteMe")
        await pilot.pause()
        await _delete(pilot)

        _select(tree, "Old", kind="dir")
        await pilot.pause()
        await _rename(pilot, "New")

        assert [str(n.label) for n in _find_all(tree.root, "file")] == ["Keep"]


async def test_the_marked_file_is_the_one_that_goes_after_a_rename(nested_tree):
    """The report's P1 reproduction, dangerous half: the pending path still
    pointed at `Old/DeleteMe.md`, so on leaving the screen the app deleted
    whatever had since been created there and left the marked file in place."""
    app = _HostApp(nested_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "DeleteMe")
        await pilot.pause()
        await _delete(pilot)

        _select(tree, "Old", kind="dir")
        await pilot.pause()
        await _rename(pilot, "New")

        # a different file re-created at the path the deletion was marked at
        (nested_tree / "Old").mkdir()
        (nested_tree / "Old" / "DeleteMe.md").write_text(
            "# DeleteMe\n\n新文\txin1wen2\tnew\n", encoding="utf-8"
        )

        pilot.app.pop_screen()
        await pilot.pause()

        assert not (nested_tree / "New" / "DeleteMe.md").exists()
        assert (nested_tree / "New" / "Keep.md").exists()
        assert (nested_tree / "Old" / "DeleteMe.md").read_text(encoding="utf-8") == (
            "# DeleteMe\n\n新文\txin1wen2\tnew\n"
        )


async def test_renaming_an_ancestor_two_levels_up_remaps_the_pending_path(tmp_path):
    top = tmp_path / "Top"
    (top / "Mid").mkdir(parents=True)
    (top / "Mid" / "Gone.md").write_text("# Gone\n\n走\tzou3\tgone\n", encoding="utf-8")

    app = _HostApp(tmp_path)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Gone")
        await pilot.pause()
        await _delete(pilot)

        _select(tree, "Top", kind="dir")
        await pilot.pause()
        await _rename(pilot, "Renamed")

        pilot.app.pop_screen()
        await pilot.pause()

        assert (tmp_path / "Renamed" / "Mid").is_dir()
        assert not (tmp_path / "Renamed" / "Mid" / "Gone.md").exists()


async def test_deleting_a_directory_under_a_renamed_parent_removes_it(tmp_path):
    (tmp_path / "Parent" / "Doomed").mkdir(parents=True)
    (tmp_path / "Parent" / "Doomed" / "X.md").write_text("# X\n", encoding="utf-8")
    (tmp_path / "Parent" / "Keep.md").write_text("# Keep\n", encoding="utf-8")

    app = _HostApp(tmp_path)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Doomed", kind="dir")
        await pilot.pause()
        await _delete(pilot)

        _select(tree, "Parent", kind="dir")
        await pilot.pause()
        await _rename(pilot, "Renamed")

        pilot.app.pop_screen()
        await pilot.pause()

        assert not (tmp_path / "Renamed" / "Doomed").exists()
        assert (tmp_path / "Renamed" / "Keep.md").exists()


async def test_a_replaced_file_is_left_alone_and_the_user_is_told(source_tree, monkeypatch):
    """The identity check on its own: a path re-created between marking and
    committing holds a different file, and not deleting is always the
    recoverable direction."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await _delete(pilot)

        path = source_tree / "Vocabulary" / "NoPdf.md"
        path.unlink()
        path.write_text("# NoPdf\n\n替\tti4\treplacement\n", encoding="utf-8")

        notifications = []
        monkeypatch.setattr(
            pilot.app, "notify", lambda *a, **k: notifications.append((a, k))
        )

        pilot.app.pop_screen()
        await pilot.pause()

        assert path.read_text(encoding="utf-8") == "# NoPdf\n\n替\tti4\treplacement\n"
        warnings = [a[0] for a, k in notifications if k.get("severity") == "warning"]
        assert warnings == ["NoPdf.md changed since it was deleted — left alone."]


async def test_a_file_deleted_externally_is_dropped_silently(source_tree, monkeypatch):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await _delete(pilot)

        (source_tree / "Vocabulary" / "NoPdf.md").unlink()

        notifications = []
        monkeypatch.setattr(
            pilot.app, "notify", lambda *a, **k: notifications.append((a, k))
        )

        pilot.app.pop_screen()
        await pilot.pause()

        assert notifications == []


async def test_undo_after_a_rename_leaves_everything_in_place(nested_tree):
    """`u` pops the pending list; remapping keeps that list correct rather
    than changing how it is consumed."""
    app = _HostApp(nested_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "DeleteMe")
        await pilot.pause()
        await _delete(pilot)

        _select(tree, "Old", kind="dir")
        await pilot.pause()
        await _rename(pilot, "New")

        await pilot.press("u")
        await pilot.pause()
        assert sorted(str(n.label) for n in _find_all(tree.root, "file")) == [
            "DeleteMe",
            "Keep",
        ]

        pilot.app.pop_screen()
        await pilot.pause()
        assert (nested_tree / "New" / "DeleteMe.md").exists()
        assert (nested_tree / "New" / "Keep.md").exists()


async def test_renaming_the_deleted_file_itself_remaps_the_pending_path(source_tree):
    """A pending delete is hidden from the tree, so the cursor can't reach it
    — but the file branch remaps an exact match anyway, so the rule holds
    however the path came to move."""
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        screen = pilot.app.screen
        tree = screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await _delete(pilot)

        old = source_tree / "Vocabulary" / "NoPdf.md"
        new = source_tree / "Vocabulary" / "Renamed.md"
        old.rename(new)
        screen._remap_pending_deletes(old, new)

        pilot.app.pop_screen()
        await pilot.pause()

        assert not new.exists()


# -- Sprint 6 M2 · #16: bracket text is text, not markup -------------------


@pytest.fixture
def bracket_tree(tmp_path):
    vocab = tmp_path / "Words [i]"
    vocab.mkdir()
    (vocab / "[b]x.md").write_text(
        "# [b]x\n\n测试\tce4shi4\tto [/] test\n", encoding="utf-8"
    )
    (vocab / "trail\\.md").write_text("# trail\\\n\n字\tzi4\tchar\n", encoding="utf-8")
    return tmp_path


def _preview_text(screen) -> str:
    from textual.widgets import Static

    # `render()`, not `.content`: a `str` is stored as given and only parsed
    # as markup when it is drawn.
    return str(screen.query_one("#preview-message", Static).render())


async def test_bracket_names_are_listed_literally(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        files = sorted(str(n.label) for n in _find_all(tree.root, "file"))
        dirs = [str(n.label) for n in _find_all(tree.root, "dir") if n is not tree.root]
        assert files == ["[b]x", "trail\\"]
        assert dirs == ["Words [i]"]


async def test_md_mode_previews_bracket_content_literally(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "[b]x")
        await pilot.pause()
        await pilot.press("tab")
        await pilot.pause()
        assert pilot.app.is_running
        assert "to [/] test" in _preview_text(pilot.app.screen)
        assert "# [b]x" in _preview_text(pilot.app.screen)


async def test_pdftotext_fallback_previews_bracket_text_literally(bracket_tree, monkeypatch):
    pdf = bracket_tree / "Words [i]" / "[b]x.pdf"
    pdf.write_bytes(b"%PDF-fake")
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.pdftoppm_available", lambda: True)
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.supports_kitty_graphics", lambda: False)
    monkeypatch.setattr(
        "vimdiomas.tui.screens.inspect.extract_text", lambda path: "to [/] test [b]x"
    )
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "[b]x")
        await pilot.pause()
        await pilot.app.workers.wait_for_complete()
        await pilot.pause()
        assert pilot.app.is_running
        assert _preview_text(pilot.app.screen) == "to [/] test [b]x"


async def test_notification_naming_a_bracket_file_does_not_raise(bracket_tree):
    app = _HostApp(bracket_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "[b]x")
        await pilot.pause()
        await _delete(pilot)
        assert pilot.app.is_running
        messages = [n.message for n in pilot.app._notifications]
        assert "Deleted [b]x.md. Press u to undo." in messages


# -- Sprint 6 M2 · #12: a failed compile on Enter is reported --------------


async def test_enter_on_a_file_that_fails_to_compile_notifies_and_opens_nothing(
    source_tree, monkeypatch
):
    import subprocess

    opened = []
    monkeypatch.setattr("vimdiomas.tui.screens.base.open_file", opened.append)

    def _failing(src, dst, **kwargs):
        raise subprocess.CalledProcessError(
            43, ["pandoc"], stderr=b"! Undefined control sequence.\n"
        )

    monkeypatch.setattr("vimdiomas.tui.screens.base.compile_file", _failing)

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "NoPdf")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()

        assert pilot.app.is_running
        assert opened == []
        [note] = [n for n in pilot.app._notifications if n.severity == "error"]
        assert "NoPdf.md" in note.message
        assert "Undefined control sequence" in note.message
        assert isinstance(pilot.app.screen, InspectTreeScreen)


# -- Sprint 6 M2 · #14: a name prompt cannot write outside the tree --------


def _snapshot(root: Path) -> dict[str, bytes | None]:
    """Every path under (and beside) `root`, with each file's bytes: a refused
    name must change none of it. The tree's parent is included because `..`
    is exactly how a name escapes the tree."""
    base = root.parent
    return {
        str(path.relative_to(base)): path.read_bytes() if path.is_file() else None
        for path in sorted(base.rglob("*"))
    }


async def _prompt(pilot, key, text):
    await pilot.press(key)
    await pilot.pause()
    pilot.app.screen.query_one("#dialog-input").value = text
    await pilot.press("enter")
    await pilot.pause()


@pytest.fixture
def contained_tree(tmp_path):
    root = tmp_path / "tree-Chinese"
    vocab = root / "Vocabulary"
    vocab.mkdir(parents=True)
    (vocab / "food.md").write_text("# food\n\n字\tzi4\tchar\n", encoding="utf-8")
    (vocab / "sub").mkdir()
    return root


REFUSED = ["/", "..", "../x", "sub/food2", "a/b", "x ", " x", "."]


@pytest.mark.parametrize("text", REFUSED)
@pytest.mark.parametrize(
    "key,target",
    [("r", "food"), ("r", "Vocabulary"), ("m", "food"), ("n", "food")],
)
async def test_a_refused_name_changes_nothing_and_says_so(contained_tree, key, target, text):
    before = _snapshot(contained_tree)
    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, target, kind="dir" if target == "Vocabulary" else "file")
        await pilot.pause()
        await _prompt(pilot, key, text)
        await pilot.app.workers.wait_for_complete()

        assert pilot.app.is_running
        assert any(n.severity == "error" for n in pilot.app._notifications)
    assert _snapshot(contained_tree) == before


async def test_rename_to_a_nested_path_keeps_the_original_header(contained_tree):
    """The report's own reproduction: today the header is rewritten to
    `# sub/food2` before the rename fails."""
    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "food")
        await pilot.pause()
        await _prompt(pilot, "r", "sub/food2")
        assert pilot.app.is_running
    food = contained_tree / "Vocabulary" / "food.md"
    assert food.read_text(encoding="utf-8") == "# food\n\n字\tzi4\tchar\n"


async def test_a_rename_that_fails_at_the_syscall_leaves_the_header(contained_tree, monkeypatch):
    real_rename = Path.rename

    def _failing_rename(self, target):
        if self.name == "food.md":
            raise PermissionError(13, "Permission denied")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", _failing_rename)
    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "food")
        await pilot.pause()
        await _prompt(pilot, "r", "drinks")

        assert pilot.app.is_running
        assert any(n.severity == "error" for n in pilot.app._notifications)
    food = contained_tree / "Vocabulary" / "food.md"
    assert food.read_text(encoding="utf-8") == "# food\n\n字\tzi4\tchar\n"
    assert not (contained_tree / "Vocabulary" / "drinks.md").exists()


async def test_a_mkdir_that_fails_is_reported(contained_tree, monkeypatch):
    def _failing_mkdir(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "mkdir", _failing_mkdir)
    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        await _prompt(pilot, "n", "Grammar")
        assert pilot.app.is_running
        assert any(n.severity == "error" for n in pilot.app._notifications)


async def test_a_new_file_that_cannot_be_written_is_reported(contained_tree, monkeypatch):
    def _failing_write(self, *args, **kwargs):
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "write_text", _failing_write)
    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        await _prompt(pilot, "m", "drinks")
        assert pilot.app.is_running
        assert any(n.severity == "error" for n in pilot.app._notifications)


# -- Sprint 6 M2 · #9: a missing optional editor is a message --------------


async def _enter_in_md_mode_on_food(pilot):
    await pilot.press("tab")
    await pilot.pause()
    tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
    _select(tree, "Food")
    await pilot.pause()
    await pilot.press("enter")
    await pilot.pause()


async def test_md_enter_without_nvim_notifies_and_touches_nothing(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.shutil.which", lambda name: None)
    ran = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.inspect.subprocess.run", lambda *a, **kw: ran.append(a)
    )
    compiled = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file", lambda *a, **kw: compiled.append(a)
    )
    food = source_tree / "Vocabulary" / "Food.md"
    mtime_before = food.stat().st_mtime_ns
    bytes_before = food.read_bytes()

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        suspended = []
        monkeypatch.setattr(pilot.app, "suspend", lambda: suspended.append(1))
        await _enter_in_md_mode_on_food(pilot)
        await pilot.app.workers.wait_for_complete()

        assert pilot.app.is_running
        assert suspended == [] and ran == [] and compiled == []
        [note] = [n for n in pilot.app._notifications if n.severity == "warning"]
        assert note.message == "nvim isn't installed, so MD mode can't open files."
        # Still usable: the tree has focus and answers to the cursor keys.
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert pilot.app.focused is tree
        line = tree.cursor_line
        await pilot.press("k")
        await pilot.pause()
        assert tree.cursor_line != line

    assert food.stat().st_mtime_ns == mtime_before
    assert food.read_bytes() == bytes_before


async def test_md_enter_when_the_editor_fails_to_start_notifies(source_tree, monkeypatch):
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.shutil.which", lambda name: "/bin/nvim")

    def _missing(*args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "nvim")

    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", _missing)
    compiled = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file", lambda *a, **kw: compiled.append(a)
    )

    class _Suspend:
        exited = False

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            _Suspend.exited = True
            return False

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        monkeypatch.setattr(pilot.app, "suspend", _Suspend)
        await _enter_in_md_mode_on_food(pilot)
        await pilot.app.workers.wait_for_complete()

        assert pilot.app.is_running
        assert _Suspend.exited  # the TUI came back
        assert compiled == []
        assert any(n.severity == "error" for n in pilot.app._notifications)


# -- Sprint 6 M3 · #17: case-only renames ----------------------------------


def _case_insensitive(directory: Path) -> bool:
    probe = directory / "CaseProbe"
    probe.touch()
    try:
        return (directory / "caseprobe").exists()
    finally:
        probe.unlink()


def test_the_source_itself_is_not_a_collision(tmp_path):
    from vimdiomas.tui.screens.inspect import is_taken

    source = tmp_path / "food.md"
    source.write_text("x", encoding="utf-8")
    assert not is_taken(source, source)
    assert not is_taken(tmp_path / "missing.md", source)


def test_a_different_file_is_a_collision(tmp_path):
    from vimdiomas.tui.screens.inspect import is_taken

    source = tmp_path / "food.md"
    other = tmp_path / "drinks.md"
    source.write_text("x", encoding="utf-8")
    other.write_text("y", encoding="utf-8")
    assert is_taken(other, source)


def test_a_failed_second_step_puts_the_original_name_back(tmp_path, monkeypatch):
    from vimdiomas.tui.screens import inspect as inspect_module

    source = tmp_path / "food.md"
    source.write_text("x", encoding="utf-8")
    real_rename = Path.rename

    def _rename(self, target):
        if Path(target).name == "Food.md":
            raise PermissionError(13, "Permission denied")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", _rename)
    # Pretend the target is the source under another spelling, whatever the
    # filesystem, so the two-step path is the one taken.
    monkeypatch.setattr(Path, "exists", lambda self: True)
    with pytest.raises(PermissionError):
        inspect_module.move(source, tmp_path / "Food.md")
    monkeypatch.undo()

    assert [p.name for p in tmp_path.iterdir()] == ["food.md"]


async def test_case_only_rename_of_a_file(contained_tree, monkeypatch):
    if not _case_insensitive(contained_tree):
        pytest.skip("case-only renames collide only on a case-insensitive filesystem")
    compiled = []
    monkeypatch.setattr(
        "vimdiomas.tui.screens.base.compile_file", lambda *a, **kw: compiled.append(a)
    )
    vocab = contained_tree / "Vocabulary"
    (vocab / "food.pdf").write_bytes(b"%PDF-fake")

    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "food")
        await pilot.pause()
        await _prompt(pilot, "r", "Food")
        await pilot.app.workers.wait_for_complete()

        assert not any(n.severity == "error" for n in pilot.app._notifications)

    names = sorted(p.name for p in vocab.iterdir())
    assert "Food.md" in names and "food.md" not in names
    assert (vocab / "Food.md").read_text(encoding="utf-8").startswith("# Food\n")
    assert compiled == [(vocab / "Food.md", vocab / "Food.pdf")]


async def test_case_only_rename_of_a_directory(contained_tree):
    if not _case_insensitive(contained_tree):
        pytest.skip("case-only renames collide only on a case-insensitive filesystem")

    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        await _prompt(pilot, "r", "vocabulary")

        assert not any(n.severity == "error" for n in pilot.app._notifications)

    assert [p.name for p in contained_tree.iterdir()] == ["vocabulary"]
    assert (contained_tree / "vocabulary" / "food.md").exists()


async def test_renaming_to_the_same_name_changes_nothing(contained_tree):
    food = contained_tree / "Vocabulary" / "food.md"
    before = food.read_text(encoding="utf-8")

    app = _HostApp(contained_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "food")
        await pilot.pause()
        await _prompt(pilot, "r", "food")

        assert not pilot.app._notifications

    assert food.read_text(encoding="utf-8") == before


# -- Sprint 6 M9 · manual editing checks ------------------------------------
#
# A file holding anything the app would not have written is marked in the tree
# and its warnings are listed above the preview, in both modes. MD mode's exit
# is when the app reads a hand edit: it re-reads the file, rebuilds the tree
# and says how many warnings the file has (requirements.md §§4–5).


TABLE_LINE = "| word | gloss |"


def _warn_food(tree_root: Path) -> Path:
    """Put something outside the format into Food.md, by hand."""
    path = tree_root / "Vocabulary" / "Food.md"
    path.write_text(
        f"# Food\n\n## Fruits\n\n苹果\tping2guo3\tapple\n\n{TABLE_LINE}\n", encoding="utf-8"
    )
    return path


async def test_a_warned_file_is_marked_in_the_tree(source_tree):
    _warn_food(source_tree)
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        labels = sorted(str(n.label) for n in _find_all(tree.root, "file"))
        # The clean file is untouched; the marker is appended to the stem.
        assert labels == ["Food ⚠", "NoPdf"]


async def test_the_marker_never_mixes_with_the_file_name(source_tree):
    """The stem is the user's text and the marker is the app's, so a name
    holding markup is still shown as typed (M2, #16)."""
    (source_tree / "Vocabulary" / "[b]x.md").write_text(f"# [b]x\n\n{TABLE_LINE}\n", encoding="utf-8")
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert "[b]x ⚠" in [str(n.label) for n in _find_all(tree.root, "file")]


async def test_the_warnings_block_heads_the_preview_in_md_mode(source_tree):
    _warn_food(source_tree)
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food ⚠")
        await pilot.pause()

        block = pilot.app.screen.query_one("#preview-warnings")
        assert block.display is True
        text = str(block.render())
        assert "⚠ 1 warning" in text
        assert "line 7: unrecognized line" in text
        assert TABLE_LINE in text


async def test_the_warnings_block_is_hidden_in_pdf_mode(source_tree):
    """In PDF mode the block would displace the rendered page; the file keeps
    its marker, and toggling the mode shows or hides the block."""
    _warn_food(source_tree)
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food ⚠")
        await pilot.pause()
        block = pilot.app.screen.query_one("#preview-warnings")
        assert pilot.app.screen.mode == "pdf"
        assert block.display is False

        await pilot.press("tab")
        await pilot.pause()
        assert block.display is True

        await pilot.press("tab")
        await pilot.pause()
        assert block.display is False


async def test_no_block_for_a_clean_file_or_a_directory(source_tree):
    _warn_food(source_tree)
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        block = pilot.app.screen.query_one("#preview-warnings")

        _select(tree, "NoPdf")
        await pilot.pause()
        assert block.display is False

        _select(tree, "Vocabulary", kind="dir")
        await pilot.pause()
        assert block.display is False

        # And it comes back on returning to the warned file.
        _select(tree, "Food ⚠")
        await pilot.pause()
        assert block.display is True


async def test_the_block_caps_the_list_and_counts_the_rest(source_tree):
    prose = "\n".join(f"line {n} of prose" for n in range(1, 12))
    (source_tree / "Vocabulary" / "Food.md").write_text(f"# Food\n\n{prose}\n", encoding="utf-8")
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food ⚠")
        await pilot.pause()
        text = str(pilot.app.screen.query_one("#preview-warnings").render())
        assert "⚠ 11 warnings" in text
        assert "line 13:" not in text  # the eleventh warning's line
        assert "… and 1 more" in text


async def test_a_file_level_warning_is_shown_without_a_line_number(source_tree):
    """A missing header has no line to blame (requirements.md §2)."""
    (source_tree / "Vocabulary" / "Food.md").write_text("苹果\tping2guo3\tapple\n", encoding="utf-8")
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        await pilot.press("tab")
        await pilot.pause()
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food ⚠")
        await pilot.pause()
        text = str(pilot.app.screen.query_one("#preview-warnings").render())
        assert "no '# Food' header line" in text
        assert "line 0" not in text


def _fake_nvim(monkeypatch, pilot, edit):
    """Run `edit` in place of nvim, as a save from the editor."""
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.shutil.which", lambda name: "/bin/nvim")
    monkeypatch.setattr("vimdiomas.tui.screens.inspect.subprocess.run", lambda args: None)
    monkeypatch.setattr("vimdiomas.tui.screens.base.compile_file", lambda *a, **kw: None)

    class _FakeSuspend:
        def __enter__(self):
            edit()
            return self

        def __exit__(self, *exc_info):
            return False

    monkeypatch.setattr(pilot.app, "suspend", lambda: _FakeSuspend())


async def test_md_exit_picks_up_a_category_added_by_hand(source_tree, monkeypatch):
    """A non-trivial change: the TUI is rebuilt from the file, so the new
    category is what the app now holds (requirements.md §3)."""
    path = source_tree / "Vocabulary" / "Food.md"

    def _edit():
        path.write_text("# Food\n\n## Snacks\n\n苹果\tping2guo3\tapple\n", encoding="utf-8")

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        _fake_nvim(monkeypatch, pilot, _edit)
        await _enter_in_md_mode_on_food(pilot)
        await pilot.app.workers.wait_for_complete()

        from vimdiomas.store import walk

        node = next(
            f for f in walk(source_tree, kind=CHARACTER_PHONETIC).dirs[0].files
            if f.path == path
        )
        assert node.categories == ["Snacks"]
        assert node.warnings == []
        # No warning to report, so nothing is said.
        assert [n for n in pilot.app._notifications if n.severity == "warning"] == []
        # The cursor stayed on the file that was edited.
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert tree.cursor_node.data.path == path


async def test_md_exit_marks_the_file_and_says_how_many(source_tree, monkeypatch):
    path = source_tree / "Vocabulary" / "Food.md"

    def _edit():
        path.write_text(
            f"# Food\n\n苹果\tping2guo3\tapple\n{TABLE_LINE}\n| --- | --- |\n", encoding="utf-8"
        )

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        _fake_nvim(monkeypatch, pilot, _edit)
        await _enter_in_md_mode_on_food(pilot)
        await pilot.app.workers.wait_for_complete()

        await pilot.pause()
        [note] = [n for n in pilot.app._notifications if n.severity == "warning"]
        assert note.message == "Food.md: 2 warnings — see the preview."
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert str(tree.cursor_node.label) == "Food ⚠"
        assert pilot.app.screen.query_one("#preview-warnings").display is True


async def test_md_exit_says_nothing_when_the_file_is_unchanged(source_tree, monkeypatch):
    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        _fake_nvim(monkeypatch, pilot, lambda: None)
        await _enter_in_md_mode_on_food(pilot)
        await pilot.app.workers.wait_for_complete()

        assert [n for n in pilot.app._notifications if n.severity == "warning"] == []
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        assert str(tree.cursor_node.label) == "Food"


async def test_a_warned_file_is_not_blocked(source_tree, monkeypatch):
    """The warning is information: the file still previews, opens and renames
    (requirements.md §2's "nothing is blocked")."""
    _warn_food(source_tree)
    opened = []
    monkeypatch.setattr("vimdiomas.tui.screens.base.open_file", lambda path: opened.append(path))

    app = _HostApp(source_tree)
    async with app.run_test() as pilot:
        tree = pilot.app.screen.query_one("#inspect-tree", InspectTree)
        _select(tree, "Food ⚠")
        await pilot.pause()
        await pilot.press("enter")
        await pilot.pause()
        assert opened == [source_tree / "Vocabulary" / "Food.pdf"]


def test_the_missing_tool_messages_name_no_command():
    # Sprint 8 M3: what is missing, never how to get it.
    from vimdiomas.tui.screens import inspect

    assert inspect.MSG_NO_POPPLER == "poppler isn't installed, so there's no PDF preview."
    assert inspect.MSG_NO_NVIM == "nvim isn't installed, so MD mode can't open files."
    for message in (inspect.MSG_NO_POPPLER, inspect.MSG_NO_NVIM):
        assert "`" not in message
        assert not any(word in message for word in ("brew", "pacman", "sudo"))
