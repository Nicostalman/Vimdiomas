# M5.3 · Browse screen — Plan

## 1. Notebook PDF listing

- A small helper (in `browse.py`, not `store.py` — this is notebook-tree-specific, not a general discovery primitive): `list_pdfs(notebook_root: Path) -> list[Path]`, returning every `.pdf` under `notebook_root` via `rglob`, as paths relative to `notebook_root`.

## 2. Tag → notebook-path mapping

- A helper: given `config.source_root`/`config.notebook_root` and a tag string, use M3's `tag_index()` over `source_root`, get the matching source file paths, convert each to its notebook-relative `.pdf` counterpart (`path.relative_to(source_root).with_suffix(".pdf")`), and intersect with the actual `list_pdfs()` result (so a tag match with no compiled PDF yet is dropped).

## 3. Screen layout

- `BrowseScreen(Screen)`: a filename `Input` (`#filename-filter`), a tag `Input` (`#tag-filter`), and a results `ListView` (or `OptionList`) below them.
- On mount: build the initial (unfiltered) results list from all notebook PDFs.

## 4. Filtering logic

- On either input's `Changed` event, recompute the visible list:
  - Start from all notebook-relative PDF paths (as display strings, e.g. `Vocabulary/Food`).
  - If the filename filter is non-empty, run `fuzzy(filename_query, candidates)` and use its ranked/filtered order.
  - If the tag filter is non-empty, intersect with the tag → notebook-path set from step 2 (preserving the fuzzy ranking order from the previous bullet, or the tag_index() file order if the filename filter was empty).
  - Repopulate the results list; show an empty-state message when nothing matches.

## 5. Opening a result

- On selecting a result (Enter / `ListView.Selected`), resolve back to the absolute PDF path and run `subprocess.run(["open", str(path)])`. Wrap in a small function (e.g. `open_pdf(path)`) so tests can monkeypatch `subprocess.run` instead of actually launching Preview.app.

## 6. Wiring into the main menu

- `MainMenuScreen._browse()`: push `BrowseScreen(config.source_root, config.notebook_root)` instead of the M5.1 placeholder.

## 7. Tests

- `tests/test_tui_browse_screen.py`, Pilot-driven, against a fixture `source/`+`notebook/` pair under `tmp_path` (a couple of real small PDFs are unnecessary — placeholder byte content is fine since nothing reads the PDF's actual content, only its existence/path):
  - No filters: all notebook PDFs listed.
  - Filename filter: ranks/filters per `fuzzy()`, matching M3's own already-tested behavior (no need to re-test `fuzzy()` itself, just that it's wired in).
  - Tag filter alone: only PDFs whose source file carries the tag are shown; a tag match whose PDF doesn't exist is correctly absent.
  - Both filters combined: intersection behaves correctly.
  - Selecting a result calls the mocked `open_pdf`/`subprocess.run` with the correct absolute path.
  - Empty-state message shown when no results match.
