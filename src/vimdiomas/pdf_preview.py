"""Rasterises a PDF's first page for Inspect Tree's preview pane.

`pdftoppm`/`pdftotext` (poppler) are external-tool subprocess calls, like
`pandoc`/`xelatex` already are for compiling — not a Python package
dependency. poppler is optional (see `doctor.py`): its absence degrades the
preview, never compiling."""

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

_PAGE_SIZE_RE = re.compile(r"Page\s+\d+\s+size:\s*([\d.]+)\s*x\s*([\d.]+)\s*pts")


def pdftoppm_available() -> bool:
    return shutil.which("pdftoppm") is not None


def page_aspect_ratio(pdf_path: Path) -> float:
    """`pdf_path`'s first page's width/height ratio, from `pdfinfo`.

    Needed because `rasterise_page` fits inside a box rather than stretching
    to it: without the page's own ratio there's no way to know which of the
    box's two dimensions is the binding one."""
    result = subprocess.run(
        ["pdfinfo", "-f", "1", "-l", "1", str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = _PAGE_SIZE_RE.search(result.stdout)
    if match is None:
        raise ValueError(f"pdfinfo output for {pdf_path} has no parseable page size")
    width_pts, height_pts = float(match.group(1)), float(match.group(2))
    return width_pts / height_pts


def rasterise_page(pdf_path: Path, width_px: int, height_px: int) -> bytes:
    """Rasterise `pdf_path`'s first page to PNG bytes, fit inside
    `width_px` x `height_px` preserving the page's own aspect ratio — never
    stretched to fill the box.

    `pdftoppm`'s `-scale-to-x`/`-scale-to-y` do **not** compute the other
    dimension proportionally when only one is given (checked against the
    installed poppler build) — the unset one falls back to the default
    150dpi resolution instead, which is not what "fit inside a box" means.
    So both are always computed here, from `page_aspect_ratio` and whichever
    of the box's two dimensions is the tighter constraint, and passed
    together — already matching the page's ratio, so `pdftoppm` has nothing
    left to stretch.

    Raises `subprocess.CalledProcessError` (a nonzero `pdftoppm`/`pdfinfo`
    exit), `FileNotFoundError` for a missing PDF, or `OSError` on failure —
    the caller turns any of these into a degradation message.

    `pdftoppm` has no stdout mode of its own (unlike `pdftotext`): it always
    writes `<root>-<page>.png` (or `<root>.png` with `-singlefile`) to disk,
    so this shells out to a temp file and reads it back rather than piping.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    page_ratio = page_aspect_ratio(pdf_path)
    box_ratio = width_px / height_px
    if box_ratio > page_ratio:
        # The box is relatively wider than the page: height is binding.
        target_height = height_px
        target_width = max(round(height_px * page_ratio), 1)
    else:
        target_width = width_px
        target_height = max(round(width_px / page_ratio), 1)

    with tempfile.TemporaryDirectory() as tmp_dir:
        out_root = Path(tmp_dir) / "page"
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-singlefile",
                "-f",
                "1",
                "-l",
                "1",
                "-scale-to-x",
                str(target_width),
                "-scale-to-y",
                str(target_height),
                str(pdf_path),
                str(out_root),
            ],
            check=True,
            capture_output=True,
        )
        return out_root.with_suffix(".png").read_bytes()


def extract_text(pdf_path: Path) -> str:
    """The no-kitty-protocol fallback: plain text of the whole PDF via
    `pdftotext`."""
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        check=True,
        capture_output=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


class RasterCache:
    """An in-memory PDF-to-raster cache, keyed on the PDF's path and target
    pixel size, invalidated on the PDF's own mtime.

    Separate from `compile.py`'s on-disk staleness cache (source-.md-to-PDF),
    which tracks a different question. This only needs to survive repeat
    cursor visits within one running session, so no on-disk format is
    needed."""

    def __init__(self) -> None:
        self._entries: dict[tuple[Path, int, int], tuple[float, bytes]] = {}

    def get_or_rasterise(self, pdf_path: Path, width_px: int, height_px: int) -> bytes:
        key = (pdf_path, width_px, height_px)
        mtime = pdf_path.stat().st_mtime
        cached = self._entries.get(key)
        if cached is not None and cached[0] == mtime:
            return cached[1]

        png_bytes = rasterise_page(pdf_path, width_px, height_px)
        self._entries[key] = (mtime, png_bytes)
        return png_bytes
