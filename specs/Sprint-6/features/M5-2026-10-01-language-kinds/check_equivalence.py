"""One-off verification tool for Sprint 6 M5 (not part of the package).

Compiles a *copy* of a tree and records everything that leaves the app: for
each source file, the markdown handed to pandoc, pandoc's full argv and the
staleness stamp; and, for each PDF, its pages rasterised with `pdftoppm`.
Run it on `main` and again on the M5 branch, then diff the two outputs.

    uv run python check_equivalence.py <tree-root> <out-dir>

The tree is copied to a scratch directory and the staleness cache pointed at a
scratch file, so the real tree, its PDFs and the real cache are never touched.
"""

import inspect
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from idiomas import compile as compile_module


def main(tree_root: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="m5-equivalence-"))
    copy = scratch / tree_root.name
    shutil.copytree(tree_root, copy, ignore=shutil.ignore_patterns("*.pdf", ".DS_Store"))
    compile_module.CACHE_PATH = scratch / "compile_cache.json"

    calls: dict[str, dict] = {}
    real_run = compile_module.subprocess.run

    def recording_run(argv, **kwargs):
        argv = list(argv)
        output = Path(argv[argv.index("-o") + 1])
        key = str(output.relative_to(copy).with_suffix(".md"))
        normalised = [
            "--template=<template>" if arg.startswith("--template=") else
            "<output>" if arg == str(output) else arg
            for arg in argv
        ]
        calls[key] = {
            "argv": normalised,
            "markdown": kwargs["input"].decode("utf-8"),
        }
        return real_run(argv, **kwargs)

    compile_module.subprocess.run = recording_run

    kwargs = {"force": True}
    if "kind" in inspect.signature(compile_module.compile_all).parameters:
        from idiomas.languages import CHARACTER_PHONETIC

        kwargs["kind"] = CHARACTER_PHONETIC
    report = compile_module.compile_all(copy, **kwargs)
    compile_module.subprocess.run = real_run
    if report.failed:
        sys.exit(f"compile failed: {report.failed}")

    cache = json.loads(compile_module.CACHE_PATH.read_text(encoding="utf-8"))
    for source, stamp in cache.items():
        calls[str(Path(source).relative_to(copy))]["stamp"] = stamp

    (out_dir / "calls.json").write_text(
        json.dumps(calls, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8"
    )

    pages = out_dir / "pages"
    pages.mkdir(exist_ok=True)
    pdfs = sorted(copy.rglob("*.pdf"))
    for pdf in pdfs:
        stem = str(pdf.relative_to(copy).with_suffix("")).replace("/", "__").replace(" ", "_")
        subprocess.run(
            ["pdftoppm", "-r", "100", "-png", str(pdf), str(pages / stem)], check=True
        )
    print(f"{len(calls)} source files, {len(pdfs)} PDFs, {len(list(pages.glob('*.png')))} pages")
    shutil.rmtree(scratch)


if __name__ == "__main__":
    main(Path(sys.argv[1]).expanduser(), Path(sys.argv[2]))
