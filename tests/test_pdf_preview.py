import subprocess

import pytest

from vimdiomas import pdf_preview
from vimdiomas.compile import compile_file
from vimdiomas.languages import CHARACTER_PHONETIC


def test_pdftoppm_available_reflects_shutil_which(monkeypatch):
    monkeypatch.setattr(pdf_preview.shutil, "which", lambda name: "/usr/bin/pdftoppm")
    assert pdf_preview.pdftoppm_available() is True

    monkeypatch.setattr(pdf_preview.shutil, "which", lambda name: None)
    assert pdf_preview.pdftoppm_available() is False


@pytest.fixture
def real_pdf(tmp_path):
    source_file = tmp_path / "Food.md"
    source_file.write_text("# Food\n\n牛肉\tniu2rou4\tbeef\n", encoding="utf-8")
    notebook_file = tmp_path / "Food.pdf"
    compile_file(source_file, notebook_file, kind=CHARACTER_PHONETIC)
    return notebook_file


@pytest.mark.integration
def test_page_aspect_ratio_matches_letter_page(real_pdf):
    # compile_file's template renders on US Letter (612 x 792 pts).
    assert pdf_preview.page_aspect_ratio(real_pdf) == pytest.approx(612 / 792)


def _png_dimensions(png_bytes: bytes) -> tuple[int, int]:
    import struct

    return struct.unpack(">II", png_bytes[16:24])


@pytest.mark.integration
def test_rasterise_page_produces_valid_png(real_pdf):
    png_bytes = pdf_preview.rasterise_page(real_pdf, 800, 1000)
    assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.integration
def test_rasterise_page_preserves_aspect_ratio_in_a_wide_box(real_pdf):
    # A box much wider than the page's own ratio: height should be the
    # binding dimension, width computed proportionally smaller than the box.
    png_bytes = pdf_preview.rasterise_page(real_pdf, 2000, 400)
    width, height = _png_dimensions(png_bytes)
    assert height == 400
    assert width < 2000
    assert width / height == pytest.approx(612 / 792, rel=0.01)


@pytest.mark.integration
def test_rasterise_page_preserves_aspect_ratio_in_a_tall_box(real_pdf):
    # A box much taller than the page's own ratio: width should be the
    # binding dimension, height computed proportionally smaller than the box.
    png_bytes = pdf_preview.rasterise_page(real_pdf, 300, 2000)
    width, height = _png_dimensions(png_bytes)
    assert width == 300
    assert height < 2000
    assert width / height == pytest.approx(612 / 792, rel=0.01)


@pytest.mark.integration
def test_rasterise_page_raises_for_missing_pdf(tmp_path):
    with pytest.raises(FileNotFoundError):
        pdf_preview.rasterise_page(tmp_path / "missing.pdf", 800, 1000)


@pytest.mark.integration
def test_extract_text_returns_non_empty_text(real_pdf):
    text = pdf_preview.extract_text(real_pdf)
    assert text.strip() != ""


@pytest.mark.integration
def test_extract_text_raises_for_missing_pdf(tmp_path):
    with pytest.raises(subprocess.CalledProcessError):
        pdf_preview.extract_text(tmp_path / "missing.pdf")


@pytest.mark.integration
def test_raster_cache_hits_pdftoppm_once_for_unchanged_pdf(real_pdf, monkeypatch):
    calls = []
    original_run = subprocess.run

    def _counting_run(args, **kwargs):
        calls.append(args)
        return original_run(args, **kwargs)

    monkeypatch.setattr(pdf_preview.subprocess, "run", _counting_run)

    cache = pdf_preview.RasterCache()
    first = cache.get_or_rasterise(real_pdf, 800, 1000)
    second = cache.get_or_rasterise(real_pdf, 800, 1000)

    assert first == second
    # One rasterisation is one pdfinfo call (aspect ratio) + one pdftoppm
    # call; the cache hit on the second lookup adds neither.
    assert len(calls) == 2


@pytest.mark.integration
def test_raster_cache_recomputes_when_pdf_mtime_changes(real_pdf, monkeypatch):
    calls = []
    original_run = subprocess.run

    def _counting_run(args, **kwargs):
        calls.append(args)
        return original_run(args, **kwargs)

    monkeypatch.setattr(pdf_preview.subprocess, "run", _counting_run)

    cache = pdf_preview.RasterCache()
    cache.get_or_rasterise(real_pdf, 800, 1000)

    import os
    import time

    time.sleep(0.01)
    os.utime(real_pdf, None)

    cache.get_or_rasterise(real_pdf, 800, 1000)
    assert len(calls) == 4
