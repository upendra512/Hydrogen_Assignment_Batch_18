#!/usr/bin/env python3
"""Package Batch 18 source, results and final PDFs for course submission."""
from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Batch18_source.zip"
TOP = ROOT.name


def selected_files() -> list[Path]:
    files: set[Path] = set()
    files.update((ROOT / name for name in (
        "README.md", "requirements.txt", ".gitignore")))
    for folder in ("case", "docs", "checklists", "presentation", "src", "tests", "data", "notebooks"):
        base = ROOT / folder
        if base.exists():
            files.update(path for path in base.rglob("*") if path.is_file())
    scripts = ROOT / "scripts"
    files.update(path for path in scripts.glob("*.py") if path.is_file())
    report = ROOT / "report"
    files.update(path for path in report.iterdir()
                 if path.is_file() and path.suffix.lower() in {".pdf", ".csv", ".png"})
    figure_dir = report / "figures"
    files.update(path for path in figure_dir.glob("*.png") if path.is_file())
    overleaf = report / "overleaf"
    if overleaf.exists():
        source_suffixes = {".tex", ".bib", ".md", ".pdf", ".png"}
        files.update(path for path in overleaf.rglob("*")
                     if path.is_file()
                     and path.suffix.lower() in source_suffixes
                     and "tmp" not in path.relative_to(overleaf).parts)
    return sorted(path for path in files if path.exists()
                  and "__pycache__" not in path.parts and path.suffix != ".pyc")


def main() -> int:
    files = selected_files()
    with ZipFile(OUTPUT, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive_name = Path(TOP) / path.relative_to(ROOT)
            archive.write(path, archive_name.as_posix())
    print(f"Wrote {OUTPUT}")
    print(f"Included {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
